"""
Static file analyzer — read-only triage of a suspicious file: file-type
identification, cryptographic hashes, printable-string extraction, and
basic PE/ELF header metadata. This module never executes or emulates the
analyzed file; it only reads bytes and metadata, which is standard first-
pass malware-triage practice before a sample goes to a sandbox.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import magic

from tools.base import require_binary, run_command
from utils.logger import get_logger

log = get_logger(__name__)

_PRINTABLE_STRING_RE = re.compile(rb"[\x20-\x7e]{6,}")
_MAX_STRINGS_RETURNED = 2000


@dataclass
class FileHashes:
    md5: str
    sha1: str
    sha256: str


@dataclass
class PEMetadata:
    is_pe: bool = False
    machine: Optional[str] = None
    compile_timestamp: Optional[str] = None
    sections: list[dict] = field(default_factory=list)
    imported_dlls: list[str] = field(default_factory=list)
    is_signed: Optional[bool] = None


@dataclass
class StaticAnalysisResult:
    file_path: str
    file_size_bytes: int
    mime_type: str
    hashes: FileHashes
    shannon_entropy: float
    strings_sample: list[str] = field(default_factory=list)
    pe_metadata: Optional[PEMetadata] = None
    error: Optional[str] = None


class FileNotFoundForAnalysisError(FileNotFoundError):
    pass


def _assert_file_exists(file_path: str) -> Path:
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundForAnalysisError(f"File not found: {file_path}")
    return path


def compute_hashes(data: bytes) -> FileHashes:
    return FileHashes(
        md5=hashlib.md5(data).hexdigest(),
        sha1=hashlib.sha1(data).hexdigest(),
        sha256=hashlib.sha256(data).hexdigest(),
    )


def compute_shannon_entropy(data: bytes) -> float:
    """High entropy (>7.5 for byte data) is a common heuristic indicator of
    packed or encrypted payloads and is a standard triage signal, not an
    exploitation primitive."""
    if not data:
        return 0.0
    counts = [0] * 256
    for byte in data:
        counts[byte] += 1
    length = len(data)
    entropy = 0.0
    for count in counts:
        if count == 0:
            continue
        p = count / length
        entropy -= p * math.log2(p)
    return round(entropy, 4)


def extract_printable_strings(data: bytes, min_length: int = 6, limit: int = _MAX_STRINGS_RETURNED) -> list[str]:
    matches = _PRINTABLE_STRING_RE.findall(data)
    decoded = [m.decode("ascii", errors="ignore") for m in matches if len(m) >= min_length]
    return decoded[:limit]


def _parse_pe_metadata(data: bytes) -> Optional[PEMetadata]:
    """Extract lightweight PE header metadata using the `pefile` library if
    available and the file looks like a PE (MZ magic). Returns None for
    non-PE files."""
    if data[:2] != b"MZ":
        return None
    try:
        import pefile  # optional dependency, imported lazily
    except ImportError:
        log.warning("pefile not installed; skipping PE header parsing")
        return PEMetadata(is_pe=True)

    try:
        pe = pefile.PE(data=data, fast_load=True)
        pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"]])

        sections = [
            {
                "name": section.Name.decode(errors="ignore").strip("\x00"),
                "virtual_size": section.Misc_VirtualSize,
                "raw_size": section.SizeOfRawData,
                "entropy": round(section.get_entropy(), 4),
            }
            for section in pe.sections
        ]

        imported_dlls = []
        if hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
            imported_dlls = [entry.dll.decode(errors="ignore") for entry in pe.DIRECTORY_ENTRY_IMPORT]

        return PEMetadata(
            is_pe=True,
            machine=hex(pe.FILE_HEADER.Machine),
            compile_timestamp=str(pe.FILE_HEADER.TimeDateStamp),
            sections=sections,
            imported_dlls=imported_dlls,
            is_signed=hasattr(pe, "DIRECTORY_ENTRY_SECURITY") if hasattr(pe, "OPTIONAL_HEADER") else None,
        )
    except Exception as exc:
        log.warning(f"PE parsing failed: {exc}")
        return PEMetadata(is_pe=True)


async def analyze_file(file_path: str, *, max_bytes_read: int = 100 * 1024 * 1024) -> StaticAnalysisResult:
    """
    Run a full read-only static triage pass over a file: hashing, MIME
    identification, entropy, string extraction, and PE metadata if
    applicable. Intended for analyst review of a quarantined/suspicious
    sample, not for automated execution or unpacking.
    """
    path = _assert_file_exists(file_path)
    size = path.stat().st_size

    with open(path, "rb") as fh:
        data = fh.read(max_bytes_read)

    mime_type = magic.from_buffer(data, mime=True)
    hashes = compute_hashes(data)
    entropy = compute_shannon_entropy(data)
    strings_sample = extract_printable_strings(data)
    pe_metadata = _parse_pe_metadata(data)

    return StaticAnalysisResult(
        file_path=str(path),
        file_size_bytes=size,
        mime_type=mime_type,
        hashes=hashes,
        shannon_entropy=entropy,
        strings_sample=strings_sample,
        pe_metadata=pe_metadata,
    )


async def run_strings_cli(file_path: str, min_length: int = 6, timeout_seconds: int = 60) -> list[str]:
    """Fallback path using the system `strings` binary (useful when a very
    large file makes in-Python regex extraction slow)."""
    path = _assert_file_exists(file_path)
    binary = require_binary("strings")
    argv = [binary, "-n", str(min_length), str(path)]
    result = await run_command(argv, timeout_seconds=timeout_seconds)
    if not result.succeeded:
        return []
    return result.stdout.splitlines()[:_MAX_STRINGS_RETURNED]
