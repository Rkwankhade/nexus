"""
Shared base for all tool wrappers (recon, scanning, blue-team, forensics).

Provides a single async subprocess runner with:
  - list-form argv only (never shell=True) to prevent shell injection
  - timeout enforcement
  - output size capping
  - structured result object tool_orchestrator/services can persist

Every concrete wrapper module builds its argv list from *validated* inputs
(see utils.parser_utils.assert_safe_hostname_or_ip / assert_safe_url) and
calls `run_command`. No wrapper should ever build a raw shell string.
"""

from __future__ import annotations

import asyncio
import shutil
from dataclasses import dataclass, field
from typing import Optional

from utils.logger import get_logger
from utils.parser_utils import truncate_output, utcnow_iso

log = get_logger(__name__)


class ToolNotInstalledError(RuntimeError):
    """Raised when the underlying CLI binary isn't present on PATH."""


@dataclass
class ToolRunResult:
    tool: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool
    started_at: str
    finished_at: str
    duration_seconds: float

    @property
    def succeeded(self) -> bool:
        return self.returncode == 0 and not self.timed_out


def require_binary(binary_name: str) -> str:
    """Resolve a CLI tool's path or raise a clear error if it's missing."""
    path = shutil.which(binary_name)
    if path is None:
        raise ToolNotInstalledError(
            f"'{binary_name}' is not installed or not on PATH. "
            f"Install it on the NEXUS host/container before running this tool."
        )
    return path


async def run_command(
    argv: list[str],
    *,
    timeout_seconds: int = 300,
    cwd: Optional[str] = None,
    env: Optional[dict[str, str]] = None,
    max_output_chars: int = 200_000,
    on_output_line: Optional[callable] = None,
) -> ToolRunResult:
    """
    Run a tool as a subprocess using list-form argv (no shell interpolation).

    `on_output_line`, if provided, is called with each decoded stdout line
    as it arrives — used by the notification service to stream live
    progress over WebSocket while the process is still running.
    """
    tool_name = argv[0]
    started = asyncio.get_event_loop().time()
    started_at = utcnow_iso()

    log.info(f"starting tool run: {tool_name}", extra={"extra_fields": {"argv": argv}})

    process = await asyncio.create_subprocess_exec(
        *argv,
        cwd=cwd,
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout_chunks: list[str] = []
    timed_out = False

    async def _stream_stdout():
        assert process.stdout is not None
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            decoded = line.decode(errors="replace")
            stdout_chunks.append(decoded)
            if on_output_line:
                try:
                    on_output_line(decoded.rstrip("\n"))
                except Exception:
                    log.warning("on_output_line callback raised", exc_info=True)

    try:
        await asyncio.wait_for(_stream_stdout(), timeout=timeout_seconds)
        stderr_bytes = await asyncio.wait_for(process.stderr.read(), timeout=10)
        await asyncio.wait_for(process.wait(), timeout=10)
    except asyncio.TimeoutError:
        timed_out = True
        process.kill()
        await process.wait()
        stderr_bytes = b""

    finished = asyncio.get_event_loop().time()
    stdout_text = truncate_output("".join(stdout_chunks), max_output_chars)
    stderr_text = truncate_output(
        stderr_bytes.decode(errors="replace") if isinstance(stderr_bytes, bytes) else "",
        max_output_chars,
    )

    result = ToolRunResult(
        tool=tool_name,
        command=argv,
        returncode=process.returncode if process.returncode is not None else -1,
        stdout=stdout_text,
        stderr=stderr_text,
        timed_out=timed_out,
        started_at=started_at,
        finished_at=utcnow_iso(),
        duration_seconds=round(finished - started, 2),
    )

    log.info(
        f"finished tool run: {tool_name}",
        extra={
            "extra_fields": {
                "returncode": result.returncode,
                "timed_out": timed_out,
                "duration_seconds": result.duration_seconds,
            }
        },
    )
    return result
