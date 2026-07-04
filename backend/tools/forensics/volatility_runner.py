"""
Volatility 3 wrapper — memory image analysis for incident response and
forensic investigations (process listing, network connections, malfind,
DLL/handle enumeration, registry/hive dumps, etc).

Volatility 3 is invoked as `vol -f <image> <plugin> [plugin-args]` with
`-r json` for structured output wherever the plugin supports it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from tools.base import ToolRunResult, require_binary, run_command
from utils.logger import get_logger
from utils.parser_utils import parse_json_safe

log = get_logger(__name__)

# Plugins we expose through the API. Keys are the short names used by
# routers/forensics.py; values are the actual Volatility3 plugin symbols.
SUPPORTED_PLUGINS: dict[str, str] = {
    "pslist": "windows.pslist.PsList",
    "pstree": "windows.pstree.PsTree",
    "psscan": "windows.psscan.PsScan",
    "netscan": "windows.netscan.NetScan",
    "malfind": "windows.malfind.Malfind",
    "dlllist": "windows.dlllist.DllList",
    "handles": "windows.handles.Handles",
    "cmdline": "windows.cmdline.CmdLine",
    "hivelist": "windows.registry.hivelist.HiveList",
    "filescan": "windows.filescan.FileScan",
    "linux_pslist": "linux.pslist.PsList",
    "linux_bash": "linux.bash.Bash",
    "linux_netstat": "linux.netstat.Netstat",
}


@dataclass
class VolatilityResult:
    plugin: str
    memory_image: str
    records: list[dict] = field(default_factory=list)
    raw: ToolRunResult = None
    error: Optional[str] = None


class InvalidPluginError(ValueError):
    pass


class MemoryImageNotFoundError(FileNotFoundError):
    pass


def _assert_valid_plugin(plugin_key: str) -> str:
    if plugin_key not in SUPPORTED_PLUGINS:
        raise InvalidPluginError(
            f"Unsupported plugin '{plugin_key}'. Supported: {sorted(SUPPORTED_PLUGINS)}"
        )
    return SUPPORTED_PLUGINS[plugin_key]


def _assert_image_exists(image_path: str) -> str:
    path = Path(image_path)
    if not path.exists() or not path.is_file():
        raise MemoryImageNotFoundError(f"Memory image not found: {image_path}")
    return str(path)


async def run_plugin(
    memory_image: str,
    plugin_key: str,
    *,
    extra_args: Optional[list[str]] = None,
    timeout_seconds: int = 900,
) -> VolatilityResult:
    """
    Run a single Volatility3 plugin against a memory image and return
    parsed JSON records (Volatility3 emits a JSON array with `-r json`).
    """
    binary = require_binary("vol")
    plugin_symbol = _assert_valid_plugin(plugin_key)
    image = _assert_image_exists(memory_image)

    argv = [binary, "-q", "-r", "json", "-f", image, plugin_symbol]
    if extra_args:
        # extra_args are plugin-specific flags (e.g. --pid 1234) supplied by
        # the API layer after its own Pydantic validation — never raw user
        # strings interpolated into a shell.
        argv.extend(extra_args)

    result = await run_command(argv, timeout_seconds=timeout_seconds)

    if not result.succeeded:
        log.warning(f"volatility plugin {plugin_key} failed: {result.stderr[:500]}")
        return VolatilityResult(
            plugin=plugin_key,
            memory_image=image,
            raw=result,
            error=result.stderr[:2000] or "volatility exited non-zero",
        )

    parsed = parse_json_safe(result.stdout)
    records = parsed if isinstance(parsed, list) else []

    return VolatilityResult(
        plugin=plugin_key,
        memory_image=image,
        records=records,
        raw=result,
    )


async def identify_image_profile(memory_image: str, timeout_seconds: int = 300) -> ToolRunResult:
    """Run `windows.info.Info` (or `banners.Banners` as a cross-OS fallback) to
    identify the OS/build of a memory image before choosing plugins."""
    binary = require_binary("vol")
    image = _assert_image_exists(memory_image)
    argv = [binary, "-q", "-r", "json", "-f", image, "banners.Banners"]
    return await run_command(argv, timeout_seconds=timeout_seconds)


async def run_triage_suite(
    memory_image: str,
    *,
    os_hint: str = "windows",
    timeout_seconds_per_plugin: int = 600,
) -> list[VolatilityResult]:
    """
    Run a standard first-pass triage set of plugins for quick IR findings:
    processes, network connections, and code-injection indicators (malfind).
    Returns one VolatilityResult per plugin so a partial failure doesn't
    block the rest of the suite.
    """
    plugin_set = (
        ["pslist", "netscan", "malfind", "cmdline"]
        if os_hint == "windows"
        else ["linux_pslist", "linux_netstat", "linux_bash"]
    )

    results: list[VolatilityResult] = []
    for plugin_key in plugin_set:
        try:
            results.append(
                await run_plugin(memory_image, plugin_key, timeout_seconds=timeout_seconds_per_plugin)
            )
        except (InvalidPluginError, MemoryImageNotFoundError) as exc:
            results.append(
                VolatilityResult(plugin=plugin_key, memory_image=memory_image, error=str(exc))
            )
    return results
