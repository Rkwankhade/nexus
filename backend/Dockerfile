FROM python:3.11-slim

WORKDIR /app

# System packages backing the recon / scanning / blue-team / forensics tool
# runners that are actually implemented in backend/tools/. Deliberately does
# NOT include exploitation, credential-cracking, or lateral-movement tooling.
#
# DEBIAN_FRONTEND=noninteractive + the debconf preseed line below are
# required because tshark's postinst asks an interactive yes/no question
# ("should non-superusers be able to capture packets?") that otherwise
# hangs/fails a non-interactive Docker build with exit code 100.
ENV DEBIAN_FRONTEND=noninteractive
RUN echo "wireshark-common wireshark-common/install-setuid boolean false" | debconf-set-selections

RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap \
    whois \
    tshark \
    yara \
    suricata \
    libpq-dev \
    gcc \
    git \
    curl \
    ca-certificates \
    perl \
    && rm -rf /var/lib/apt/lists/*

# nikto isn't packaged for this Debian release (trixie) — it's a small Perl
# script tool anyway, so install it straight from the upstream repo instead.
RUN git clone --depth 1 https://github.com/sullo/nikto.git /opt/nikto \
    && ln -s /opt/nikto/program/nikto.pl /usr/local/bin/nikto \
    && chmod +x /opt/nikto/program/nikto.pl

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]