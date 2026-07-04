export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info'

export type TargetStatus = 'pending_auth' | 'authorized' | 'active' | 'inactive'

export interface Target {
  id: string
  name: string
  host: string
  type?: 'ip' | 'domain' | 'network' | 'webapp' | 'wireless'
  scope_notes?: string
  status?: TargetStatus
  authorization_reference?: string
  created_at: string
}

export type FindingStatus = 'open' | 'confirmed' | 'false_positive' | 'remediated' | 'accepted_risk'

export interface Finding {
  id: string
  target_id: string
  target_name: string
  scan_id?: string
  title: string
  description?: string
  severity: Severity
  status?: FindingStatus
  tool: string
  cvss_score?: number
  cvss_vector?: string
  cve_ids?: string[]
  mitre_techniques: string[]
  affected_host?: string
  affected_port?: number
  affected_service?: string
  evidence?: Record<string, unknown>
  remediation?: string
  ai_summary?: string
  ai_analysis?: Record<string, unknown>
  created_at: string
  updated_at?: string
}

export interface ToolJob {
  id: string
  tool: string
  tool_name?: string
  category?: string
  target_id: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  progress: number
  result_summary?: Record<string, unknown>
  error_message?: string
  started_at?: string
  finished_at?: string
  created_at?: string
}

export interface Alert {
  id: string
  severity: Severity
  title: string
  message: string
  source: string
  created_at: string
  acknowledged: boolean
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface GraphNode {
  id: string
  type: 'host' | 'vuln' | 'cred' | 'service'
  label: string
  severity?: Severity
  data?: Record<string, unknown>
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  label?: string
}

export type ReportFormat = 'pdf' | 'html' | 'json'
export type ReportStatus = 'pending' | 'generating' | 'ready' | 'failed'

export interface Report {
  id: string
  target_id: string
  generated_by: string
  title: string
  format: ReportFormat
  status: ReportStatus
  file_path?: string
  summary?: Record<string, unknown>
  created_at: string
}

export interface DetectionRule {
  id: string
  name: string
  description?: string
  engine: 'sigma' | 'suricata' | 'yara' | 'custom'
  severity: Severity
  enabled: boolean
  match_count?: number
}

export interface LogEntry {
  id: string
  source: string
  host: string
  event_type: string
  severity: string
  message: string
  matched_rules?: string[]
  ingested_at: string
}
