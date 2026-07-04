"""
Sigma rule engine — loads Sigma-format detection rules (YAML) and
evaluates them against normalized log events (dicts). This powers the
blue-team log-correlation workflow: SIEM/EDR/firewall logs come in via
log_ingestor, and each event is checked against the loaded ruleset to
raise Alert rows.

Supports the common Sigma subset:
  - selection blocks with field: value / field: [value, ...] (OR within a list)
  - field modifiers: contains, startswith, endswith, re, all
  - boolean conditions: "selection", "sel1 and sel2", "sel1 or not sel2", parens
  - "1 of selection*", "all of selection*", "all of them"

This module only *detects* — it matches rules against already-collected
defensive telemetry and produces alerts; it issues no commands to hosts.
"""

from __future__ import annotations

import re as _re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

from utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class SigmaRule:
    rule_id: str
    title: str
    description: str
    level: str
    tags: list[str]
    logsource: dict[str, str]
    detection: dict[str, Any]
    condition: str
    source_path: str = ""


@dataclass
class SigmaMatch:
    rule: SigmaRule
    event: dict


class SigmaParseError(ValueError):
    pass


def load_rule(path: str) -> SigmaRule:
    """Parse a single Sigma YAML rule file."""
    file_path = Path(path)
    try:
        data = yaml.safe_load(file_path.read_text(errors="replace"))
    except yaml.YAMLError as exc:
        raise SigmaParseError(f"Invalid YAML in {path}: {exc}") from exc

    if not isinstance(data, dict) or "detection" not in data:
        raise SigmaParseError(f"{path} is missing a 'detection' block")

    detection = dict(data["detection"])
    condition = detection.pop("condition", None)
    if condition is None:
        raise SigmaParseError(f"{path} detection block is missing 'condition'")

    return SigmaRule(
        rule_id=str(data.get("id", file_path.stem)),
        title=data.get("title", file_path.stem),
        description=data.get("description", "") or "",
        level=data.get("level", "medium"),
        tags=list(data.get("tags", []) or []),
        logsource=dict(data.get("logsource", {}) or {}),
        detection=detection,
        condition=str(condition),
        source_path=str(file_path),
    )


def load_rules_from_directory(directory: str) -> list[SigmaRule]:
    """Load every .yml/.yaml Sigma rule under `directory` (recursive)."""
    root = Path(directory)
    if not root.exists():
        raise FileNotFoundError(f"Sigma rules directory not found: {directory}")

    rules: list[SigmaRule] = []
    for rule_path in list(root.rglob("*.yml")) + list(root.rglob("*.yaml")):
        try:
            rules.append(load_rule(str(rule_path)))
        except SigmaParseError as exc:
            log.warning(f"skipping unparseable Sigma rule {rule_path}: {exc}")
    return rules


# ---------------------------------------------------------------------------
# Field matching
# ---------------------------------------------------------------------------


def _get_event_value(event: dict, field_name: str) -> Any:
    # Support flat dotted-path lookups (e.g. "process.name") in addition to
    # plain keys, since normalized log events may nest structured fields.
    if field_name in event:
        return event[field_name]
    parts = field_name.split(".")
    current: Any = event
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def _match_single_value(actual: Any, expected: Any, modifier: Optional[str]) -> bool:
    if actual is None:
        return False
    actual_str = str(actual)
    expected_str = str(expected)

    if modifier == "contains":
        return expected_str.lower() in actual_str.lower()
    if modifier == "startswith":
        return actual_str.lower().startswith(expected_str.lower())
    if modifier == "endswith":
        return actual_str.lower().endswith(expected_str.lower())
    if modifier == "re":
        try:
            return bool(_re.search(expected_str, actual_str))
        except _re.error:
            return False
    # default: exact match, case-insensitive for strings
    if isinstance(actual, str) and isinstance(expected, str):
        return actual.lower() == expected.lower()
    return actual == expected


def _match_field(event: dict, field_spec: str, expected: Any) -> bool:
    modifier = None
    field_name = field_spec
    if "|" in field_spec:
        field_name, modifier = field_spec.split("|", 1)

    actual = _get_event_value(event, field_name)

    if isinstance(expected, list):
        if modifier == "all":
            return all(_match_single_value(actual, v, None) for v in expected)
        return any(_match_single_value(actual, v, modifier) for v in expected)

    return _match_single_value(actual, expected, modifier)


def _match_selection(event: dict, selection: Any) -> bool:
    """A selection is a dict of field:value (AND across fields), or a list of
    such dicts (OR across the list — Sigma's list-of-maps form)."""
    if isinstance(selection, list):
        return any(_match_selection(event, item) for item in selection)

    if not isinstance(selection, dict):
        return False

    return all(_match_field(event, field_spec, expected) for field_spec, expected in selection.items())


# ---------------------------------------------------------------------------
# Condition expression evaluation
# ---------------------------------------------------------------------------

_TOKEN_RE = _re.compile(r"\(|\)|\band\b|\bor\b|\bnot\b|[A-Za-z_][A-Za-z0-9_*]*")


class _ConditionParser:
    """Small recursive-descent parser/evaluator for Sigma condition strings."""

    def __init__(self, tokens: list[str], selection_results: dict[str, bool]):
        self.tokens = tokens
        self.pos = 0
        self.selection_results = selection_results

    def _peek(self) -> Optional[str]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _advance(self) -> Optional[str]:
        tok = self._peek()
        self.pos += 1
        return tok

    def parse_expression(self) -> bool:
        left = self.parse_term()
        while self._peek() == "or":
            self._advance()
            right = self.parse_term()
            left = left or right
        return left

    def parse_term(self) -> bool:
        left = self.parse_factor()
        while self._peek() == "and":
            self._advance()
            right = self.parse_factor()
            left = left and right
        return left

    def parse_factor(self) -> bool:
        if self._peek() == "not":
            self._advance()
            return not self.parse_factor()
        if self._peek() == "(":
            self._advance()
            value = self.parse_expression()
            if self._peek() == ")":
                self._advance()
            return value
        return self.parse_identifier()

    def parse_identifier(self) -> bool:
        token = self._advance()
        if token is None:
            return False

        # "1 of selection*" / "all of selection*" / "all of them"
        if token.isdigit() and self._peek() == "of":
            count = int(token)
            self._advance()  # consume "of"
            pattern = self._advance() or ""
            return self._eval_of(pattern, min_count=count)

        if token == "all" and self._peek() == "of":
            self._advance()
            pattern = self._advance() or ""
            return self._eval_of(pattern, min_count=None)

        if token.endswith("*"):
            return self._eval_of(token, min_count=None)

        return self.selection_results.get(token, False)

    def _eval_of(self, pattern: str, min_count: Optional[int]) -> bool:
        if pattern == "them":
            matches = list(self.selection_results.values())
        else:
            prefix = pattern.rstrip("*")
            matches = [v for k, v in self.selection_results.items() if k.startswith(prefix)]

        if not matches:
            return False
        true_count = sum(1 for m in matches if m)
        required = min_count if min_count is not None else len(matches)
        return true_count >= required


def evaluate_rule(rule: SigmaRule, event: dict) -> bool:
    """Return True if `event` matches `rule`'s detection condition."""
    selection_results = {
        name: _match_selection(event, spec)
        for name, spec in rule.detection.items()
    }

    tokens = _TOKEN_RE.findall(rule.condition.lower())
    parser = _ConditionParser(tokens, selection_results)
    try:
        return parser.parse_expression()
    except Exception as exc:
        log.warning(f"failed evaluating Sigma condition for rule {rule.rule_id}: {exc}")
        return False


def evaluate_event_against_rules(event: dict, rules: list[SigmaRule]) -> list[SigmaMatch]:
    """Check one event against every loaded rule, returning all matches."""
    return [SigmaMatch(rule=r, event=event) for r in rules if evaluate_rule(r, event)]
