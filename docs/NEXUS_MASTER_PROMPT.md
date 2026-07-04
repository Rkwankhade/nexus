# ╔══════════════════════════════════════════════════════════════════╗
# ║         NEXUS — AI-POWERED CYBER OPERATIONS PLATFORM            ║
# ║              MASTER BUILD SPECIFICATION v1.0                    ║
# ╚══════════════════════════════════════════════════════════════════╝

You are a senior full-stack security engineer. Build the complete NEXUS platform
exactly as specified below. Output EVERY file with FULL code — no placeholders,
no "# TODO", no "..." truncations. Build phase by phase. After each phase confirm
completion and wait for "next" before proceeding.

═══════════════════════════════════════════════════════════════
## 0. PROJECT IDENTITY
═══════════════════════════════════════════════════════════════

**Name:** NEXUS — Network EXploit & Unified Security Platform  
**Target OS:** Kali Linux (also compatible with Ubuntu 22.04+)  
**Purpose:** Full-cycle AI-powered cyber operations — recon → exploit → defend → forensics → report  
**Audience:** Penetration testers, SOC analysts, security researchers (authorized use only)  
**License:** MIT with ethical use clause  

═══════════════════════════════════════════════════════════════
## 1. TECH STACK (EXACT VERSIONS)
═══════════════════════════════════════════════════════════════

### Backend
- Python 3.11+
- FastAPI 0.111+
- Uvicorn 0.29+ (ASGI server)
- SQLAlchemy 2.0+ (async ORM)
- Alembic (migrations)
- Celery 5.3+ + Redis (task queue)
- asyncpg (PostgreSQL async driver)
- redis-py 5.0+
- python-jose (JWT)
- passlib[bcrypt] (password hashing)
- python-dotenv
- aiofiles
- websockets
- anthropic (Claude API SDK)
- neo4j (graph DB driver)
- reportlab (PDF generation)
- python-multipart
- httpx (async HTTP client)
- pydantic 2.0+
- typer (CLI)
- rich (terminal output)

### Frontend
- Next.js 15 (App Router)
- TypeScript 5+
- Tailwind CSS 3.4+
- shadcn/ui (latest)
- lucide-react
- recharts (graphs/charts)
- react-flow (attack graph visualizer)
- xterm.js (embedded terminal)
- socket.io-client
- axios
- zustand (state management)
- @tanstack/react-query
- next-auth v5

### Databases
- PostgreSQL 16 (primary)
- Redis 7 (cache + task queue + pub/sub)
- Neo4j 5 (attack graph)

### Infrastructure
- Docker + Docker Compose
- Nginx (reverse proxy)

### AI
- Anthropic Claude claude-sonnet-4-6 via official SDK

═══════════════════════════════════════════════════════════════
## 2. COMPLETE DIRECTORY STRUCTURE
═══════════════════════════════════════════════════════════════

Create EXACTLY this structure:

```
nexus/
├── .env.example
├── .gitignore
├── docker-compose.yml
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── main.py                          # FastAPI app entry point
│   │
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/                    # migration files go here
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                    # settings from .env
│   │   ├── database.py                  # async SQLAlchemy engine
│   │   ├── redis_client.py              # Redis connection
│   │   ├── neo4j_client.py              # Neo4j connection
│   │   ├── security.py                  # JWT, password hashing
│   │   └── dependencies.py              # FastAPI dependency injection
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── scan.py
│   │   ├── target.py
│   │   ├── finding.py
│   │   ├── exploit.py
│   │   ├── log_entry.py
│   │   ├── report.py
│   │   ├── tool_job.py
│   │   └── alert.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── scan.py
│   │   ├── target.py
│   │   ├── finding.py
│   │   ├── exploit.py
│   │   ├── report.py
│   │   ├── tool_job.py
│   │   └── alert.py
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py                      # /api/auth/*
│   │   ├── users.py                     # /api/users/*
│   │   ├── targets.py                   # /api/targets/*
│   │   ├── scans.py                     # /api/scans/*
│   │   ├── findings.py                  # /api/findings/*
│   │   ├── exploits.py                  # /api/exploits/*
│   │   ├── ai.py                        # /api/ai/*
│   │   ├── reports.py                   # /api/reports/*
│   │   ├── alerts.py                    # /api/alerts/*
│   │   ├── forensics.py                 # /api/forensics/*
│   │   ├── blueteam.py                  # /api/blueteam/*
│   │   ├── wireless.py                  # /api/wireless/*
│   │   └── websocket.py                 # /ws/*
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_engine.py                 # Claude API integration (core AI)
│   │   ├── tool_orchestrator.py         # Runs all tools via subprocess/API
│   │   ├── report_generator.py          # PDF report builder
│   │   ├── attack_graph.py              # Neo4j attack path builder
│   │   ├── log_ingestor.py              # SIEM log ingestion
│   │   └── notification_service.py      # WebSocket push notifications
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   │
│   │   ├── recon/
│   │   │   ├── __init__.py
│   │   │   ├── nmap_runner.py
│   │   │   ├── amass_runner.py
│   │   │   ├── theharvester_runner.py
│   │   │   ├── shodan_client.py
│   │   │   ├── whois_runner.py
│   │   │   └── dnsx_runner.py
│   │   │
│   │   ├── scanning/
│   │   │   ├── __init__.py
│   │   │   ├── nuclei_runner.py
│   │   │   ├── nikto_runner.py
│   │   │   ├── openvas_client.py
│   │   │   └── wpscan_runner.py
│   │   │
│   │   ├── web/
│   │   │   ├── __init__.py
│   │   │   ├── sqlmap_runner.py
│   │   │   ├── ffuf_runner.py
│   │   │   ├── dalfox_runner.py
│   │   │   └── wfuzz_runner.py
│   │   │
│   │   ├── exploitation/
│   │   │   ├── __init__.py
│   │   │   ├── metasploit_client.py     # XMLRPC client
│   │   │   ├── searchsploit_runner.py
│   │   │   └── exploit_suggester.py
│   │   │
│   │   ├── password/
│   │   │   ├── __init__.py
│   │   │   ├── hashcat_runner.py
│   │   │   ├── hydra_runner.py
│   │   │   ├── john_runner.py
│   │   │   └── wordlist_generator.py
│   │   │
│   │   ├── post_exploit/
│   │   │   ├── __init__.py
│   │   │   ├── impacket_runner.py
│   │   │   ├── bloodhound_parser.py
│   │   │   └── crackmapexec_runner.py
│   │   │
│   │   ├── network/
│   │   │   ├── __init__.py
│   │   │   ├── wireshark_parser.py      # Parse PCAP files
│   │   │   ├── bettercap_client.py
│   │   │   └── scapy_engine.py
│   │   │
│   │   ├── wireless/
│   │   │   ├── __init__.py
│   │   │   ├── aircrack_runner.py
│   │   │   └── wifite_runner.py
│   │   │
│   │   ├── blueteam/
│   │   │   ├── __init__.py
│   │   │   ├── suricata_manager.py
│   │   │   ├── yara_scanner.py
│   │   │   ├── sigma_engine.py
│   │   │   └── wazuh_client.py
│   │   │
│   │   └── forensics/
│   │       ├── __init__.py
│   │       ├── volatility_runner.py
│   │       ├── autopsy_client.py
│   │       ├── pcap_analyzer.py
│   │       ├── static_analyzer.py       # strings, PE analysis
│   │       └── yara_malware_scanner.py
│   │
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── celery_app.py               # Celery configuration
│   │   ├── scan_tasks.py               # Background scan jobs
│   │   ├── exploit_tasks.py            # Background exploit jobs
│   │   ├── ai_tasks.py                 # Background AI analysis jobs
│   │   └── report_tasks.py             # Background report generation
│   │
│   └── utils/
│       ├── __init__.py
│       ├── parser_utils.py             # Common output parsers
│       ├── xml_parser.py               # Nmap XML parser
│       ├── cvss_calculator.py          # CVSS score helper
│       ├── mitre_mapper.py             # Map findings to ATT&CK
│       └── logger.py                   # Structured logging
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   ├── .env.local.example
│   │
│   ├── app/
│   │   ├── layout.tsx                  # Root layout
│   │   ├── page.tsx                    # Landing / redirect
│   │   ├── globals.css
│   │   │
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   │
│   │   └── (dashboard)/
│   │       ├── layout.tsx              # Dashboard shell with sidebar
│   │       ├── dashboard/page.tsx      # Main overview
│   │       ├── targets/
│   │       │   ├── page.tsx            # Target list
│   │       │   └── [id]/page.tsx       # Target detail
│   │       ├── recon/page.tsx          # Recon module
│   │       ├── scanner/page.tsx        # Vuln scanner
│   │       ├── web-attacks/page.tsx    # Web attack module
│   │       ├── exploitation/page.tsx   # Exploit engine
│   │       ├── post-exploit/page.tsx   # Post-exploitation
│   │       ├── passwords/page.tsx      # Password attacks
│   │       ├── wireless/page.tsx       # Wireless attacks
│   │       ├── blueteam/
│   │       │   ├── page.tsx            # Blue team overview
│   │       │   ├── siem/page.tsx       # SIEM log viewer
│   │       │   ├── alerts/page.tsx     # Alert dashboard
│   │       │   └── rules/page.tsx      # Detection rules
│   │       ├── forensics/
│   │       │   ├── page.tsx            # Forensics overview
│   │       │   ├── memory/page.tsx     # Memory analysis
│   │       │   ├── disk/page.tsx       # Disk forensics
│   │       │   └── malware/page.tsx    # Malware analysis
│   │       ├── ai-assistant/page.tsx   # AI chat + analysis
│   │       ├── attack-graph/page.tsx   # Neo4j visual attack paths
│   │       ├── reports/
│   │       │   ├── page.tsx            # Report list
│   │       │   └── [id]/page.tsx       # Report viewer
│   │       ├── findings/page.tsx       # All findings
│   │       └── settings/page.tsx       # Platform settings
│   │
│   ├── components/
│   │   ├── ui/                         # shadcn components (auto-generated)
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── TopBar.tsx
│   │   │   ├── MobileSidebar.tsx
│   │   │   └── ThemeToggle.tsx
│   │   ├── dashboard/
│   │   │   ├── StatsGrid.tsx
│   │   │   ├── ActivityFeed.tsx
│   │   │   ├── ThreatMap.tsx
│   │   │   ├── RiskScore.tsx
│   │   │   └── RecentFindings.tsx
│   │   ├── tools/
│   │   │   ├── ToolCard.tsx
│   │   │   ├── ToolLauncher.tsx
│   │   │   ├── JobStatus.tsx
│   │   │   └── OutputTerminal.tsx      # xterm.js wrapper
│   │   ├── ai/
│   │   │   ├── AIChat.tsx
│   │   │   ├── AIAnalysisPanel.tsx
│   │   │   ├── MITREMapper.tsx
│   │   │   └── KillChainView.tsx
│   │   ├── findings/
│   │   │   ├── FindingCard.tsx
│   │   │   ├── FindingDetail.tsx
│   │   │   ├── CVSSBadge.tsx
│   │   │   └── FindingFilters.tsx
│   │   ├── charts/
│   │   │   ├── SeverityPieChart.tsx
│   │   │   ├── TimelineChart.tsx
│   │   │   ├── AttackSurface.tsx
│   │   │   └── LogVolumeChart.tsx
│   │   ├── attack-graph/
│   │   │   ├── GraphCanvas.tsx         # react-flow canvas
│   │   │   ├── NodeTypes.tsx
│   │   │   └── EdgeTypes.tsx
│   │   └── reports/
│   │       ├── ReportBuilder.tsx
│   │       └── ReportPreview.tsx
│   │
│   ├── lib/
│   │   ├── api.ts                      # axios instance + interceptors
│   │   ├── auth.ts                     # next-auth config
│   │   ├── socket.ts                   # socket.io client
│   │   ├── utils.ts                    # cn(), formatters, etc.
│   │   └── constants.ts                # MITRE tactics, severity levels
│   │
│   ├── store/
│   │   ├── useAuthStore.ts
│   │   ├── useScanStore.ts
│   │   ├── useAlertStore.ts
│   │   └── useTerminalStore.ts
│   │
│   └── types/
│       ├── api.ts                      # API response types
│       ├── scan.ts
│       ├── finding.ts
│       ├── tool.ts
│       └── ai.ts
│
└── nginx/
    ├── nginx.conf
    └── Dockerfile
```

═══════════════════════════════════════════════════════════════
## 3. DATABASE SCHEMAS (PostgreSQL)
═══════════════════════════════════════════════════════════════

### users
```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
email VARCHAR(255) UNIQUE NOT NULL
username VARCHAR(100) UNIQUE NOT NULL
hashed_password VARCHAR(255) NOT NULL
role VARCHAR(50) NOT NULL DEFAULT 'analyst'  -- admin | analyst | readonly
is_active BOOLEAN DEFAULT true
created_at TIMESTAMP DEFAULT now()
updated_at TIMESTAMP DEFAULT now()
last_login TIMESTAMP
api_key VARCHAR(255) UNIQUE  -- for API access
```

### targets
```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
name VARCHAR(255) NOT NULL
type VARCHAR(50) NOT NULL  -- ip | domain | network | webapp | wireless
value VARCHAR(500) NOT NULL  -- IP/domain/CIDR/URL
description TEXT
scope TEXT  -- authorized scope notes
tags JSONB DEFAULT '[]'
status VARCHAR(50) DEFAULT 'active'
created_by UUID REFERENCES users(id)
created_at TIMESTAMP DEFAULT now()
updated_at TIMESTAMP DEFAULT now()
```

### tool_jobs
```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
target_id UUID REFERENCES targets(id)
tool_name VARCHAR(100) NOT NULL
module VARCHAR(100)  -- submodule (e.g. 'port_scan', 'service_detect')
command TEXT  -- exact command executed
status VARCHAR(50) DEFAULT 'pending'  -- pending | running | done | failed
raw_output TEXT
parsed_output JSONB
error_message TEXT
started_at TIMESTAMP
completed_at TIMESTAMP
duration_seconds INTEGER
created_by UUID REFERENCES users(id)
created_at TIMESTAMP DEFAULT now()
celery_task_id VARCHAR(255)
```

### findings
```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
target_id UUID REFERENCES targets(id)
tool_job_id UUID REFERENCES tool_jobs(id)
title VARCHAR(500) NOT NULL
description TEXT
severity VARCHAR(20) NOT NULL  -- critical | high | medium | low | info
cvss_score FLOAT
cvss_vector VARCHAR(100)
cve_ids JSONB DEFAULT '[]'
cwe_ids JSONB DEFAULT '[]'
mitre_techniques JSONB DEFAULT '[]'  -- ATT&CK technique IDs
affected_component VARCHAR(500)
port INTEGER
protocol VARCHAR(20)
proof_of_concept TEXT
remediation TEXT
ai_analysis TEXT  -- Claude's analysis
ai_remediation TEXT  -- Claude's remediation advice
false_positive BOOLEAN DEFAULT false
verified BOOLEAN DEFAULT false
status VARCHAR(50) DEFAULT 'open'  -- open | in_progress | resolved | accepted
created_at TIMESTAMP DEFAULT now()
updated_at TIMESTAMP DEFAULT now()
```

### reports
```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
title VARCHAR(500) NOT NULL
target_ids JSONB DEFAULT '[]'
finding_ids JSONB DEFAULT '[]'
executive_summary TEXT
technical_summary TEXT
methodology TEXT
scope TEXT
ai_generated_narrative TEXT
risk_rating VARCHAR(20)
pdf_path VARCHAR(500)
status VARCHAR(50) DEFAULT 'draft'  -- draft | generating | complete
template VARCHAR(100) DEFAULT 'professional'
created_by UUID REFERENCES users(id)
created_at TIMESTAMP DEFAULT now()
updated_at TIMESTAMP DEFAULT now()
```

### log_entries  (SIEM)
```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
source VARCHAR(100)  -- syslog | wazuh | suricata | snort | manual
source_ip VARCHAR(50)
dest_ip VARCHAR(50)
source_port INTEGER
dest_port INTEGER
protocol VARCHAR(20)
severity VARCHAR(20)
category VARCHAR(100)  -- intrusion | malware | policy | anomaly
message TEXT NOT NULL
raw_log TEXT
parsed_fields JSONB
rule_id VARCHAR(100)
rule_name VARCHAR(255)
mitre_technique VARCHAR(50)
alert_generated BOOLEAN DEFAULT false
created_at TIMESTAMP DEFAULT now()
```

### alerts
```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
log_entry_id UUID REFERENCES log_entries(id)
title VARCHAR(500) NOT NULL
description TEXT
severity VARCHAR(20) NOT NULL
status VARCHAR(50) DEFAULT 'open'  -- open | investigating | resolved | fp
assigned_to UUID REFERENCES users(id)
ai_triage TEXT  -- Claude's triage analysis
ioc_data JSONB DEFAULT '[]'
created_at TIMESTAMP DEFAULT now()
updated_at TIMESTAMP DEFAULT now()
```

### yara_rules
```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
name VARCHAR(255) NOT NULL
description TEXT
rule_text TEXT NOT NULL
tags JSONB DEFAULT '[]'
ai_generated BOOLEAN DEFAULT false
source VARCHAR(100)
enabled BOOLEAN DEFAULT true
match_count INTEGER DEFAULT 0
created_by UUID REFERENCES users(id)
created_at TIMESTAMP DEFAULT now()
```

### sigma_rules
```sql
id UUID PRIMARY KEY DEFAULT gen_random_uuid()
title VARCHAR(255) NOT NULL
description TEXT
rule_yaml TEXT NOT NULL
status VARCHAR(50) DEFAULT 'experimental'
level VARCHAR(20)
tags JSONB DEFAULT '[]'
ai_generated BOOLEAN DEFAULT false
enabled BOOLEAN DEFAULT true
created_at TIMESTAMP DEFAULT now()
```

═══════════════════════════════════════════════════════════════
## 4. ENVIRONMENT VARIABLES (.env.example)
═══════════════════════════════════════════════════════════════

```env
# === Application ===
APP_NAME=NEXUS
APP_ENV=development
SECRET_KEY=change-this-to-a-long-random-string-minimum-32-chars
DEBUG=true

# === Database ===
DATABASE_URL=postgresql+asyncpg://nexus:nexus_password@localhost:5432/nexus_db
DATABASE_URL_SYNC=postgresql://nexus:nexus_password@localhost:5432/nexus_db

# === Redis ===
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# === Neo4j ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=nexus_neo4j_password

# === AI ===
ANTHROPIC_API_KEY=your-anthropic-api-key-here
AI_MODEL=claude-sonnet-4-6
AI_MAX_TOKENS=4096

# === External APIs ===
SHODAN_API_KEY=your-shodan-api-key
VIRUSTOTAL_API_KEY=your-virustotal-api-key
NVD_API_KEY=your-nvd-api-key

# === Metasploit ===
MSF_RPC_HOST=127.0.0.1
MSF_RPC_PORT=55553
MSF_RPC_USER=msf
MSF_RPC_PASS=msf_password

# === JWT ===
JWT_SECRET_KEY=change-this-jwt-secret-minimum-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# === File Storage ===
UPLOAD_DIR=/tmp/nexus/uploads
REPORT_DIR=/tmp/nexus/reports
PCAP_DIR=/tmp/nexus/pcaps
WORDLIST_DIR=/usr/share/wordlists

# === Tool Paths (auto-detected if in PATH) ===
NMAP_PATH=/usr/bin/nmap
NIKTO_PATH=/usr/bin/nikto
HYDRA_PATH=/usr/bin/hydra
HASHCAT_PATH=/usr/bin/hashcat
SQLMAP_PATH=/usr/bin/sqlmap
FFUF_PATH=/usr/bin/ffuf
NUCLEI_PATH=/usr/bin/nuclei
AIRCRACK_PATH=/usr/bin/aircrack-ng
VOLATILITY_PATH=/usr/bin/vol
YARA_PATH=/usr/bin/yara

# === Frontend (Next.js) ===
NEXTAUTH_SECRET=change-this-nextauth-secret
NEXTAUTH_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

═══════════════════════════════════════════════════════════════
## 5. BACKEND — CORE FILES
═══════════════════════════════════════════════════════════════

### backend/main.py
FastAPI app with:
- CORS middleware (allow origins from .env)
- Include ALL routers with prefix /api
- WebSocket router at /ws
- Lifespan event: connect DB, Redis, Neo4j on startup; close on shutdown
- Global exception handlers (404, 500, validation errors)
- Static file mount for /uploads
- OpenAPI docs at /docs and /redoc
- Health check at GET /health returning {status, version, timestamp, db, redis}

### backend/core/config.py
Pydantic BaseSettings class reading all .env values.
Include: app_name, secret_key, database_url, redis_url, neo4j_uri,
anthropic_api_key, ai_model, shodan_api_key, jwt settings, file paths,
tool paths, msf rpc settings. Singleton `get_settings()` with lru_cache.

### backend/core/database.py
- Async SQLAlchemy engine with asyncpg
- AsyncSession factory
- Base declarative model with created_at/updated_at mixins
- `get_db()` async dependency yielding sessions
- `init_db()` function creating all tables

### backend/core/redis_client.py
- Redis connection pool (asyncio)
- `get_redis()` dependency
- Helper methods: `publish_event(channel, data)`, `get_cache(key)`,
  `set_cache(key, value, ttl)`, `delete_cache(key)`

### backend/core/neo4j_client.py
- Neo4j async driver
- `get_neo4j()` dependency
- Helper: `run_query(cypher, params)` returning list of records

### backend/core/security.py
- `hash_password(password)` → bcrypt hash
- `verify_password(plain, hashed)` → bool
- `create_access_token(data, expires_delta)` → JWT string
- `create_refresh_token(data)` → JWT string
- `decode_token(token)` → payload dict or raise HTTPException 401
- `generate_api_key()` → secure random 32-char hex string

### backend/core/dependencies.py
- `get_current_user(token, db)` → User model (validates JWT)
- `require_admin(current_user)` → User or raise 403
- `require_analyst(current_user)` → User or raise 403
- `get_pagination(skip, limit)` → tuple

═══════════════════════════════════════════════════════════════
## 6. ALL API ENDPOINTS
═══════════════════════════════════════════════════════════════

### AUTH  /api/auth/
- POST /register         → create user, return tokens
- POST /login            → email+password, return {access_token, refresh_token, user}
- POST /refresh          → refresh_token → new access_token
- POST /logout           → invalidate refresh token in Redis
- GET  /me               → current user profile
- PUT  /me               → update profile
- POST /me/change-password → old+new password

### USERS  /api/users/  (admin only)
- GET    /               → list users (paginated)
- GET    /{id}           → get user
- PUT    /{id}           → update user
- DELETE /{id}           → soft delete
- POST   /{id}/reset-password

### TARGETS  /api/targets/
- GET    /               → list targets (filter by type, status)
- POST   /               → create target
- GET    /{id}           → get target + all jobs + findings summary
- PUT    /{id}           → update target
- DELETE /{id}           → delete target + cascade
- GET    /{id}/findings  → all findings for target
- GET    /{id}/jobs      → all tool jobs for target
- GET    /{id}/timeline  → chronological activity

### SCANS  /api/scans/
- POST /recon/nmap              body: {target_id, ports, scan_type, options}
- POST /recon/amass             body: {target_id, domain, mode}
- POST /recon/theharvester      body: {target_id, domain, sources}
- POST /recon/shodan            body: {target_id, query}
- POST /recon/whois             body: {target_id, domain}
- POST /scanning/nuclei         body: {target_id, templates, severity}
- POST /scanning/nikto          body: {target_id, url, options}
- POST /scanning/wpscan         body: {target_id, url, options}
- POST /web/sqlmap              body: {target_id, url, params, technique}
- POST /web/ffuf                body: {target_id, url, wordlist, extensions}
- POST /web/dalfox              body: {target_id, url, options}
- POST /passwords/hashcat       body: {target_id, hash_file, hash_type, wordlist}
- POST /passwords/hydra         body: {target_id, service, host, wordlist}
- POST /wireless/aircrack       body: {target_id, capture_file}
- GET  /jobs                    → list all jobs (filter: status, tool, target)
- GET  /jobs/{id}               → get job detail + output
- DELETE /jobs/{id}             → cancel/delete job

### EXPLOITATION  /api/exploits/
- POST /search              body: {query, platform, type} → searchsploit results
- POST /suggest             body: {target_id, service, version} → AI suggested modules
- POST /metasploit/modules  body: {search} → list msf modules
- POST /metasploit/run      body: {module, options, target_id} → run module
- GET  /metasploit/sessions → active sessions
- POST /metasploit/session/command body: {session_id, command}
- POST /post-exploit/bloodhound body: {target_id, zip_file}
- POST /post-exploit/impacket body: {target_id, tool, options}

### FINDINGS  /api/findings/
- GET    /               → list (filter: severity, status, target, tool, mitre)
- GET    /{id}           → finding detail
- PUT    /{id}           → update (status, false_positive, verified)
- DELETE /{id}           → delete
- POST   /{id}/analyze   → trigger AI analysis of this finding
- GET    /stats          → count by severity, by target, by date
- POST   /bulk-update    → update multiple findings at once

### AI  /api/ai/
- POST /analyze/output       body: {tool_name, raw_output, target_id} → AI analysis
- POST /analyze/finding      body: {finding_id} → AI finding deep-dive
- POST /analyze/pcap         body: {file_path} → AI network traffic analysis
- POST /generate/report      body: {target_ids, finding_ids} → AI report narrative
- POST /generate/yara        body: {sample_description, iocs} → generate YARA rule
- POST /generate/sigma       body: {attack_description, log_source} → generate Sigma rule
- POST /generate/suricata    body: {attack_description} → generate Suricata rule
- POST /generate/wordlist    body: {target_info, osint_data} → custom wordlist
- POST /attack-path          body: {target_id} → AI kill chain from findings
- POST /mitre-map            body: {finding_ids} → map to ATT&CK matrix
- POST /remediation-plan     body: {finding_ids} → prioritized remediation
- POST /threat-hunt          body: {hypothesis, log_source} → hunt queries
- POST /chat                 body: {messages: [{role, content}], context} → streaming chat

### REPORTS  /api/reports/
- GET    /               → list reports
- POST   /               → create report (triggers background PDF generation)
- GET    /{id}           → get report
- GET    /{id}/download  → stream PDF file
- PUT    /{id}           → update report metadata
- DELETE /{id}           → delete report
- POST   /{id}/regenerate → re-run AI narrative + rebuild PDF

### BLUE TEAM  /api/blueteam/
- POST /logs/ingest         body: {source, logs: []} → ingest log batch
- POST /logs/upload         multipart: file (syslog, JSON, CSV)
- GET  /logs                → paginated log entries (filter: source, severity, date)
- GET  /logs/{id}           → log entry detail
- GET  /alerts              → paginated alerts (filter: severity, status)
- GET  /alerts/{id}         → alert detail
- PUT  /alerts/{id}         → update alert (status, assignee)
- POST /alerts/{id}/triage  → AI triage this alert
- GET  /rules/yara          → list YARA rules
- POST /rules/yara          → create YARA rule
- PUT  /rules/yara/{id}     → update YARA rule
- POST /rules/yara/scan     body: {file_path, rule_ids} → scan file with YARA
- GET  /rules/sigma         → list Sigma rules
- POST /rules/sigma         → create Sigma rule
- POST /suricata/reload     → reload Suricata rules
- GET  /stats               → alert counts, log volume, detection rate

### FORENSICS  /api/forensics/
- POST /memory/analyze      multipart: memory_dump → Volatility analysis
- POST /memory/plugins      body: {dump_file, plugin, args} → run specific plugin
- POST /disk/analyze        multipart: disk_image → Autopsy analysis
- POST /static/analyze      multipart: binary_file → PE + strings + YARA
- POST /pcap/analyze        multipart: pcap_file → network forensics
- POST /malware/scan        multipart: file → YARA + hashes + VT lookup
- GET  /jobs                → forensics job list
- GET  /jobs/{id}           → forensics job result

### WEBSOCKET  /ws/
- /ws/terminal/{session_id}        → bidirectional shell/tool output
- /ws/scan-progress/{job_id}       → real-time scan progress
- /ws/alerts                       → live alert stream
- /ws/logs                         → live log stream
- /ws/ai-stream                    → streaming Claude responses

═══════════════════════════════════════════════════════════════
## 7. AI ENGINE — backend/services/ai_engine.py
═══════════════════════════════════════════════════════════════

Use the official `anthropic` Python SDK. Model: claude-sonnet-4-6.

Implement these async methods in class `AIEngine`:

```python
class AIEngine:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    async def analyze_tool_output(self, tool_name: str, raw_output: str,
                                   target: dict) -> dict:
        """Analyze raw tool output and return structured findings"""
        # Returns: {summary, findings[], attack_vectors[], mitre_techniques[],
        #           risk_level, recommendations[]}

    async def analyze_finding(self, finding: dict) -> dict:
        """Deep-dive analysis of a single vulnerability finding"""
        # Returns: {explanation, impact, exploit_likelihood, remediation_steps[],
        #           references[], mitre_mapping, priority_score}

    async def generate_kill_chain(self, target: dict, findings: list) -> dict:
        """Build attack kill chain from recon + vulnerability data"""
        # Returns: {phases[], attack_path[], tools_to_use[], mitre_chain[]}

    async def generate_report_narrative(self, target: dict, findings: list,
                                         scope: str) -> dict:
        """Generate complete report narrative sections"""
        # Returns: {executive_summary, technical_summary, risk_rating,
        #           findings_narrative, methodology, recommendations}

    async def generate_yara_rule(self, description: str, iocs: list) -> str:
        """Generate a YARA rule from description and IOCs"""

    async def generate_sigma_rule(self, attack_desc: str,
                                   log_source: str) -> str:
        """Generate a Sigma detection rule"""

    async def generate_suricata_rule(self, attack_desc: str) -> str:
        """Generate a Suricata IDS rule"""

    async def generate_hunt_queries(self, hypothesis: str,
                                     log_source: str) -> dict:
        """Generate threat hunting queries"""
        # Returns: {splunk_query, elastic_query, sigma_rule, description}

    async def triage_alert(self, alert: dict, recent_logs: list) -> dict:
        """AI triage of a security alert"""
        # Returns: {verdict, confidence, reasoning, recommended_action,
        #           related_iocs[], severity_override}

    async def analyze_pcap(self, connections: list, protocols: list,
                            anomalies: list) -> dict:
        """Analyze network traffic data"""
        # Returns: {summary, suspicious_flows[], iocs[], attack_indicators[]}

    async def generate_wordlist(self, target_info: dict,
                                 osint_data: dict) -> list:
        """Generate targeted wordlist from OSINT"""

    async def chat_stream(self, messages: list, context: str):
        """Streaming chat with security context — async generator"""
        # Use anthropic streaming API, yield text chunks

    async def map_to_mitre(self, findings: list) -> dict:
        """Map findings to MITRE ATT&CK framework"""
        # Returns: {tactics, techniques, subtechniques, coverage_percentage}

    async def remediation_plan(self, findings: list,
                                business_context: str) -> dict:
        """Prioritized remediation roadmap"""
        # Returns: {immediate[], short_term[], long_term[], estimated_effort}

    async def analyze_binary(self, strings_output: str, imports: list,
                              entropy: float, file_info: dict) -> dict:
        """Static malware analysis"""
        # Returns: {verdict, family_guess, capabilities[], iocs[], 
        #           behavior_prediction, yara_rule_suggestion}
```

Each method must:
1. Build a detailed system prompt establishing security expert persona
2. Build user prompt with structured data as JSON context
3. Call `self.client.messages.create()`
4. Parse response (JSON where structured data expected)
5. Return typed dict
6. Handle API errors with graceful fallback

═══════════════════════════════════════════════════════════════
## 8. TOOL ORCHESTRATOR — backend/services/tool_orchestrator.py
═══════════════════════════════════════════════════════════════

Class `ToolOrchestrator`:
- All tool runs are async using `asyncio.create_subprocess_exec`
- Stream stdout/stderr in real-time via Redis pub/sub to WebSocket
- Save raw output and parsed results to `tool_jobs` table
- Return `job_id` immediately; actual work happens in Celery task
- Each tool method:
  1. Creates `ToolJob` record in DB with status='running'
  2. Publishes progress events to Redis channel `scan:{job_id}`
  3. Runs tool subprocess with timeout (configurable per tool)
  4. Captures stdout/stderr line by line, publishes each line
  5. On completion: calls appropriate parser, saves parsed_output
  6. Triggers AI analysis via `ai_engine.analyze_tool_output()`
  7. Creates `Finding` records from AI-identified vulnerabilities
  8. Updates job status to 'done' or 'failed'
  9. Publishes completion event

Implement run methods for every tool:
`run_nmap`, `run_amass`, `run_theharvester`, `run_shodan`,
`run_nikto`, `run_nuclei`, `run_wpscan`, `run_sqlmap`, `run_ffuf`,
`run_dalfox`, `run_hashcat`, `run_hydra`, `run_aircrack`, `run_wifite`,
`run_searchsploit`, `run_volatility`, `run_yara`

═══════════════════════════════════════════════════════════════
## 9. TOOL IMPLEMENTATIONS (backend/tools/)
═══════════════════════════════════════════════════════════════

### recon/nmap_runner.py
Class `NmapRunner`:
- `async run_port_scan(target, ports="1-65535", flags="-sV -sC")` → raw XML output
- `async run_os_detection(target)` → raw output  
- `async run_vuln_scan(target)` → raw output using --script vuln
- `async run_ping_sweep(network)` → list of alive hosts
- `parse_xml_output(xml_str)` → dict with {hosts[], open_ports[], services[], os_guess}
- Command: `nmap -oX - {flags} {target} -p {ports}`

### recon/amass_runner.py
Class `AmassRunner`:
- `async run_enum(domain, mode="passive")` → subdomains list
- `async run_intel(domain)` → org/ASN/CIDR data
- Parse output lines to extract subdomain list

### recon/theharvester_runner.py
Class `TheHarvesterRunner`:
- `async run(domain, sources="all", limit=500)` → {emails[], hosts[], ips[]}
- Parse XML output format

### recon/shodan_client.py
Class `ShodanClient`:
- Uses `shodan` Python library (pip install shodan)
- `async search(query, limit=100)` → {results[], total}
- `async host_info(ip)` → full host details
- `async search_exploits(cve)` → exploit list

### scanning/nuclei_runner.py
Class `NucleiRunner`:
- `async run(target, templates=None, severity="medium,high,critical")` → findings[]
- `async update_templates()` → run `nuclei -update-templates`
- Parse JSONL output format
- Each finding: {template_id, name, severity, matched_at, description, reference}

### scanning/nikto_runner.py
Class `NiktoRunner`:
- `async run(url, options="")` → findings[]
- Parse CSV/JSON output
- Extract: {id, method, uri, description, osvdb}

### web/sqlmap_runner.py
Class `SQLmapRunner`:
- `async run(url, params=None, technique="BEUSTQ", level=2, risk=2)` → results
- `async run_from_request(request_file)` → results
- Parse output for: {injectable_params[], dbms, payloads_used[]}

### web/ffuf_runner.py
Class `FfufRunner`:
- `async run(url, wordlist, extensions=".php,.html,.txt", status_codes="200,301,302,403")` → results[]
- Parse JSON output
- Returns: {url, status, length, words, lines}[]

### exploitation/metasploit_client.py
Class `MetasploitClient`:
- Uses `python-msfrpc` or direct XMLRPC calls via httpx
- `async login()` → auth token
- `async search_modules(query)` → module list
- `async run_module(module_path, options)` → job_id
- `async get_sessions()` → active sessions dict
- `async session_command(session_id, cmd)` → output
- `async module_info(module_path)` → module details

### exploitation/searchsploit_runner.py
Class `SearchsploitRunner`:
- `async search(query, type=None)` → results[]
- `async get_path(exploit_id)` → local file path
- Parse JSON output (-j flag)
- Returns: {title, edb_id, path, type, platform, date}[]

### password/hashcat_runner.py
Class `HashcatRunner`:
- `async crack(hash_file, hash_type, wordlist, rules=None)` → cracked[]
- `async benchmark(hash_type)` → speed stats
- `async identify_hash(hash_string)` → possible types[]
- Monitor .pot file for results in real-time

### password/hydra_runner.py
Class `HydraRunner`:
- `async attack(host, service, userlist, passlist, port=None, options="")` → cracked[]
- Services: ssh, ftp, http-post-form, rdp, smb, mysql, postgres, telnet
- Parse output for found credentials

### blueteam/yara_scanner.py
Class `YaraScanner`:
- `async scan_file(file_path, rules_dir)` → matches[]
- `async scan_directory(dir_path, rules_dir)` → {file: matches[]}
- `compile_rules(rules_dir)` → compiled ruleset
- Match: {rule, namespace, tags[], strings[], meta{}}

### blueteam/sigma_engine.py
Class `SigmaEngine`:
- `parse_rule(yaml_str)` → rule dict
- `convert_to_splunk(rule)` → SPL query
- `convert_to_elastic(rule)` → ES query DSL
- `convert_to_suricata(rule)` → Suricata rule (if applicable)
- `evaluate_log(rule, log_entry)` → bool

### forensics/volatility_runner.py
Class `VolatilityRunner`:
- `async run_plugin(memory_dump, plugin, args="")` → raw output
- `async analyze_full(memory_dump)` → comprehensive analysis running:
  windows.pslist, windows.cmdline, windows.dlllist, windows.netscan,
  windows.malfind, windows.svcscan, windows.handles
- Parse each plugin output into structured dicts
- Returns: {processes[], connections[], injections[], services[], handles[]}

### forensics/static_analyzer.py
Class `StaticAnalyzer`:
- `async analyze(file_path)` → full analysis
- `run_strings(file_path)` → interesting strings[]
- `get_file_hashes(file_path)` → {md5, sha1, sha256}
- `check_pe_headers(file_path)` → {is_pe, imports[], exports[], sections[], entropy}
- `run_yara(file_path)` → matches[]
- `lookup_virustotal(sha256)` → VT result (if API key set)

═══════════════════════════════════════════════════════════════
## 10. CELERY WORKERS — backend/workers/
═══════════════════════════════════════════════════════════════

### celery_app.py
```python
from celery import Celery
from core.config import get_settings

settings = get_settings()
celery_app = Celery(
    "nexus",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["workers.scan_tasks", "workers.exploit_tasks",
             "workers.ai_tasks", "workers.report_tasks"]
)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.timezone = "UTC"
```

### scan_tasks.py
- `@celery_app.task` `run_nmap_task(target_id, options, job_id, user_id)`
- `@celery_app.task` `run_nuclei_task(target_id, options, job_id, user_id)`
- `@celery_app.task` `run_nikto_task(target_id, url, options, job_id, user_id)`
- `@celery_app.task` `run_sqlmap_task(target_id, url, options, job_id, user_id)`
- `@celery_app.task` `run_hydra_task(target_id, options, job_id, user_id)`
- Each task: updates DB, runs tool, parses, saves findings, triggers AI

### ai_tasks.py
- `@celery_app.task` `analyze_output_task(job_id, tool_name, raw_output)`
- `@celery_app.task` `generate_report_task(report_id)`
- `@celery_app.task` `triage_alert_task(alert_id)`

### report_tasks.py
- `@celery_app.task` `generate_pdf_report(report_id)`
  → fetches report from DB, calls ai_engine.generate_report_narrative(),
  calls report_generator.build_pdf(), saves PDF to disk, updates report.pdf_path

═══════════════════════════════════════════════════════════════
## 11. REPORT GENERATOR — backend/services/report_generator.py
═══════════════════════════════════════════════════════════════

Class `ReportGenerator` using ReportLab:

`async build_pdf(report_data: dict) → str (file path)`:

PDF must include:
- Cover page: Platform logo (text-based), report title, target, date, classification
- Table of Contents (auto-generated)
- Section 1: Executive Summary (AI narrative, risk rating meter graphic)
- Section 2: Scope and Methodology
- Section 3: Attack Surface (host/port/service table from Nmap)
- Section 4: Findings (one subsection per severity: Critical → High → Medium → Low)
  - Each finding: title, CVSS score, description, affected component, 
    proof of concept, screenshots (if any), remediation steps
- Section 5: MITRE ATT&CK Coverage Matrix (text-based heat map)
- Section 6: Remediation Roadmap (prioritized table)
- Section 7: Technical Appendix (raw tool outputs, command list)

Styling:
- Dark professional theme: #0f172a background style or white with dark headers
- Severity color coding: Critical=#dc2626, High=#ea580c, Medium=#d97706, Low=#16a34a
- Fixed-width font for code/commands
- Page numbers in footer
- Header with report title on each page

═══════════════════════════════════════════════════════════════
## 12. WEBSOCKET ENGINE — backend/routers/websocket.py
═══════════════════════════════════════════════════════════════

```python
# Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, room: str)
    async def disconnect(self, websocket: WebSocket, room: str)
    async def broadcast_to_room(self, room: str, message: dict)
    async def send_personal(self, websocket: WebSocket, message: dict)

manager = ConnectionManager()

# Routes:
# /ws/scan-progress/{job_id}  → subscribe to Redis channel scan:{job_id}
# /ws/alerts                  → subscribe to Redis channel alerts:live
# /ws/logs                    → subscribe to Redis channel logs:live  
# /ws/ai-stream               → bidirectional Claude streaming
# /ws/terminal/{session_id}   → bidirectional Metasploit session or tool shell
```

Each WebSocket handler:
1. Authenticates via query param `?token=<jwt>`
2. Subscribes to appropriate Redis channel
3. Forwards messages from Redis to WebSocket client
4. Handles disconnection gracefully

═══════════════════════════════════════════════════════════════
## 13. ATTACK GRAPH — backend/services/attack_graph.py
═══════════════════════════════════════════════════════════════

Class `AttackGraphService` using Neo4j:

Node types: Host, Service, Vulnerability, Credential, User, Network, Finding
Edge types: RUNS, HAS, EXPLOITS, LEADS_TO, AUTHENTICATES_WITH, LATERAL_MOVE

Methods:
- `create_host_node(target)` → node id
- `create_service_node(service_data, host_id)` → node id
- `create_vuln_node(finding)` → node id
- `add_exploit_edge(vuln_id, service_id)` → edge
- `add_lateral_path(from_host, to_host, method)` → edge
- `get_attack_paths(target_id)` → [{path[], nodes[], edges[]}]
- `get_graph_data(target_id)` → {nodes[], edges[]} for frontend
- Cypher: Build shortest path from 'External' to crown-jewel assets

═══════════════════════════════════════════════════════════════
## 14. FRONTEND — DETAILED COMPONENT SPECS
═══════════════════════════════════════════════════════════════

### Color Theme (globals.css + tailwind.config.ts)
Dark cybersecurity theme:
```
--bg-primary:    #0a0e1a   (deep navy black)
--bg-secondary:  #0f1629   (dark navy)
--bg-card:       #141d35   (card background)
--bg-elevated:   #1a2540   (elevated elements)
--border:        #1e3a5f   (subtle blue border)
--accent:        #00d4ff   (cyan accent)
--accent-green:  #00ff88   (green for success/safe)
--accent-red:    #ff3366   (red for critical)
--accent-orange: #ff8c42   (orange for high)
--accent-yellow: #ffd700   (yellow for medium)
--text-primary:  #e2e8f0
--text-secondary:#94a3b8
--text-muted:    #4a5568
```

Font: JetBrains Mono for code/terminal. Inter for UI text.
Add subtle scanline/grid CSS effects for cyber aesthetic.

### app/(dashboard)/layout.tsx
- Collapsible sidebar (64px collapsed, 280px expanded)
- Top bar with: search, notifications bell (live count), user menu, theme toggle
- Sidebar sections:
  - OPERATIONS: Dashboard, Targets
  - RED TEAM: Recon, Scanner, Web Attacks, Exploitation, Post-Exploit, Passwords, Wireless
  - BLUE TEAM: Alerts, SIEM, Detection Rules
  - FORENSICS: Memory, Disk, Malware Analysis
  - AI: AI Assistant, Attack Graph
  - PLATFORM: Reports, Findings, Settings
- Live stats in sidebar footer: active jobs counter, open alerts counter

### app/(dashboard)/dashboard/page.tsx
Grid layout with:
- **Row 1 (4 stat cards):** Total Targets, Open Findings (with severity breakdown sparkline),
  Active Jobs (with spinner if >0), Open Alerts (with critical count badge)
- **Row 2:** 
  - LEFT (60%): Recent Findings table (severity badge, target, tool, time, AI analysis preview)
  - RIGHT (40%): Risk Score gauge (recharts RadialBarChart) + Severity distribution pie
- **Row 3:**
  - LEFT (50%): Activity Timeline (recharts AreaChart — findings per day, 30d)
  - RIGHT (50%): Live Alert Feed (auto-scrolling, color-coded by severity)
- **Row 4:**
  - LEFT (40%): Active Tool Jobs (with progress bars, cancel button)
  - RIGHT (60%): MITRE ATT&CK coverage heatmap (custom grid component)

### app/(dashboard)/recon/page.tsx
Tabbed interface — tabs: Nmap, Amass, theHarvester, Shodan, WHOIS
Each tab:
- LEFT panel: Form with all tool parameters + target selector dropdown
- RIGHT panel: Tabbed output view — Terminal (xterm.js), Parsed Results (table),
  AI Analysis (markdown-rendered panel with MITRE badges)
- Bottom: Job history table for this tool

### app/(dashboard)/exploitation/page.tsx
3-column layout:
- Col 1: Searchsploit search + Module Browser (searchable list)
- Col 2: Module detail + configuration form (options key-value editor)
- Col 3: Active Sessions list + session terminal (xterm.js)
AI Suggest button: sends target findings to AI, returns suggested modules ranked

### components/tools/OutputTerminal.tsx
xterm.js terminal component:
- Dark theme matching platform
- Receives WebSocket messages and writes to terminal
- Auto-scroll to bottom
- Copy-to-clipboard button
- Download raw output button
- Search/filter within output
- Color-coded lines (errors=red, success=green, info=cyan)

### components/ai/AIChat.tsx
Full chat interface:
- Message history display (markdown rendering for AI responses)
- Code blocks with syntax highlighting + copy button
- Input box with: send button, attach file button, clear context button
- Context selector: "No context" | "Current Target" | "Current Findings" | "Current Job"
- Preset prompts panel (collapsible): quick-access common security queries
- Streaming response with cursor animation
- Export chat button

### app/(dashboard)/attack-graph/page.tsx
react-flow full-screen canvas:
- Node types with custom icons: Host (server icon), Vuln (bug icon),
  Cred (key icon), Service (plug icon)
- Color coding: nodes by severity/type
- Edge labels with attack technique names
- Right panel: selected node detail (findings, services, recommended exploits)
- Top toolbar: target selector, layout type (dagre/force), filter by severity
- Minimap in corner
- Export as PNG button

### lib/api.ts
```typescript
import axios from 'axios'
const api = axios.create({ baseURL: process.env.NEXT_PUBLIC_API_URL })
// Request interceptor: add Bearer token from localStorage
// Response interceptor: 401 → refresh token → retry; 403 → redirect
```

### lib/socket.ts
Socket.io client singleton with:
- Auto-reconnect with exponential backoff
- Auth header with JWT
- Event handlers: `onAlert`, `onScanProgress`, `onLogEntry`, `onJobComplete`
- Room subscriptions: `subscribeToJob(jobId)`, `subscribeToAlerts()`

═══════════════════════════════════════════════════════════════
## 15. DOCKER COMPOSE
═══════════════════════════════════════════════════════════════

```yaml
version: "3.9"
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: nexus_db
      POSTGRES_USER: nexus
      POSTGRES_PASSWORD: nexus_password
    volumes: [postgres_data:/var/lib/postgresql/data]
    ports: ["5432:5432"]

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes: [redis_data:/data]
    ports: ["6379:6379"]

  neo4j:
    image: neo4j:5-community
    environment:
      NEO4J_AUTH: neo4j/nexus_neo4j_password
      NEO4J_PLUGINS: '["apoc"]'
    volumes: [neo4j_data:/data]
    ports: ["7474:7474", "7687:7687"]

  backend:
    build: ./backend
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    volumes: [./backend:/app, /tmp/nexus:/tmp/nexus]
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [postgres, redis, neo4j]

  celery_worker:
    build: ./backend
    command: celery -A workers.celery_app worker --loglevel=info --concurrency=4
    volumes: [./backend:/app, /tmp/nexus:/tmp/nexus]
    env_file: .env
    depends_on: [postgres, redis]

  celery_beat:
    build: ./backend
    command: celery -A workers.celery_app beat --loglevel=info
    volumes: [./backend:/app]
    env_file: .env
    depends_on: [redis]

  flower:
    build: ./backend
    command: celery -A workers.celery_app flower --port=5555
    ports: ["5555:5555"]
    env_file: .env
    depends_on: [redis]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    env_file: frontend/.env.local
    depends_on: [backend]

  nginx:
    build: ./nginx
    ports: ["80:80", "443:443"]
    depends_on: [backend, frontend]

volumes:
  postgres_data:
  redis_data:
  neo4j_data:
```

═══════════════════════════════════════════════════════════════
## 16. BACKEND Dockerfile
═══════════════════════════════════════════════════════════════

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y \
    nmap nikto hydra sqlmap ffuf nuclei aircrack-ng \
    libpq-dev gcc git curl && \
    rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

═══════════════════════════════════════════════════════════════
## 17. REQUIREMENTS.TXT (backend)
═══════════════════════════════════════════════════════════════

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy[asyncio]==2.0.30
alembic==1.13.1
asyncpg==0.29.0
redis==5.0.4
celery[redis]==5.3.6
anthropic==0.28.0
neo4j==5.20.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
python-dotenv==1.0.1
aiofiles==23.2.1
httpx==0.27.0
pydantic==2.7.1
pydantic-settings==2.3.0
reportlab==4.2.0
shodan==1.31.0
typer==0.12.3
rich==13.7.1
websockets==12.0
yara-python==4.5.1
python-magic==0.4.27
pyshark==0.6
impacket==0.12.0
```

═══════════════════════════════════════════════════════════════
## 18. PACKAGE.JSON (frontend, key deps)
═══════════════════════════════════════════════════════════════

```json
{
  "name": "nexus-frontend",
  "version": "1.0.0",
  "dependencies": {
    "next": "^15.0.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "typescript": "^5.4.5",
    "tailwindcss": "^3.4.3",
    "next-auth": "^5.0.0",
    "axios": "^1.7.2",
    "socket.io-client": "^4.7.5",
    "zustand": "^4.5.2",
    "@tanstack/react-query": "^5.40.0",
    "recharts": "^2.12.7",
    "reactflow": "^11.11.4",
    "@xterm/xterm": "^5.5.0",
    "@xterm/addon-fit": "^0.10.0",
    "lucide-react": "^0.383.0",
    "react-markdown": "^9.0.1",
    "react-syntax-highlighter": "^15.5.0",
    "date-fns": "^3.6.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.3.0"
  }
}
```

═══════════════════════════════════════════════════════════════
## 19. BUILD PHASES — FOLLOW THIS ORDER EXACTLY
═══════════════════════════════════════════════════════════════

### PHASE 1 — Foundation (Backend Core)
Output in this order:
1. `.env.example`
2. `.gitignore`
3. `backend/requirements.txt`
4. `backend/core/config.py`
5. `backend/core/database.py`
6. `backend/core/redis_client.py`
7. `backend/core/neo4j_client.py`
8. `backend/core/security.py`
9. `backend/core/dependencies.py`
10. All SQLAlchemy `backend/models/*.py` files
11. All Pydantic `backend/schemas/*.py` files
12. `backend/alembic.ini` + `backend/alembic/env.py`
13. `backend/main.py`

Confirm: "Phase 1 complete — Foundation ready"

### PHASE 2 — API Routers
Output in this order:
1. `backend/routers/auth.py`
2. `backend/routers/users.py`
3. `backend/routers/targets.py`
4. `backend/routers/scans.py`
5. `backend/routers/findings.py`
6. `backend/routers/exploits.py`
7. `backend/routers/ai.py`
8. `backend/routers/reports.py`
9. `backend/routers/alerts.py`
10. `backend/routers/blueteam.py`
11. `backend/routers/forensics.py`
12. `backend/routers/wireless.py`
13. `backend/routers/websocket.py`

Confirm: "Phase 2 complete — All API routers ready"

### PHASE 3 — Tool Implementations
Output all files in `backend/tools/` across all subdirectories.
Start with `backend/utils/` utilities (parser_utils, xml_parser, cvss_calculator, mitre_mapper, logger).
Then each tool subdirectory: recon, scanning, web, exploitation, password, post_exploit, network, wireless, blueteam, forensics.

Confirm: "Phase 3 complete — All tool wrappers ready"

### PHASE 4 — Services & Workers
1. `backend/services/ai_engine.py` — FULL implementation
2. `backend/services/tool_orchestrator.py` — FULL implementation
3. `backend/services/report_generator.py` — FULL implementation
4. `backend/services/attack_graph.py`
5. `backend/services/log_ingestor.py`
6. `backend/services/notification_service.py`
7. `backend/workers/celery_app.py`
8. `backend/workers/scan_tasks.py`
9. `backend/workers/ai_tasks.py`
10. `backend/workers/report_tasks.py`
11. `backend/workers/exploit_tasks.py`
12. `backend/Dockerfile`

Confirm: "Phase 4 complete — All services and workers ready"

### PHASE 5 — Frontend Foundation
1. `frontend/package.json`
2. `frontend/tsconfig.json`
3. `frontend/tailwind.config.ts`
4. `frontend/next.config.ts`
5. `frontend/app/globals.css` — FULL cyber theme
6. `frontend/app/layout.tsx`
7. `frontend/lib/api.ts`
8. `frontend/lib/auth.ts`
9. `frontend/lib/socket.ts`
10. `frontend/lib/utils.ts`
11. `frontend/lib/constants.ts`
12. All `frontend/store/*.ts` files
13. All `frontend/types/*.ts` files
14. `frontend/app/(auth)/login/page.tsx`
15. `frontend/app/(auth)/register/page.tsx`
16. `frontend/app/(dashboard)/layout.tsx` — with full sidebar

Confirm: "Phase 5 complete — Frontend foundation ready"

### PHASE 6 — Frontend Components
Output ALL components in `frontend/components/` with full implementation:
- layout/ (Sidebar, TopBar, etc.)
- dashboard/ (all stat cards, charts, feeds)
- tools/ (ToolCard, ToolLauncher, JobStatus, OutputTerminal with xterm.js)
- ai/ (AIChat, AIAnalysisPanel, MITREMapper, KillChainView)
- findings/ (FindingCard, FindingDetail, CVSSBadge, FindingFilters)
- charts/ (all chart components)
- attack-graph/ (GraphCanvas, NodeTypes, EdgeTypes with react-flow)
- reports/ (ReportBuilder, ReportPreview)

Confirm: "Phase 6 complete — All components ready"

### PHASE 7 — Frontend Pages
Output ALL pages in `frontend/app/(dashboard)/`:
1. dashboard/page.tsx
2. targets/page.tsx + targets/[id]/page.tsx
3. recon/page.tsx
4. scanner/page.tsx
5. web-attacks/page.tsx
6. exploitation/page.tsx
7. post-exploit/page.tsx
8. passwords/page.tsx
9. wireless/page.tsx
10. blueteam/page.tsx + blueteam/siem/page.tsx + blueteam/alerts/page.tsx + blueteam/rules/page.tsx
11. forensics/page.tsx + forensics/memory/page.tsx + forensics/disk/page.tsx + forensics/malware/page.tsx
12. ai-assistant/page.tsx
13. attack-graph/page.tsx
14. reports/page.tsx + reports/[id]/page.tsx
15. findings/page.tsx
16. settings/page.tsx
17. `frontend/Dockerfile`

Confirm: "Phase 7 complete — All pages ready"

### PHASE 8 — Infrastructure & Docs
1. `docker-compose.yml`
2. `nginx/nginx.conf`
3. `nginx/Dockerfile`
4. `README.md` — full setup guide (install, configure .env, docker-compose up, first login)

Confirm: "Phase 8 complete — NEXUS platform fully built ✅"

═══════════════════════════════════════════════════════════════
## 20. CRITICAL IMPLEMENTATION RULES
═══════════════════════════════════════════════════════════════

1. **NEVER output placeholder code.** No "# implement this", no "pass", no "..."
   Every function must have a real, working implementation.

2. **Every file = complete file.** Show the entire file from top to bottom,
   including all imports, every class, every method.

3. **Type everything.** Full Python type hints. Full TypeScript types.
   No `any` in TypeScript unless absolutely unavoidable.

4. **Error handling everywhere.** Try/except in Python, try/catch in TS.
   FastAPI HTTPExceptions with proper status codes.
   WebSocket error handling. Subprocess timeout handling.

5. **Real subprocess commands.** Use actual tool CLI syntax.
   Every tool runner must produce commands that work on Kali Linux.

6. **Real AI prompts.** AI engine methods must include actual detailed
   system prompts and structured user prompts — not "your prompt here".

7. **Consistent naming.** snake_case Python, camelCase/PascalCase TypeScript.
   REST conventions for all endpoints.

8. **Security first.** All endpoints require JWT auth except /api/auth/*.
   No hardcoded secrets. Validate all inputs with Pydantic.
   Sanitize tool inputs to prevent command injection.
   Rate limit AI endpoints.

9. **Async everything.** All FastAPI routes async. All DB calls await.
   All tool subprocess calls async. All AI calls async.

10. **Real-time by default.** Every tool run publishes progress to Redis.
    WebSocket consumers forward to browser. Dashboard reflects live state.

═══════════════════════════════════════════════════════════════
## START COMMAND
═══════════════════════════════════════════════════════════════

Begin with Phase 1. Output every file listed, fully implemented.
After completing all 8 phases, the output must be a complete,
runnable NEXUS platform with zero gaps.

> ⚠️ ETHICS NOTICE (include in README):
> NEXUS is built for authorized security testing, SOC operations, CTF
> competitions, and defensive research only. All tool use must occur
> within explicit written authorization. Unauthorized use is illegal
> under CFAA, IT Act 2000, and equivalent legislation worldwide.

START PHASE 1 NOW →
