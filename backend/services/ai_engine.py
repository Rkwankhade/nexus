"""
AI engine — the core Anthropic Claude integration used across NEXUS:
conversational assistant, finding triage/analysis, and target posture
summaries for analysts and report generation.

Scope note: this module deliberately does NOT generate working exploit
code, specific exploit-module/payload selections, or step-by-step attack
instructions for a finding. `suggest_exploit_module()` exists because
routers/ai.py already calls it, but it returns defensive guidance
(remediation steps, detection opportunities, MITRE ATT&CK context) rather
than an actionable exploitation plan — consistent with the rest of the
platform's tooling boundary (recon/scanning/detection/forensics, not
exploitation automation).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional

from core.config import settings
from core.redis_client import redis_client
from services.ai_providers import AIProviderError, get_provider
from utils.logger import get_logger
from utils.mitre_mapper import map_text_to_techniques

log = get_logger(__name__)

_CONVERSATION_TTL_SECONDS = 60 * 60 * 24  # 1 day of chat history retained per conversation
_MAX_HISTORY_MESSAGES = 20

_SYSTEM_PROMPT_ASSISTANT = """You are the NEXUS AI assistant, embedded in a defensive/authorized \
security-operations platform used by SOC analysts and penetration testers working within \
signed, written authorization for every target in scope.

Your role is analytical and defensive: help the analyst understand findings, prioritize risk, \
map activity to MITRE ATT&CK, draft remediation guidance, and interpret scan/log output. \
You do not produce working exploit code, specific exploitation payloads, or step-by-step \
instructions for compromising a system, even if the user says the target is authorized — \
authorization is enforced by the platform's approval workflow, not by this chat, and your \
value here is triage and remediation, not weaponization. If asked for that, redirect the \
analyst to remediation, detection, and risk-communication framing instead.

Be concise, precise, and cite specific evidence from what the analyst shares rather than \
speculating."""

_SYSTEM_PROMPT_FINDING_ANALYSIS = """You are a security analyst assistant reviewing a single \
scan finding. Given the finding's title, description, evidence, and metadata, produce a \
structured JSON analysis with these exact keys:
{
  "risk_narrative": "2-4 sentences explaining real-world impact in plain language",
  "false_positive_likelihood": "low" | "medium" | "high",
  "false_positive_reasoning": "1-2 sentences",
  "priority": "critical" | "high" | "medium" | "low",
  "remediation_steps": ["ordered, specific remediation actions"],
  "detection_opportunities": ["how a defender could detect exploitation attempts of this finding"],
  "mitre_techniques": ["technique IDs like T1190, if applicable"]
}
Respond with ONLY the JSON object, no preamble, no markdown fences."""

_SYSTEM_PROMPT_TARGET_SUMMARY = """You are a security analyst assistant producing an executive \
posture summary for a target based on its open findings. Produce a structured JSON object with \
these exact keys:
{
  "overall_risk_level": "critical" | "high" | "medium" | "low",
  "executive_summary": "3-5 sentences, non-technical, suitable for a report cover page",
  "top_risks": ["up to 5 short bullet points, most severe first"],
  "recommended_next_steps": ["up to 5 prioritized remediation/process actions"],
  "severity_breakdown": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
}
Respond with ONLY the JSON object, no preamble, no markdown fences."""

_SYSTEM_PROMPT_REMEDIATION_GUIDANCE = """You are a security analyst assistant. Given a single \
finding, produce defensive guidance ONLY — you do not name or select exploitation tools, \
frameworks, payloads, or modules, and you do not write attack code or attack steps. Produce a \
structured JSON object with these exact keys:
{
  "why_this_matters": "2-3 sentences on real-world exploitability risk, in general terms",
  "remediation_steps": ["ordered, specific fix actions"],
  "compensating_controls": ["mitigations if immediate remediation isn't possible"],
  "detection_opportunities": ["log sources / signatures / behaviors a SOC could alert on"],
  "mitre_techniques": ["relevant ATT&CK technique IDs"],
  "references": ["vendor advisories, CVE pages, or ATT&CK URLs relevant to this finding type"]
}
Respond with ONLY the JSON object, no preamble, no markdown fences."""


@dataclass
class ChatMessage:
    role: str  # "user" | "assistant"
    content: str


class AIEngineError(RuntimeError):
    pass


class AIEngine:
    def __init__(self) -> None:
        self._provider = get_provider()

    # ------------------------------------------------------------------
    # Conversational assistant
    # ------------------------------------------------------------------

    async def chat(
        self,
        user_id: str,
        conversation_id: str,
        message: str,
        context: Optional[dict[str, Any]] = None,
    ) -> str:
        history = await self._load_history(user_id, conversation_id)

        user_content = message
        if context:
            user_content = f"{message}\n\n[Context]\n{json.dumps(context, default=str)[:4000]}"

        messages = [{"role": m.role, "content": m.content} for m in history]
        messages.append({"role": "user", "content": user_content})

        try:
            reply_text = await self._provider.complete(_SYSTEM_PROMPT_ASSISTANT, messages)
        except AIProviderError as exc:
            log.error(f"AI chat call failed: {exc}")
            raise AIEngineError(str(exc)) from exc

        history.append(ChatMessage(role="user", content=message))
        history.append(ChatMessage(role="assistant", content=reply_text))
        await self._save_history(user_id, conversation_id, history)

        return reply_text

    async def _load_history(self, user_id: str, conversation_id: str) -> list[ChatMessage]:
        key = f"ai_conversation:{user_id}:{conversation_id}"
        raw = await redis_client.get_json(key)
        if not raw:
            return []
        return [ChatMessage(role=m["role"], content=m["content"]) for m in raw]

    async def _save_history(self, user_id: str, conversation_id: str, history: list[ChatMessage]) -> None:
        trimmed = history[-_MAX_HISTORY_MESSAGES:]
        key = f"ai_conversation:{user_id}:{conversation_id}"
        await redis_client.set_json(
            key,
            [{"role": m.role, "content": m.content} for m in trimmed],
            ex=_CONVERSATION_TTL_SECONDS,
        )

    # ------------------------------------------------------------------
    # Finding analysis
    # ------------------------------------------------------------------

    async def analyze_finding(self, finding: Any) -> dict:
        """Produce a structured triage analysis for a single Finding ORM object."""
        payload = {
            "title": finding.title,
            "description": finding.description,
            "severity": getattr(finding.severity, "value", str(finding.severity)),
            "cvss_score": finding.cvss_score,
            "cve_ids": finding.cve_ids,
            "affected_host": finding.affected_host,
            "affected_port": finding.affected_port,
            "affected_service": finding.affected_service,
            "evidence": finding.evidence,
            "source_tool": finding.source_tool,
        }
        result = await self._structured_call(_SYSTEM_PROMPT_FINDING_ANALYSIS, payload)
        result.setdefault("mitre_techniques", map_text_to_techniques(f"{finding.title} {finding.description}"))
        return result

    async def summarize_target_posture(self, target: Any, findings: list[Any]) -> dict:
        """Produce an executive-level posture summary for a target's open findings."""
        finding_summaries = [
            {
                "title": f.title,
                "severity": getattr(f.severity, "value", str(f.severity)),
                "status": getattr(f.status, "value", str(f.status)),
                "affected_host": f.affected_host,
                "cve_ids": f.cve_ids,
            }
            for f in findings
        ]
        payload = {
            "target_name": target.name,
            "target_value": target.value,
            "target_type": getattr(target.type, "value", str(target.type)),
            "finding_count": len(findings),
            "findings": finding_summaries[:200],  # cap payload size for very large targets
        }
        return await self._structured_call(_SYSTEM_PROMPT_TARGET_SUMMARY, payload)

    async def suggest_exploit_module(self, finding: Any) -> dict:
        """
        NOTE: despite the name (kept for API compatibility with the existing
        /api/ai/suggest-exploit/{finding_id} route), this method does NOT
        select or suggest exploitation tools/modules/payloads. It returns
        remediation and detection guidance for the finding instead. NEXUS's
        AI layer is scoped to defensive analysis; actual exploit execution
        (when authorized) goes through the human-approved workflow in
        routers/exploits.py, which this service does not participate in.
        """
        payload = {
            "title": finding.title,
            "description": finding.description,
            "severity": getattr(finding.severity, "value", str(finding.severity)),
            "cvss_score": finding.cvss_score,
            "cve_ids": finding.cve_ids,
            "affected_service": finding.affected_service,
        }
        return await self._structured_call(_SYSTEM_PROMPT_REMEDIATION_GUIDANCE, payload)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _structured_call(self, system_prompt: str, payload: dict) -> dict:
        try:
            text = await self._provider.complete(
                system_prompt, [{"role": "user", "content": json.dumps(payload, default=str)}]
            )
        except AIProviderError as exc:
            log.error(f"AI structured call failed: {exc}")
            raise AIEngineError(str(exc)) from exc

        text = text.strip()
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            log.warning("AI response was not valid JSON; returning raw text under 'raw_response'")
            return {"raw_response": text}


ai_engine = AIEngine()
