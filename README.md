# NEXUS — Unified Security Operations Platform

NEXUS is a full-stack platform for reconnaissance, vulnerability scanning, blue-team
detection, and digital forensics, with an AI assistant (Claude) layered on top to help
interpret findings, map them to MITRE ATT&CK, and draft reports. It also ships a
Typer-based CLI so the same operations can be scripted from a terminal.

> **Scope note:** this build intentionally does not include automated exploitation,
> credential-cracking, or post-exploitation/lateral-movement tooling (e.g. Metasploit
> orchestration, Hydra/Hashcat/John runners, Impacket/BloodHound/CrackMapExec
> integration, SQLMap-style automated exploitation, or Wi-Fi handshake cracking).
> Those directories exist as scaffolding (with a `NOTE.md` explaining why) and the
> frontend nav items for them show an explanatory page instead of a broken link.
> Everything else in the original spec — recon, scanning, web testing, blue team,
> forensics, AI, reporting, the frontend, database migrations, demo data, and the
> CLI — is implemented.

## Stack

- **Backend:** FastAPI, SQLAlchemy (async), Alembic, Celery + Redis, Neo4j, Anthropic SDK
- **Frontend:** Next.js 15 (App Router), TypeScript, Tailwind, shadcn/ui patterns
- **CLI:** Typer + httpx + Rich, talks to the same API as the frontend
- **Databases:** PostgreSQL 16, Redis 7, Neo4j 5
- **Infra:** Docker Compose, Nginx reverse proxy

## Layout

```
NEXUS/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── core/              # config, db, redis, neo4j, security, deps
│   ├── models/ schemas/    # SQLAlchemy models + Pydantic schemas
│   ├── routers/            # FastAPI routers (auth, targets, scans, findings, ai, ...)
│   ├── services/           # ai_engine, tool_orchestrator, report_generator, attack_graph, ...
│   ├── tools/
│   │   ├── recon/          # nmap, amass, theHarvester, shodan, whois, dnsx
│   │   ├── scanning/       # nuclei, nikto, openvas, wpscan
│   │   ├── web/             # ffuf, wfuzz, dalfox
│   │   ├── network/         # wireshark/pcap parsing
│   │   ├── blueteam/        # yara, sigma, suricata, wazuh
│   │   ├── forensics/       # volatility, autopsy, static analysis, malware yara
│   │   └── exploitation/ password/ post_exploit/ wireless/   # scaffolded, unimplemented — see NOTE.md in each
│   ├── workers/             # Celery app + tasks
│   ├── utils/               # cvss calculator, mitre mapper, parsers, logging
│   ├── alembic/versions/    # 0001_initial_schema.py — full schema, hand-authored
│   ├── scripts/seed_data.py # idempotent demo-data seeder (Typer)
│   └── Dockerfile
├── frontend/                 # Next.js app (dashboard, recon, scanner, SIEM, forensics, AI chat, attack graph, ...)
│   └── Dockerfile
├── nginx/                     # reverse proxy config + Dockerfile
├── cli/nexus_cli.py           # single-file Typer CLI mirroring the API surface
└── docs/NEXUS_MASTER_PROMPT.md  # original build spec
```

## AI features — free by default

`AI_PROVIDER` in `.env` picks the backend and defaults to **Ollama** — fully
local, $0 forever, no signup, no rate limits, nothing leaves your machine.
It's already wired up as a service in `docker-compose.yml`.

```powershell
docker compose up --build
# once the ollama container is up, pull a model (one-time, ~5GB):
docker compose exec ollama ollama pull llama3.1
```

That's it — chat, finding analysis, and target summaries all route through
it with no cost. Two other options are supported, switchable via `.env`:

| `AI_PROVIDER` | Cost | Notes |
|---|---|---|
| `ollama` (default) | Free forever | Local, needs ~5GB disk + a model pull, slower on CPU-only machines |
| `gemini` | Free tier | Hosted, no card required — get a key at aistudio.google.com/apikey, set `GEMINI_API_KEY` |
| `anthropic` | Paid | Best quality, pay-per-token — set `ANTHROPIC_API_KEY` |

## Local development

1. Copy environment files:
   ```bash
   cp .env.example .env
   cp frontend/.env.local.example frontend/.env.local
   ```
   Fill in `ANTHROPIC_API_KEY`, database passwords, and (optionally) `SHODAN_API_KEY`.

2. Start the stack (from the project root, where `docker-compose.yml` lives):
   ```bash
   docker compose up --build
   ```

3. Run database migrations, then seed demo data:
   ```bash
   docker compose exec backend alembic upgrade head
   docker compose exec backend python scripts/seed_data.py --admin-password 'YourPassword!'
   ```

4. Access:
   - Frontend: http://localhost:3000 (or http://localhost via nginx)
   - API docs: http://localhost:8000/docs
   - Flower (Celery monitor): http://localhost:5555
   - Neo4j browser: http://localhost:7474

## Manual (non-Docker) setup

Backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
python scripts/seed_data.py
uvicorn main:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

Celery worker:
```bash
cd backend
celery -A workers.celery_app worker --loglevel=info
```

CLI:
```bash
pip install typer[all] httpx rich
python cli/nexus_cli.py auth login
python cli/nexus_cli.py targets list
```

## License

MIT, with an ethical-use clause: this platform is for authorized security testing and
defense only, against systems you own or have explicit written permission to assess.
