"""
Report generator — builds a PDF pentest/SOC findings report from a target
and its findings using reportlab. Pure document assembly: no scanning,
no exploitation, just turning already-collected findings/AI analysis into
a client- or stakeholder-ready artifact.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from core.config import settings
from utils.logger import get_logger

log = get_logger(__name__)

_SEVERITY_COLORS = {
    "critical": colors.HexColor("#7f1d1d"),
    "high": colors.HexColor("#b91c1c"),
    "medium": colors.HexColor("#b45309"),
    "low": colors.HexColor("#1d4ed8"),
    "info": colors.HexColor("#4b5563"),
}

_SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]


@dataclass
class ReportBuildResult:
    file_path: str
    page_count: int


class ReportGenerationError(RuntimeError):
    pass


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    custom = {
        "Title": ParagraphStyle("NexusTitle", parent=base["Title"], fontSize=24, spaceAfter=6),
        "Subtitle": ParagraphStyle("NexusSubtitle", parent=base["Normal"], fontSize=12, textColor=colors.grey, spaceAfter=20),
        "H2": ParagraphStyle("NexusH2", parent=base["Heading2"], spaceBefore=18, spaceAfter=8),
        "H3": ParagraphStyle("NexusH3", parent=base["Heading3"], spaceBefore=12, spaceAfter=6),
        "Body": ParagraphStyle("NexusBody", parent=base["Normal"], fontSize=10, leading=14),
        "Small": ParagraphStyle("NexusSmall", parent=base["Normal"], fontSize=8, textColor=colors.grey),
    }
    return custom


def _severity_badge(severity: str) -> Table:
    color = _SEVERITY_COLORS.get(severity.lower(), colors.grey)
    table = Table([[severity.upper()]], colWidths=[0.9 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), color),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _build_cover_page(story: list, styles: dict, target_name: str, generated_by: str) -> None:
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("NEXUS Security Assessment Report", styles["Title"]))
    story.append(Paragraph(f"Target: {target_name}", styles["Subtitle"]))
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    story.append(Paragraph(f"Generated {generated_at} by {generated_by}", styles["Small"]))
    story.append(
        Paragraph(
            "CONFIDENTIAL — Prepared under signed engagement authorization. "
            "Distribution restricted to authorized recipients.",
            styles["Small"],
        )
    )
    story.append(PageBreak())


def _build_executive_summary(story: list, styles: dict, ai_summary: Optional[dict]) -> None:
    story.append(Paragraph("Executive Summary", styles["H2"]))
    if not ai_summary:
        story.append(Paragraph("No AI-generated summary was available for this report.", styles["Body"]))
        return

    story.append(Paragraph(f"Overall risk level: <b>{ai_summary.get('overall_risk_level', 'unknown').upper()}</b>", styles["Body"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(ai_summary.get("executive_summary", ""), styles["Body"]))

    top_risks = ai_summary.get("top_risks") or []
    if top_risks:
        story.append(Paragraph("Top Risks", styles["H3"]))
        for risk in top_risks:
            story.append(Paragraph(f"• {risk}", styles["Body"]))

    next_steps = ai_summary.get("recommended_next_steps") or []
    if next_steps:
        story.append(Paragraph("Recommended Next Steps", styles["H3"]))
        for step in next_steps:
            story.append(Paragraph(f"• {step}", styles["Body"]))

    story.append(PageBreak())


def _build_findings_summary_table(story: list, styles: dict, findings: list[dict]) -> None:
    story.append(Paragraph("Findings Summary", styles["H2"]))

    counts = {sev: 0 for sev in _SEVERITY_ORDER}
    for f in findings:
        sev = str(f.get("severity", "info")).lower()
        counts[sev] = counts.get(sev, 0) + 1

    data = [["Severity", "Count"]] + [[sev.upper(), str(counts[sev])] for sev in _SEVERITY_ORDER]
    table = Table(data, colWidths=[2 * inch, 1 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(table)
    story.append(PageBreak())


def _build_finding_detail(story: list, styles: dict, finding: dict) -> None:
    header_table = Table(
        [[_severity_badge(str(finding.get("severity", "info"))), Paragraph(finding.get("title", "Untitled Finding"), styles["H3"])]],
        colWidths=[1.1 * inch, 5.5 * inch],
    )
    header_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(header_table)

    meta_bits = []
    if finding.get("cvss_score") is not None:
        meta_bits.append(f"CVSS {finding['cvss_score']}")
    if finding.get("cve_ids"):
        meta_bits.append(", ".join(finding["cve_ids"]))
    if finding.get("affected_host"):
        host = finding["affected_host"]
        if finding.get("affected_port"):
            host += f":{finding['affected_port']}"
        meta_bits.append(host)
    if meta_bits:
        story.append(Paragraph(" | ".join(meta_bits), styles["Small"]))

    story.append(Spacer(1, 4))
    story.append(Paragraph(finding.get("description", ""), styles["Body"]))

    ai_analysis = finding.get("ai_analysis") or {}
    if ai_analysis.get("risk_narrative"):
        story.append(Paragraph("<b>Risk Analysis:</b> " + ai_analysis["risk_narrative"], styles["Body"]))

    if finding.get("remediation"):
        story.append(Paragraph("<b>Remediation:</b> " + finding["remediation"], styles["Body"]))
    elif ai_analysis.get("remediation_steps"):
        story.append(Paragraph("<b>Remediation:</b>", styles["Body"]))
        for step in ai_analysis["remediation_steps"]:
            story.append(Paragraph(f"• {step}", styles["Body"]))

    if finding.get("mitre_techniques"):
        story.append(Paragraph(f"<b>MITRE ATT&CK:</b> {', '.join(finding['mitre_techniques'])}", styles["Small"]))

    story.append(Spacer(1, 14))


def build_report(
    *,
    target_name: str,
    generated_by: str,
    findings: list[dict[str, Any]],
    ai_target_summary: Optional[dict] = None,
    output_dir: Optional[str] = None,
    file_name: Optional[str] = None,
) -> ReportBuildResult:
    """
    Assemble a PDF report from already-collected findings and (optionally)
    an AI-generated posture summary. `findings` is a list of plain dicts
    (as produced by schemas.finding.FindingOut.model_dump()) so this module
    has no direct ORM dependency.
    """
    output_dir = output_dir or settings.REPORT_DIR
    os.makedirs(output_dir, exist_ok=True)

    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in target_name)[:64]
    file_name = file_name or f"nexus_report_{safe_name}_{int(datetime.now(timezone.utc).timestamp())}.pdf"
    file_path = os.path.join(output_dir, file_name)

    styles = _styles()
    story: list = []

    _build_cover_page(story, styles, target_name, generated_by)
    _build_executive_summary(story, styles, ai_target_summary)
    _build_findings_summary_table(story, styles, findings)

    story.append(Paragraph("Detailed Findings", styles["H2"]))
    severity_rank = {sev: i for i, sev in enumerate(_SEVERITY_ORDER)}
    sorted_findings = sorted(findings, key=lambda f: severity_rank.get(str(f.get("severity", "info")).lower(), 99))
    for finding in sorted_findings:
        _build_finding_detail(story, styles, finding)

    try:
        doc = SimpleDocTemplate(
            file_path,
            pagesize=LETTER,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )
        doc.build(story)
    except Exception as exc:
        log.error(f"PDF report generation failed: {exc}")
        raise ReportGenerationError(f"Failed to generate report: {exc}") from exc

    page_count = _estimate_page_count(file_path)
    log.info(f"report generated: {file_path}", extra={"extra_fields": {"findings_count": len(findings)}})
    return ReportBuildResult(file_path=file_path, page_count=page_count)


def _estimate_page_count(file_path: str) -> int:
    try:
        from pypdf import PdfReader

        return len(PdfReader(file_path).pages)
    except Exception:
        return 0
