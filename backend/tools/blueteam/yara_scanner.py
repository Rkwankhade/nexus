"""
YARA scanner — signature-based malware/artifact detection over files and
directories, using the `yara-python` library bindings directly (no
subprocess needed). Used by both the blue-team file-integrity workflow and
the forensics malware-triage workflow.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yara

from utils.logger import get_logger

log = get_logger(__name__)

_MAX_FILE_SIZE_BYTES = 200 * 1024 * 1024  # 200MB safety cap per scanned file


@dataclass
class YaraMatch:
    file_path: str
    rule_name: str
    tags: list[str] = field(default_factory=list)
    meta: dict = field(default_factory=dict)
    matched_strings: list[str] = field(default_factory=list)


class RuleCompilationError(RuntimeError):
    pass


def compile_rules(rule_paths: list[str]) -> "yara.Rules":
    """
    Compile one or more .yar/.yara rule files into a single Rules object.
    `rule_paths` maps namespace -> filepath internally so rule names never
    collide across files.
    """
    sources: dict[str, str] = {}
    for path_str in rule_paths:
        path = Path(path_str)
        if not path.exists():
            raise FileNotFoundError(f"YARA rule file not found: {path_str}")
        namespace = path.stem
        sources[namespace] = str(path)

    try:
        return yara.compile(filepaths=sources)
    except yara.SyntaxError as exc:
        raise RuleCompilationError(f"YARA rule syntax error: {exc}") from exc


def scan_file(rules: "yara.Rules", file_path: str, timeout_seconds: int = 30) -> list[YaraMatch]:
    """Scan a single file against compiled rules."""
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return []
    if path.stat().st_size > _MAX_FILE_SIZE_BYTES:
        log.warning(f"skipping oversized file for YARA scan: {file_path}")
        return []

    try:
        raw_matches = rules.match(filepath=str(path), timeout=timeout_seconds)
    except yara.Error as exc:
        log.warning(f"YARA scan failed for {file_path}: {exc}")
        return []

    matches: list[YaraMatch] = []
    for match in raw_matches:
        matched_strings = []
        for string_match in getattr(match, "strings", []):
            try:
                identifier = string_match.identifier
                matched_strings.append(identifier)
            except AttributeError:
                continue

        matches.append(
            YaraMatch(
                file_path=str(path),
                rule_name=match.rule,
                tags=list(match.tags),
                meta=dict(match.meta),
                matched_strings=matched_strings,
            )
        )
    return matches


def scan_directory(
    rules: "yara.Rules",
    directory: str,
    recursive: bool = True,
    max_files: int = 5000,
    timeout_seconds_per_file: int = 30,
) -> list[YaraMatch]:
    """Walk `directory` and scan every regular file found against compiled rules."""
    root = Path(directory)
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    all_matches: list[YaraMatch] = []
    scanned = 0

    walker = os.walk(root) if recursive else [(str(root), [], [p.name for p in root.iterdir() if p.is_file()])]

    for dirpath, _dirnames, filenames in walker:
        for filename in filenames:
            if scanned >= max_files:
                log.warning(f"YARA directory scan hit max_files={max_files} cap; stopping early")
                return all_matches
            file_path = os.path.join(dirpath, filename)
            all_matches.extend(scan_file(rules, file_path, timeout_seconds_per_file))
            scanned += 1

    return all_matches


def scan_bytes(rules: "yara.Rules", data: bytes, source_label: str = "<memory>") -> list[YaraMatch]:
    """Scan an in-memory byte buffer (e.g. extracted email attachment) against compiled rules."""
    try:
        raw_matches = rules.match(data=data)
    except yara.Error as exc:
        log.warning(f"YARA in-memory scan failed: {exc}")
        return []

    return [
        YaraMatch(
            file_path=source_label,
            rule_name=match.rule,
            tags=list(match.tags),
            meta=dict(match.meta),
            matched_strings=[s.identifier for s in getattr(match, "strings", [])],
        )
        for match in raw_matches
    ]
