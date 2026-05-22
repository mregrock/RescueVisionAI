export type RiskLevel = 'low' | 'medium' | 'high' | 'critical'
export type VictimStatus = 'OK' | 'Minor' | 'Serious' | 'Critical'
export type Scenario =
  | 'single_unconscious'
  | 'multiple_victims'
  | 'severe_bleeding'
  | 'low_confidence'

export interface Gps {
  lat: number
  lon: number
}

export interface AnalyzeRequest {
  incident_id: string
  rescuer_id: string
  scenario: Scenario
  gps?: Gps
  timestamp?: string
}

export interface Scene {
  people_count: number
  observations: string[]
}

export interface Victim {
  id: number
  priority: number
  severity_score: number
  severity_label: RiskLevel
  status: VictimStatus
  bbox: [number, number, number, number] | null
  signals: string[]
  first_aid: string[]
  protocols: string[]
}

export interface Action {
  id: string
  title: string
  description: string
  priority: number
  critical: boolean
}

export interface Quality {
  low_confidence: boolean
  notes: string[]
}

export interface AnalyzeResponse {
  analysis_id: string
  overall_risk: RiskLevel
  confidence: number
  scene: Scene
  victims: Victim[]
  recommended_actions: Action[]
  protocols: string[]
  quality: Quality
  disclaimer: string
  scenario?: Scenario
}

export interface ProtocolSummary {
  id: string
  title: string
  tags: string[]
}

export interface ProtocolsList {
  protocols: ProtocolSummary[]
}

export interface Protocol extends ProtocolSummary {
  summary?: string
  steps: string[]
  warnings?: string[]
  disclaimer?: string
}

export interface HealthResponse {
  status: string
  service: string
  version: string
}
