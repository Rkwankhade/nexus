export const APP_NAME = 'NEXUS'
export const APP_TAGLINE = 'AI-Powered Cyber Operations Platform'

export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'
export const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8000'

export const SEVERITIES = ['critical', 'high', 'medium', 'low', 'info'] as const

export const TARGET_TYPES = ['ip', 'domain', 'network', 'webapp', 'wireless'] as const

export const SCAN_STATUSES = ['queued', 'running', 'completed', 'failed', 'cancelled'] as const

/** Recon / scanning / analysis tools this platform can orchestrate.
 *  Exploitation, credential-attack, and lateral-movement tooling are
 *  intentionally out of scope for this build. */
export const RECON_TOOLS = [
  { id: 'nmap', label: 'Nmap', description: 'Port & service discovery' },
  { id: 'amass', label: 'Amass', description: 'Subdomain enumeration' },
  { id: 'theharvester', label: 'theHarvester', description: 'OSINT email/host harvesting' },
  { id: 'shodan', label: 'Shodan', description: 'Internet-wide device search' },
  { id: 'whois', label: 'WHOIS', description: 'Domain registration lookup' },
  { id: 'dnsx', label: 'dnsx', description: 'Fast DNS resolution/enum' },
] as const

export const SCANNING_TOOLS = [
  { id: 'nuclei', label: 'Nuclei', description: 'Template-based vulnerability scanning' },
  { id: 'nikto', label: 'Nikto', description: 'Web server misconfiguration scanner' },
  { id: 'openvas', label: 'OpenVAS', description: 'Full vulnerability assessment' },
  { id: 'wpscan', label: 'WPScan', description: 'WordPress security scanner' },
] as const

export const WEB_TOOLS = [
  { id: 'ffuf', label: 'ffuf', description: 'Fast web content/parameter fuzzing' },
  { id: 'wfuzz', label: 'Wfuzz', description: 'Web application fuzzer' },
  { id: 'dalfox', label: 'Dalfox', description: 'XSS scanning' },
] as const

export const BLUETEAM_TOOLS = [
  { id: 'sigma', label: 'Sigma', description: 'Generic detection rule engine' },
  { id: 'wazuh', label: 'Wazuh', description: 'Host-based SIEM/EDR' },
  { id: 'yara', label: 'YARA', description: 'Pattern-based file/malware matching' },
  { id: 'suricata', label: 'Suricata', description: 'Network IDS/IPS' },
] as const

export const FORENSICS_TOOLS = [
  { id: 'volatility', label: 'Volatility', description: 'Memory forensics' },
  { id: 'pcap_analyzer', label: 'PCAP Analyzer', description: 'Packet capture analysis' },
  { id: 'autopsy', label: 'Autopsy', description: 'Disk/file-system forensics' },
  { id: 'yara_malware', label: 'YARA Malware Scan', description: 'Static malware signature matching' },
  { id: 'static_analyzer', label: 'Static Analyzer', description: 'Binary/file static analysis' },
] as const

export const MITRE_TACTICS = [
  'Reconnaissance',
  'Resource Development',
  'Initial Access',
  'Execution',
  'Persistence',
  'Privilege Escalation',
  'Defense Evasion',
  'Credential Access',
  'Discovery',
  'Lateral Movement',
  'Collection',
  'Command and Control',
  'Exfiltration',
  'Impact',
] as const

export const REPORT_FORMATS = ['pdf', 'html', 'json'] as const

export const POLL_INTERVAL_MS = 15_000
