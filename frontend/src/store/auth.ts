import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@/types'

interface AuthStore {
  token: string | null
  user: User | null
  roles: string[]
  setAuth: (token: string, user: User, roles: string[]) => void
  clearAuth: () => void
  isAuthenticated: () => boolean
  hasRole: (...roles: string[]) => boolean
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      roles: [],
      setAuth: (token, user, roles) => set({ token, user, roles }),
      clearAuth: () => set({ token: null, user: null, roles: [] }),
      isAuthenticated: () => !!get().token,
      hasRole: (...roles) => roles.some(r => get().roles.includes(r)),
    }),
    { name: 'sigtpi-auth', partialize: s => ({ token: s.token, user: s.user, roles: s.roles }) }
  )
)
