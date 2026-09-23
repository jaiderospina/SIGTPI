export interface User {
  id: string
  email: string
  full_name: string
  status: string
  is_superuser: boolean
  totp_enabled: boolean
  roles: Role[]
}

export interface Role {
  id: string
  role_code: string
  program_id: string | null
  is_active: boolean
}

export interface AuthState {
  token: string | null
  user: User | null
  roles: string[]
  isAuthenticated: boolean
}

export interface TI {
  id: string
  title: string
  knowledge_area: string
  status: string
  progress_percent: number
  student_id: string
  tutor_id: string
  estimated_defense: string | null
  milestones: Milestone[]
  advances: Advance[]
  alerts: Alert[]
  active_alerts?: number
}

export interface Milestone {
  id: string
  name: string
  milestone_type: string
  status: string
  planned_date: string
  actual_date: string | null
  weight_percent: number
  is_critical: boolean
}

export interface Advance {
  id: string
  period: string
  activities_done: string
  progress_percent: number
  obstacles: string | null
  registered_at: string
}

export interface Alert {
  id: string
  level: string
  reason: string
  status: string
  detected_at: string
}

export interface Session {
  id: string
  ti_id: string
  tutor_id: string
  student_id: string
  scheduled_at: string
  duration_minutes: number
  modality: string
  status: string
  agenda: string | null
  meeting_url: string | null
  has_minutes?: boolean
}

export interface Notification {
  id: string
  subject: string
  priority: string
  status: string
  is_read: boolean
  event_type: string | null
  created_at: string
}

export type RoleCode = 'EST' | 'TUT' | 'COT' | 'CEV' | 'DIR' | 'COO' | 'ADM' | 'EXT'
