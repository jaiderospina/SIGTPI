import { Navigate } from "react-router-dom"
import { useAuthStore } from "@/store/auth"

interface Props {
  children: React.ReactNode
  roles?: string[]
}

export default function ProtectedRoute({ children, roles }: Props) {
  const { isAuthenticated, hasRole } = useAuthStore()
  if (!isAuthenticated()) return <Navigate to="/login" replace />
  if (roles && !hasRole(...roles)) return <Navigate to="/dashboard" replace />
  return <>{children}</>
}
