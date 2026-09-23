import axios from "axios"
import { useAuthStore } from "@/store/auth"

const api = axios.create({ baseURL: "/" })

api.interceptors.request.use(cfg => {
  const token = useAuthStore.getState().token
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

// Track redirect to avoid loops
let _redirecting = false

api.interceptors.response.use(
  r => r,
  err => {
    // Only handle 401 from auth endpoints — not from data queries
    const url = err.config?.url ?? ''
    const isAuthCall = url.includes('/api/auth/')
    
    if (err.response?.status === 401 && isAuthCall && !_redirecting) {
      _redirecting = true
      const store = useAuthStore.getState() as any
      if (store.clearAuth) store.clearAuth()
      setTimeout(() => { _redirecting = false }, 3000)
      if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

export default api

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string, totp_code?: string) =>
    api.post('/api/auth/login', { email, password, totp_code }),
  me:    () => api.get('/api/auth/me'),
  changePassword: (d: unknown) => api.post('/api/auth/password/change', d),
  mfaSetup:   () => api.post('/api/auth/mfa/setup', {}),
  mfaVerify:  (totp_code: string) => api.post('/api/auth/mfa/verify', { totp_code }),
  mfaDisable: () => api.post('/api/auth/mfa/disable', {}),
}

// ── Users ─────────────────────────────────────────────────────────────────────
export const userApi = {
  list:   (p?: Record<string,unknown>) => api.get('/api/users/users', { params: p }),
  get:    (id: string) => api.get(`/api/users/users/${id}`),
  me:     () => api.get('/api/users/users/me'),
  create: (d: unknown) => api.post('/api/users/users', d),
  update: (id: string, d: unknown) => api.patch(`/api/users/users/${id}`, d),
  status: (id: string, status: string) => api.patch(`/api/users/users/${id}/status`, { status }),
  roles:  {
    assign: (d: unknown) => api.post('/api/users/roles/assign', d),
    revoke: (d: unknown) => api.post('/api/users/roles/revoke', d),
  },
}

// ── TI Management ─────────────────────────────────────────────────────────────
export const tiApi = {
  list:   (p?: Record<string,unknown>) => api.get('/api/ti/ti', { params: p }),
  get:    (id: string) => api.get(`/api/ti/ti/${id}`),
  create: (d: unknown) => api.post('/api/ti/ti', d),
  advance:(d: unknown) => api.post('/api/ti/ti/advances', d),
  approveMilestone:(id: string, d: unknown) => api.post(`/api/ti/ti/milestones/${id}/approve`, d),
  alerts: (p?: Record<string,unknown>) => api.get('/api/ti/ti/alerts', { params: p }),
  justifyAlert:(id: string, j: string) =>
    api.post(`/api/ti/ti/alerts/${id}/justify`, { justification: j }),
}

// ── Sessions ──────────────────────────────────────────────────────────────────
export const sessionApi = {
  list:    (p?: Record<string,unknown>) => api.get('/api/sessions/sessions', { params: p }),
  create:  (d: unknown) => api.post('/api/sessions/sessions', d),
  complete:(id: string) => api.post(`/api/sessions/sessions/${id}/complete`),
  cancel:  (id: string, reason: string) =>
    api.post(`/api/sessions/sessions/${id}/cancel`, { reason }),
  createMinutes: (d: unknown) => api.post('/api/sessions/sessions/minutes', d),
}

// ── Notifications ─────────────────────────────────────────────────────────────
export const notifApi = {
  list:    (p?: Record<string,unknown>) => api.get('/api/notifications/notifications/my', { params: p }),
  unread:  () => api.get('/api/notifications/notifications/my/unread-count'),
  markRead:(id: string) => api.post(`/api/notifications/notifications/${id}/read`),
  send:    (d: unknown) => api.post('/api/notifications/notifications', d),
}

// ── Evaluations ───────────────────────────────────────────────────────────────
export const evalApi = {
  rubrics:     () => api.get('/api/evaluations/evaluations/rubrics'),
  createRubric:(d: unknown) => api.post('/api/evaluations/evaluations/rubrics', d),
  create:      (d: unknown) => api.post('/api/evaluations/evaluations', d),
  get:         (id: string) => api.get(`/api/evaluations/evaluations/${id}`),
  score:       (d: unknown) => api.post('/api/evaluations/evaluations/scores', d),
  dictamen:    (id: string, d: unknown) =>
    api.post(`/api/evaluations/evaluations/${id}/dictamen`, d),
}

// ── Reports ───────────────────────────────────────────────────────────────────
export const reportApi = {
  dashboard: () => api.get('/api/reports/reports/dashboard'),
  tiStatus:  () => api.get('/api/reports/reports/ti/status'),
  student:   (id: string) => api.get(`/api/reports/reports/students/${id}`),
  tutor:     (id: string) => api.get(`/api/reports/reports/tutors/${id}/workload`),
  program:   (id: string) => api.get(`/api/reports/reports/programs/${id}`),
}
