"""
CVSS v3.1 base score calculator.

Implements the official CVSS v3.1 base score formula (FIRST.org spec) so
findings can be scored consistently regardless of which tool produced them.
Reference: https://www.first.org/cvss/v3.1/specification-document
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class AttackVector(str, Enum):
    NETWORK = "N"
    ADJACENT = "A"
    LOCAL = "L"
    PHYSICAL = "P"


class AttackComplexity(str, Enum):
    LOW = "L"
    HIGH = "H"


class PrivilegesRequired(str, Enum):
    NONE = "N"
    LOW = "L"
    HIGH = "H"


class UserInteraction(str, Enum):
    NONE = "N"
    REQUIRED = "R"


class Scope(str, Enum):
    UNCHANGED = "U"
    CHANGED = "C"


class ImpactLevel(str, Enum):
    NONE = "N"
    LOW = "L"
    HIGH = "H"


_AV_WEIGHTS = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2}
_AC_WEIGHTS = {"L": 0.77, "H": 0.44}
_UI_WEIGHTS = {"N": 0.85, "R": 0.62}
_IMPACT_WEIGHTS = {"N": 0.0, "L": 0.22, "H": 0.56}

# PR weights depend on scope (changed scope gives attacker more credit)
_PR_WEIGHTS_UNCHANGED = {"N": 0.85, "L": 0.62, "H": 0.27}
_PR_WEIGHTS_CHANGED = {"N": 0.85, "L": 0.68, "H": 0.5}


@dataclass
class CVSSVector:
    attack_vector: AttackVector
    attack_complexity: AttackComplexity
    privileges_required: PrivilegesRequired
    user_interaction: UserInteraction
    scope: Scope
    confidentiality: ImpactLevel
    integrity: ImpactLevel
    availability: ImpactLevel

    def to_string(self) -> str:
        return (
            f"CVSS:3.1/AV:{self.attack_vector.value}/AC:{self.attack_complexity.value}"
            f"/PR:{self.privileges_required.value}/UI:{self.user_interaction.value}"
            f"/S:{self.scope.value}/C:{self.confidentiality.value}"
            f"/I:{self.integrity.value}/A:{self.availability.value}"
        )


@dataclass
class CVSSResult:
    base_score: float
    severity: str
    vector_string: str
    impact_subscore: float
    exploitability_subscore: float


def _round_up(value: float) -> float:
    """CVSS 'round up' function: round to nearest 0.1, always rounding up."""
    int_value = int(round(value * 100000))
    if int_value % 10000 == 0:
        return int_value / 100000
    return (math.floor(int_value / 10000) + 1) / 10.0


def severity_from_score(score: float) -> str:
    if score == 0.0:
        return "none"
    if score < 4.0:
        return "low"
    if score < 7.0:
        return "medium"
    if score < 9.0:
        return "high"
    return "critical"


def calculate_cvss(vector: CVSSVector) -> CVSSResult:
    """Compute the CVSS v3.1 base score from a fully specified vector."""
    iss = 1 - (
        (1 - _IMPACT_WEIGHTS[vector.confidentiality.value])
        * (1 - _IMPACT_WEIGHTS[vector.integrity.value])
        * (1 - _IMPACT_WEIGHTS[vector.availability.value])
    )

    if vector.scope == Scope.UNCHANGED:
        impact = 6.42 * iss
    else:
        impact = 7.52 * (iss - 0.029) - 3.25 * ((iss - 0.02) ** 15)

    pr_weights = (
        _PR_WEIGHTS_CHANGED
        if vector.scope == Scope.CHANGED
        else _PR_WEIGHTS_UNCHANGED
    )

    exploitability = (
        8.22
        * _AV_WEIGHTS[vector.attack_vector.value]
        * _AC_WEIGHTS[vector.attack_complexity.value]
        * pr_weights[vector.privileges_required.value]
        * _UI_WEIGHTS[vector.user_interaction.value]
    )

    if impact <= 0:
        base_score = 0.0
    elif vector.scope == Scope.UNCHANGED:
        base_score = _round_up(min(impact + exploitability, 10.0))
    else:
        base_score = _round_up(min(1.08 * (impact + exploitability), 10.0))

    return CVSSResult(
        base_score=round(base_score, 1),
        severity=severity_from_score(base_score),
        vector_string=vector.to_string(),
        impact_subscore=round(impact, 2),
        exploitability_subscore=round(exploitability, 2),
    )


def parse_vector_string(vector_string: str) -> CVSSVector:
    """Parse a 'CVSS:3.1/AV:N/AC:L/...' string into a CVSSVector."""
    parts = {}
    for chunk in vector_string.split("/"):
        if ":" not in chunk:
            continue
        key, value = chunk.split(":", 1)
        parts[key] = value

    return CVSSVector(
        attack_vector=AttackVector(parts["AV"]),
        attack_complexity=AttackComplexity(parts["AC"]),
        privileges_required=PrivilegesRequired(parts["PR"]),
        user_interaction=UserInteraction(parts["UI"]),
        scope=Scope(parts["S"]),
        confidentiality=ImpactLevel(parts["C"]),
        integrity=ImpactLevel(parts["I"]),
        availability=ImpactLevel(parts["A"]),
    )


def score_from_vector_string(vector_string: str) -> CVSSResult:
    """Convenience: parse + score in one call."""
    return calculate_cvss(parse_vector_string(vector_string))


def estimate_vector_from_finding(
    *,
    remote: bool = True,
    requires_auth: bool = False,
    requires_user_interaction: bool = False,
    confidentiality_impact: str = "L",
    integrity_impact: str = "L",
    availability_impact: str = "L",
    complexity: str = "L",
    scope_changed: bool = False,
) -> Optional[CVSSResult]:
    """
    Build a reasonable CVSS vector from coarse tool-output signals when a
    scanner reports a finding without a ready-made CVSS vector (e.g. a
    heuristic nikto or nuclei match). Not a substitute for an authoritative
    NVD/vendor CVSS score when one is available.
    """
    vector = CVSSVector(
        attack_vector=AttackVector.NETWORK if remote else AttackVector.LOCAL,
        attack_complexity=AttackComplexity.LOW
        if complexity.upper() == "L"
        else AttackComplexity.HIGH,
        privileges_required=PrivilegesRequired.LOW
        if requires_auth
        else PrivilegesRequired.NONE,
        user_interaction=UserInteraction.REQUIRED
        if requires_user_interaction
        else UserInteraction.NONE,
        scope=Scope.CHANGED if scope_changed else Scope.UNCHANGED,
        confidentiality=ImpactLevel(confidentiality_impact.upper()),
        integrity=ImpactLevel(integrity_impact.upper()),
        availability=ImpactLevel(availability_impact.upper()),
    )
    return calculate_cvss(vector)
