#!/usr/bin/env python3
"""
nexus_cli.py — command-line client for the NEXUS Cyber Operations Platform API.

A single-file, Typer-based CLI covering auth, targets, scans, findings,
reports, alerts, blue-team (SIEM/rules), forensics, and AI analysis.
Talks to the same FastAPI backend the web dashboard uses.

Design notes:
  * Credentials are cached at ~/.nexus/credentials.json (0600) after `nexus auth login`.
  * Every command supports --output/-o {table,json,csv} for scripting.
  * Long-running jobs (scans, forensics) support --watch to poll with a
    live progress bar until the job finishes.
  * Multiple named profiles (--profile) let you point at dev/staging/prod
    backends without re-authenticating each time.
  * Intentionally scoped to reconnaissance, scanning, findings, reporting,
    blue-team, and forensic analysis — this client has no commands for
    exploitation, credential attacks, or lateral movement, mirroring the
    backend's own tool boundary.

Install:
    pip install typer[all] httpx rich

Usage:
    nexus auth login
    nexus targets list
    nexus targets create --name "Corp DMZ" --value 10.10.0.0/24 --type ip_range \
        --auth-ref "SOW-2026-014"
    nexus scans run --target <id> --tool nmap --type port_scan --watch
    nexus findings list --severity critical
    nexus reports create --target <id> --title "Q3 Assessment" --format pdf
    nexus forensics memory --image /evidence/host01.mem --watch
    nexus ai chat "Summarize the top risks for target X"
"""
from __future__ import annotations

import csv
import io
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import httpx
import typer
from rich.console import Console
from rich.json import JSON as RichJSON
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table

# --------------------------------------------------------------------------- #
# Config & session storage
# --------------------------------------------------------------------------- #

CONFIG_DIR = Path(os.environ.get("NEXUS_CLI_HOME", Path.home() / ".nexus"))
CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULT_PROFILE = "default"

SEVERITY_COLOR = {
    "critical": "bold white on red",
    "high": "bold red",
    "medium": "bold yellow",
    "low": "cyan",
    "info": "dim",
}
STATUS_COLOR = {
    "queued": "dim",
    "running": "yellow",
    "completed": "green",
    "ready": "green",
    "failed": "bold red",
    "cancelled": "dim strike",
    "generating": "yellow",
    "pending": "dim",
}

console = Console()
err_console = Console(stderr=True)


@dataclass
class ProfileConfig:
    base_url: str = "http://localhost:8000/api"
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    username: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "base_url": self.base_url,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "username": self.username,
        }


@dataclass
class CliConfig:
    profiles: dict[str, ProfileConfig] = field(default_factory=dict)
    active_profile: str = DEFAULT_PROFILE

    @classmethod
    def load(cls) -> "CliConfig":
        if not CONFIG_FILE.exists():
            return cls(profiles={DEFAULT_PROFILE: ProfileConfig()})
        raw = json.loads(CONFIG_FILE.read_text())
        profiles = {
            name: ProfileConfig(**data) for name, data in raw.get("profiles", {}).items()
        }
        if DEFAULT_PROFILE not in profiles:
            profiles[DEFAULT_PROFILE] = ProfileConfig()
        return cls(profiles=profiles, active_profile=raw.get("active_profile", DEFAULT_PROFILE))

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "active_profile": self.active_profile,
            "profiles": {name: p.to_dict() for name, p in self.profiles.items()},
        }
        CONFIG_FILE.write_text(json.dumps(payload, indent=2))
        CONFIG_FILE.chmod(0o600)

    def profile(self, name: Optional[str] = None) -> ProfileConfig:
        key = name or self.active_profile
        if key not in self.profiles:
            self.profiles[key] = ProfileConfig()
        return self.profiles[key]


# --------------------------------------------------------------------------- #
# API client
# --------------------------------------------------------------------------- #


class ApiError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


class NexusClient:
    """Thin wrapper over httpx with auth-header injection and 401 refresh."""

    def __init__(self, config: CliConfig, profile_name: Optional[str] = None):
        self.config = config
        self.profile_name = profile_name or config.active_profile
        self.profile = config.profile(self.profile_name)
        self._client = httpx.Client(base_url=self.profile.base_url, timeout=30.0)

    # -- low level ---------------------------------------------------------
    def _headers(self) -> dict:
        headers = {}
        if self.profile.access_token:
            headers["Authorization"] = f"Bearer {self.profile.access_token}"
        return headers

    def _request(self, method: str, path: str, retry_on_401: bool = True, **kwargs) -> Any:
        resp = self._client.request(method, path, headers=self._headers(), **kwargs)
        if resp.status_code == 401 and retry_on_401 and self.profile.refresh_token:
            if self._refresh():
                resp = self._client.request(method, path, headers=self._headers(), **kwargs)
        if resp.status_code >= 400:
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            raise ApiError(resp.status_code, str(detail))
        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    def _refresh(self) -> bool:
        try:
            resp = self._client.post(
                "/auth/refresh", json={"refresh_token": self.profile.refresh_token}
            )
            if resp.status_code != 200:
                return False
            data = resp.json()
            self.profile.access_token = data["access_token"]
            self.config.save()
            return True
        except httpx.HTTPError:
            return False

    def get(self, path: str, params: Optional[dict] = None) -> Any:
        return self._request("GET", path, params=_clean(params))

    def post(self, path: str, json_body: Optional[dict] = None) -> Any:
        return self._request("POST", path, json=json_body or {})

    def patch(self, path: str, json_body: Optional[dict] = None) -> Any:
        return self._request("PATCH", path, json=json_body or {})

    def delete(self, path: str) -> Any:
        return self._request("DELETE", path)

    # -- auth ----------------------------------------------------------
    def login(self, username: str, password: str) -> dict:
        resp = self._client.post(
            "/auth/login", json={"username": username, "password": password}
        )
        if resp.status_code >= 400:
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            raise ApiError(resp.status_code, str(detail))
        data = resp.json()
        self.profile.access_token = data["access_token"]
        self.profile.refresh_token = data["refresh_token"]
        self.profile.username = data["user"]["username"]
        self.config.save()
        return data

    def download(self, path: str, dest: Path) -> Path:
        with self._client.stream("GET", path, headers=self._headers()) as resp:
            if resp.status_code >= 400:
                raise ApiError(resp.status_code, resp.read().decode(errors="ignore"))
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "wb") as f:
                for chunk in resp.iter_bytes():
                    f.write(chunk)
        return dest


def _clean(params: Optional[dict]) -> Optional[dict]:
    if not params:
        return None
    return {k: v for k, v in params.items() if v is not None}


# --------------------------------------------------------------------------- #
# Output rendering
# --------------------------------------------------------------------------- #

OutputFormat = typer.Option("table", "--output", "-o", help="table | json | csv")


def render(data: Any, fmt: str = "table", columns: Optional[list[str]] = None, title: str = ""):
    if fmt == "json":
        console.print(RichJSON(json.dumps(data, default=str)))
        return

    rows = data if isinstance(data, list) else [data]
    if not rows:
        console.print("[dim]No results.[/dim]")
        return

    if fmt == "csv":
        cols = columns or list(rows[0].keys())
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in cols})
        console.print(buf.getvalue())
        return

    cols = columns or list(rows[0].keys())
    table = Table(title=title or None, show_lines=False, header_style="bold cyan")
    for c in cols:
        table.add_column(c)
    for row in rows:
        cells = []
        for c in cols:
            val = row.get(c, "")
            cells.append(_format_cell(c, val))
        table.add_row(*cells)
    console.print(table)


def _format_cell(col: str, val: Any) -> str:
    if val is None:
        return "[dim]—[/dim]"
    if col == "severity" and isinstance(val, str):
        style = SEVERITY_COLOR.get(val.lower(), "")
        return f"[{style}]{val}[/{style}]" if style else val
    if col == "status" and isinstance(val, str):
        style = STATUS_COLOR.get(val.lower(), "")
        return f"[{style}]{val}[/{style}]" if style else val
    if isinstance(val, (dict, list)):
        return json.dumps(val, default=str)[:80]
    if isinstance(val, str) and len(val) > 60:
        return val[:57] + "…"
    return str(val)


def die(message: str, code: int = 1):
    err_console.print(f"[bold red]Error:[/bold red] {message}")
    raise typer.Exit(code)


def handle_api_error(fn):
    """Decorator: convert ApiError into a clean CLI error rather than a traceback."""
    import functools

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ApiError as e:
            die(f"[{e.status_code}] {e.detail}")
        except httpx.ConnectError:
            die("Could not reach the NEXUS API. Check --profile / base URL and that the backend is running.")
        except httpx.TimeoutException:
            die("Request timed out.")

    return wrapper


# --------------------------------------------------------------------------- #
# Global app / shared state
# --------------------------------------------------------------------------- #

app = typer.Typer(
    name="nexus",
    help="NEXUS Cyber Operations Platform — command-line client",
    add_completion=True,
    no_args_is_help=True,
)

state: dict[str, Any] = {}


@app.callback()
def main(
    ctx: typer.Context,
    profile: str = typer.Option(DEFAULT_PROFILE, "--profile", "-p", help="Config profile to use"),
    base_url: Optional[str] = typer.Option(None, "--base-url", help="Override the API base URL"),
):
    """NEXUS CLI — manage targets, scans, findings, reports, blue-team and forensics from the terminal."""
    config = CliConfig.load()
    if base_url:
        config.profile(profile).base_url = base_url
    config.active_profile = profile
    state["config"] = config
    state["client"] = NexusClient(config, profile_name=profile)


def client() -> NexusClient:
    return state["client"]


def cfg() -> CliConfig:
    return state["config"]


# --------------------------------------------------------------------------- #
# auth
# --------------------------------------------------------------------------- #

auth_app = typer.Typer(help="Authenticate and manage CLI sessions")
app.add_typer(auth_app, name="auth")


@auth_app.command("login")
@handle_api_error
def auth_login(
    username: Optional[str] = typer.Option(None, "--username", "-u"),
    password: Optional[str] = typer.Option(None, "--password", hide_input=True),
):
    """Log in and cache access/refresh tokens for the active profile."""
    username = username or Prompt.ask("Username")
    password = password or Prompt.ask("Password", password=True)
    data = client().login(username, password)
    user = data["user"]
    console.print(
        Panel(
            f"[green]Logged in[/green] as [bold]{user['username']}[/bold] "
            f"({user['role']}) on profile [bold]{cfg().active_profile}[/bold]",
            expand=False,
        )
    )


@auth_app.command("logout")
def auth_logout():
    """Clear cached tokens for the active profile."""
    profile = cfg().profile()
    profile.access_token = None
    profile.refresh_token = None
    cfg().save()
    console.print("[green]Logged out.[/green]")


@auth_app.command("whoami")
@handle_api_error
def auth_whoami(output: str = OutputFormat):
    """Show the currently authenticated user."""
    me = client().get("/auth/me")
    render(me, output, columns=["username", "email", "role", "is_active", "mfa_enabled"])


@auth_app.command("profiles")
def auth_profiles():
    """List configured profiles and which one is active."""
    table = Table(header_style="bold cyan")
    table.add_column("Profile")
    table.add_column("Base URL")
    table.add_column("Logged in as")
    table.add_column("Active")
    for name, p in cfg().profiles.items():
        table.add_row(
            name,
            p.base_url,
            p.username or "[dim]—[/dim]",
            "✓" if name == cfg().active_profile else "",
        )
    console.print(table)


# --------------------------------------------------------------------------- #
# targets
# --------------------------------------------------------------------------- #

targets_app = typer.Typer(help="Manage engagement targets and their authorization status")
app.add_typer(targets_app, name="targets")

TARGET_TYPES = ["domain", "ip", "ip_range", "url", "wireless_ssid"]


@targets_app.command("list")
@handle_api_error
def targets_list(output: str = OutputFormat):
    """List all targets."""
    data = client().get("/targets")
    render(data, output, columns=["id", "name", "value", "type", "status", "created_at"])


@targets_app.command("get")
@handle_api_error
def targets_get(target_id: str, output: str = OutputFormat):
    """Show a single target."""
    data = client().get(f"/targets/{target_id}")
    render(data, output)


@targets_app.command("create")
@handle_api_error
def targets_create(
    name: str = typer.Option(..., "--name", "-n"),
    value: str = typer.Option(..., "--value", help="IP / CIDR / domain / URL / SSID"),
    type_: str = typer.Option(..., "--type", "-t", help=f"One of: {', '.join(TARGET_TYPES)}"),
    description: str = typer.Option("", "--description", "-d"),
    auth_ref: str = typer.Option(
        "", "--auth-ref", help="Authorization reference — required to move to AUTHORIZED"
    ),
    output: str = OutputFormat,
):
    """Create a new target. Without --auth-ref it stays PENDING_AUTH and cannot be scanned."""
    if type_ not in TARGET_TYPES:
        die(f"--type must be one of: {', '.join(TARGET_TYPES)}")
    payload = {
        "name": name,
        "value": value,
        "type": type_,
        "description": description,
        "authorization_reference": auth_ref,
    }
    data = client().post("/targets", payload)
    console.print(f"[green]Created target[/green] {data['id']}")
    render(data, output)


@targets_app.command("authorize")
@handle_api_error
def targets_authorize(
    target_id: str,
    auth_ref: str = typer.Option(..., "--auth-ref", help="Ticket/contract reference proving scope"),
    output: str = OutputFormat,
):
    """Mark a target AUTHORIZED. Refuses without a reference (same rule the API enforces)."""
    data = client().patch(
        f"/targets/{target_id}",
        {"status": "authorized", "authorization_reference": auth_ref},
    )
    console.print(f"[green]Target {target_id} authorized.[/green]")
    render(data, output)


@targets_app.command("delete")
def targets_delete(target_id: str, yes: bool = typer.Option(False, "--yes", "-y")):
    """Delete a target."""
    if not yes and not Confirm.ask(f"Delete target {target_id}? This cannot be undone"):
        raise typer.Abort()
    try:
        client().delete(f"/targets/{target_id}")
    except ApiError as e:
        die(f"[{e.status_code}] {e.detail}")
    console.print("[green]Deleted.[/green]")


# --------------------------------------------------------------------------- #
# scans
# --------------------------------------------------------------------------- #

scans_app = typer.Typer(help="Dispatch and track reconnaissance / scanning jobs")
app.add_typer(scans_app, name="scans")

SCAN_TYPES = ["recon", "port_scan", "vuln_scan", "web_scan", "wireless_scan"]
RECON_SCAN_TOOLS = {"nmap", "amass", "theharvester", "shodan", "whois", "dnsx"}
VULN_SCAN_TOOLS = {"nuclei", "nikto", "openvas", "wpscan"}
WEB_SCAN_TOOLS = {"ffuf", "wfuzz", "dalfox"}


@scans_app.command("list")
@handle_api_error
def scans_list(
    target: Optional[str] = typer.Option(None, "--target", "-t"),
    output: str = OutputFormat,
):
    """List scans, optionally filtered by target."""
    data = client().get("/scans", params={"target_id": target})
    render(data, output, columns=["id", "tool", "scan_type", "status", "progress_pct", "created_at"])


@scans_app.command("run")
@handle_api_error
def scans_run(
    target: str = typer.Option(..., "--target", "-t"),
    tool: str = typer.Option(..., "--tool", help="e.g. nmap, nuclei, ffuf, amass"),
    scan_type: Optional[str] = typer.Option(
        None, "--type", help=f"One of: {', '.join(SCAN_TYPES)} (inferred from --tool if omitted)"
    ),
    param: list[str] = typer.Option(
        [], "--param", help="key=value scan parameter, repeatable, e.g. --param ports=1-1000"
    ),
    watch: bool = typer.Option(False, "--watch", "-w", help="Poll and show a live progress bar"),
    output: str = OutputFormat,
):
    """Dispatch a recon/scanning/web tool run against an authorized target."""
    inferred_type = scan_type or _infer_scan_type(tool)
    if inferred_type not in SCAN_TYPES:
        die(f"--type must be one of: {', '.join(SCAN_TYPES)}")
    parameters = _parse_kv_list(param)
    data = client().post(
        "/scans", {"target_id": target, "scan_type": inferred_type, "tool": tool, "parameters": parameters}
    )
    console.print(f"[green]Scan dispatched[/green] {data['id']} ({tool})")
    if watch:
        _watch_job(lambda: client().get(f"/scans/{data['id']}"), label=f"{tool} scan")
    else:
        render(data, output)


def _infer_scan_type(tool: str) -> str:
    t = tool.lower()
    if t in VULN_SCAN_TOOLS:
        return "vuln_scan"
    if t in WEB_SCAN_TOOLS:
        return "web_scan"
    if t in RECON_SCAN_TOOLS:
        return "recon"
    return "recon"


@scans_app.command("get")
@handle_api_error
def scans_get(scan_id: str, output: str = OutputFormat):
    """Show a single scan's status/result."""
    render(client().get(f"/scans/{scan_id}"), output)


@scans_app.command("cancel")
@handle_api_error
def scans_cancel(scan_id: str):
    """Cancel a queued or running scan."""
    client().post(f"/scans/{scan_id}/cancel")
    console.print(f"[yellow]Scan {scan_id} cancelled.[/yellow]")


@scans_app.command("watch")
@handle_api_error
def scans_watch(scan_id: str):
    """Attach a live progress bar to an already-running scan."""
    _watch_job(lambda: client().get(f"/scans/{scan_id}"), label="scan")


# --------------------------------------------------------------------------- #
# findings
# --------------------------------------------------------------------------- #

findings_app = typer.Typer(help="Review and triage findings")
app.add_typer(findings_app, name="findings")

SEVERITIES = ["critical", "high", "medium", "low", "info"]
FINDING_STATUSES = ["open", "confirmed", "false_positive", "remediated", "accepted_risk"]


@findings_app.command("list")
@handle_api_error
def findings_list(
    target: Optional[str] = typer.Option(None, "--target", "-t"),
    severity: Optional[str] = typer.Option(None, "--severity", "-s"),
    output: str = OutputFormat,
):
    """List findings, optionally filtered by target and/or severity."""
    if severity and severity not in SEVERITIES:
        die(f"--severity must be one of: {', '.join(SEVERITIES)}")
    data = client().get("/findings", params={"target_id": target, "severity": severity})
    render(
        data,
        output,
        columns=["id", "title", "severity", "status", "tool", "cvss_score", "created_at"],
    )


@findings_app.command("get")
@handle_api_error
def findings_get(finding_id: str, output: str = OutputFormat):
    """Show full detail for a finding, including AI analysis if present."""
    render(client().get(f"/findings/{finding_id}"), output)


@findings_app.command("triage")
@handle_api_error
def findings_triage(
    finding_id: str,
    status: str = typer.Option(..., "--status", "-s", help=f"One of: {', '.join(FINDING_STATUSES)}"),
    remediation: Optional[str] = typer.Option(None, "--remediation"),
):
    """Update a finding's status (and optionally remediation notes)."""
    if status not in FINDING_STATUSES:
        die(f"--status must be one of: {', '.join(FINDING_STATUSES)}")
    payload = {"status": status}
    if remediation:
        payload["remediation"] = remediation
    client().patch(f"/findings/{finding_id}", payload)
    console.print(f"[green]Finding {finding_id} → {status}[/green]")


@findings_app.command("stats")
@handle_api_error
def findings_stats(target: Optional[str] = typer.Option(None, "--target", "-t")):
    """Severity breakdown for a target (or globally)."""
    data = client().get("/findings", params={"target_id": target})
    counts = {s: 0 for s in SEVERITIES}
    for f in data:
        counts[f.get("severity", "info")] = counts.get(f.get("severity", "info"), 0) + 1

    table = Table(title="Findings by Severity", header_style="bold cyan")
    table.add_column("Severity")
    table.add_column("Count", justify="right")
    for s in SEVERITIES:
        style = SEVERITY_COLOR.get(s, "")
        table.add_row(f"[{style}]{s}[/{style}]", str(counts[s]))
    console.print(table)


# --------------------------------------------------------------------------- #
# reports
# --------------------------------------------------------------------------- #

reports_app = typer.Typer(help="Generate and download assessment reports")
app.add_typer(reports_app, name="reports")

REPORT_FORMATS = ["pdf", "html", "json"]


@reports_app.command("list")
@handle_api_error
def reports_list(
    target: Optional[str] = typer.Option(None, "--target", "-t"),
    output: str = OutputFormat,
):
    data = client().get("/reports", params={"target_id": target})
    render(data, output, columns=["id", "title", "format", "status", "created_at"])


@reports_app.command("create")
@handle_api_error
def reports_create(
    target: str = typer.Option(..., "--target", "-t"),
    title: str = typer.Option(..., "--title"),
    format_: str = typer.Option("pdf", "--format", "-f"),
    finding: list[str] = typer.Option([], "--finding", help="Finding ID to include, repeatable"),
    watch: bool = typer.Option(True, "--watch/--no-watch", help="Poll until the report is ready"),
    download_to: Optional[Path] = typer.Option(
        None, "--download-to", help="Download the file here once ready"
    ),
):
    """Generate a new report, optionally scoped to specific findings."""
    if format_ not in REPORT_FORMATS:
        die(f"--format must be one of: {', '.join(REPORT_FORMATS)}")
    data = client().post(
        "/reports",
        {"target_id": target, "title": title, "format": format_, "finding_ids": finding},
    )
    console.print(f"[green]Report queued[/green] {data['id']}")

    if watch:
        final = _watch_job(
            lambda: client().get(f"/reports/{data['id']}"), label="report", terminal_states={"ready", "failed"}
        )
        if final and final.get("status") == "ready" and download_to:
            path = client().download(f"/reports/{data['id']}/download", download_to)
            console.print(f"[green]Downloaded to[/green] {path}")


@reports_app.command("download")
@handle_api_error
def reports_download(
    report_id: str,
    dest: Path = typer.Option(..., "--to", help="Destination file path"),
):
    """Download a ready report."""
    path = client().download(f"/reports/{report_id}/download", dest)
    console.print(f"[green]Downloaded to[/green] {path}")


# --------------------------------------------------------------------------- #
# alerts
# --------------------------------------------------------------------------- #

alerts_app = typer.Typer(help="View and acknowledge platform alerts")
app.add_typer(alerts_app, name="alerts")

ALERT_STATUSES = ["open", "acknowledged", "resolved", "suppressed"]


@alerts_app.command("list")
@handle_api_error
def alerts_list(
    status_filter: Optional[str] = typer.Option(None, "--status"),
    severity: Optional[str] = typer.Option(None, "--severity"),
    output: str = OutputFormat,
):
    data = client().get("/alerts", params={"status_filter": status_filter, "severity": severity})
    render(data, output, columns=["id", "title", "severity", "source", "created_at"])


@alerts_app.command("ack")
@handle_api_error
def alerts_ack(alert_id: str):
    """Acknowledge an alert."""
    client().patch(f"/alerts/{alert_id}", {"status": "acknowledged"})
    console.print(f"[green]Alert {alert_id} acknowledged.[/green]")


@alerts_app.command("watch")
@handle_api_error
def alerts_watch(
    interval: int = typer.Option(10, "--interval", "-i", help="Seconds between polls"),
):
    """Continuously poll for open alerts (Ctrl+C to stop)."""
    console.print("[dim]Watching for open alerts — Ctrl+C to stop…[/dim]")
    seen: set[str] = set()
    try:
        while True:
            data = client().get("/alerts", params={"status_filter": "open"})
            for a in data:
                if a["id"] not in seen:
                    seen.add(a["id"])
                    style = SEVERITY_COLOR.get(a.get("severity", "info"), "")
                    console.print(
                        f"[{style}][{a['severity'].upper()}][/{style}] {a['title']} "
                        f"[dim]({a['source']}, {a['created_at']})[/dim]"
                    )
            time.sleep(interval)
    except KeyboardInterrupt:
        console.print("\n[dim]Stopped.[/dim]")


# --------------------------------------------------------------------------- #
# blueteam
# --------------------------------------------------------------------------- #

blueteam_app = typer.Typer(help="SIEM log queries and detection rule management")
app.add_typer(blueteam_app, name="blueteam")


@blueteam_app.command("logs")
@handle_api_error
def blueteam_logs(
    source: Optional[str] = typer.Option(None, "--source"),
    limit: int = typer.Option(50, "--limit", "-n"),
    output: str = OutputFormat,
):
    """Query the aggregated SIEM log stream."""
    data = client().get("/blueteam/siem/logs", params={"source": source, "limit": limit})
    render(data, output, columns=["ingested_at", "source", "host", "event_type", "message"])


@blueteam_app.command("rules")
@handle_api_error
def blueteam_rules(output: str = OutputFormat):
    """List active Sigma / Suricata / YARA detection rules."""
    data = client().get("/blueteam/rules")
    render(data, output, columns=["name", "engine", "severity", "enabled", "match_count"])


# --------------------------------------------------------------------------- #
# forensics
# --------------------------------------------------------------------------- #

forensics_app = typer.Typer(help="Dispatch memory / disk / malware forensic analysis jobs")
app.add_typer(forensics_app, name="forensics")


@forensics_app.command("memory")
@handle_api_error
def forensics_memory(
    image: str = typer.Option(..., "--image", help="Path to the memory image"),
    profile: str = typer.Option("auto", "--profile"),
    plugin: list[str] = typer.Option(
        ["pslist", "netscan", "malfind"], "--plugin", help="Volatility plugin, repeatable"
    ),
    watch: bool = typer.Option(True, "--watch/--no-watch"),
):
    """Run Volatility plugins against a memory image."""
    data = client().post(
        "/forensics/memory/analyze",
        {"image_path": image, "profile": profile, "plugins": plugin},
    )
    console.print(f"[green]Job dispatched[/green] {data['id']}")
    if watch:
        _watch_job(lambda: client().get(f"/forensics/jobs/{data['id']}"), label="memory analysis")


@forensics_app.command("disk")
@handle_api_error
def forensics_disk(
    image: str = typer.Option(..., "--image", help="Path to the disk image"),
    filesystem: str = typer.Option("auto", "--filesystem"),
    module: list[str] = typer.Option(
        ["timeline", "deleted_files", "registry", "browser_artifacts"], "--module"
    ),
    watch: bool = typer.Option(True, "--watch/--no-watch"),
):
    """Run Autopsy-based modules against a disk image."""
    data = client().post(
        "/forensics/disk/analyze",
        {"image_path": image, "filesystem": filesystem, "modules": module},
    )
    console.print(f"[green]Job dispatched[/green] {data['id']}")
    if watch:
        _watch_job(lambda: client().get(f"/forensics/jobs/{data['id']}"), label="disk analysis")


@forensics_app.command("malware")
@handle_api_error
def forensics_malware(
    file: str = typer.Option(..., "--file", help="Path to the sample"),
    deep: bool = typer.Option(False, "--deep", help="Full ruleset + entropy analysis"),
    watch: bool = typer.Option(True, "--watch/--no-watch"),
):
    """Static YARA signature scan of a file. No code execution."""
    data = client().post(
        "/forensics/malware/scan", {"file_path": file, "deep_scan": deep}
    )
    console.print(f"[green]Job dispatched[/green] {data['id']}")
    if watch:
        _watch_job(lambda: client().get(f"/forensics/jobs/{data['id']}"), label="malware scan")


@forensics_app.command("pcap")
@handle_api_error
def forensics_pcap(
    pcap: str = typer.Option(..., "--pcap", help="Path to the packet capture"),
    watch: bool = typer.Option(True, "--watch/--no-watch"),
):
    """Analyze a packet capture."""
    data = client().post("/forensics/pcap/analyze", {"pcap_path": pcap})
    console.print(f"[green]Job dispatched[/green] {data['id']}")
    if watch:
        _watch_job(lambda: client().get(f"/forensics/jobs/{data['id']}"), label="pcap analysis")


@forensics_app.command("job")
@handle_api_error
def forensics_job(job_id: str, output: str = OutputFormat):
    """Show a forensics job's current status/result."""
    render(client().get(f"/forensics/jobs/{job_id}"), output)


# --------------------------------------------------------------------------- #
# ai
# --------------------------------------------------------------------------- #

ai_app = typer.Typer(help="AI chat and finding/target analysis")
app.add_typer(ai_app, name="ai")


@ai_app.command("chat")
@handle_api_error
def ai_chat(
    message: str,
    conversation: Optional[str] = typer.Option(None, "--conversation", "-c"),
):
    """Send a message to the AI assistant."""
    data = client().post("/ai/chat", {"message": message, "conversation_id": conversation})
    console.print(Panel(data["reply"], title="NEXUS AI", border_style="cyan"))
    console.print(f"[dim]conversation: {data['conversation_id']}[/dim]")


@ai_app.command("analyze-finding")
@handle_api_error
def ai_analyze_finding(finding_id: str, output: str = OutputFormat):
    """Request (or refresh) AI analysis for a finding."""
    data = client().post(f"/ai/analyze-finding/{finding_id}")
    render(data, output)


@ai_app.command("summarize-target")
@handle_api_error
def ai_summarize_target(target_id: str, output: str = OutputFormat):
    """Get an AI-generated security posture summary for a target."""
    data = client().post(f"/ai/summarize-target/{target_id}")
    render(data, output)


# --------------------------------------------------------------------------- #
# shared job-watching helper
# --------------------------------------------------------------------------- #


def _parse_kv_list(pairs: list[str]) -> dict:
    result: dict[str, Any] = {}
    for pair in pairs:
        if "=" not in pair:
            die(f"--param must be key=value, got: {pair}")
        k, v = pair.split("=", 1)
        result[k] = v
    return result


def _watch_job(
    fetch: "callable[[], dict]",
    label: str = "job",
    terminal_states: Optional[set[str]] = None,
    poll_interval: float = 2.0,
) -> Optional[dict]:
    """Poll `fetch()` and render a live progress bar until the job reaches a
    terminal state. Works for both scan jobs (progress_pct) and tool jobs
    (progress) since it checks both field names."""
    terminal = terminal_states or {"completed", "failed", "cancelled"}
    with Progress(
        SpinnerColumn(),
        TextColumn(f"[bold cyan]{label}[/bold cyan]"),
        BarColumn(),
        TextColumn("{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task(label, total=100)
        last = None
        while True:
            data = fetch()
            pct = data.get("progress_pct", data.get("progress", 0)) or 0
            status = data.get("status", "unknown")
            progress.update(task, completed=pct, description=f"{label} — {status}")
            if status in terminal:
                last = data
                break
            time.sleep(poll_interval)

    if last:
        style = STATUS_COLOR.get(last.get("status", ""), "")
        console.print(
            f"[{style}]{label} finished: {last.get('status')}[/{style}] "
            f"[dim]({last.get('id')})[/dim]"
        )
        if last.get("status") == "failed" and last.get("error_message"):
            err_console.print(f"[red]{last['error_message']}[/red]")
    return last


if __name__ == "__main__":
    app()
