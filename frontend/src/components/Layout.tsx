import React, { useState } from "react"
import { Link, useLocation, useNavigate } from "react-router-dom"
import { useAuthStore } from "@/store/auth"
import { useQuery } from "@tanstack/react-query"
import { notifApi } from "@/services/api"
import {
  LayoutDashboard, BookOpen, Calendar, FileText,
  Bell, LogOut, Menu, X, ChevronDown, User, Settings,
  GraduationCap, ClipboardList, BarChart2, Shield,
  UserCheck, TrendingUp, CheckCircle
} from "lucide-react"
import clsx from "clsx"

const navItems = [
  { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard", roles: ["EST","TUT","COO","DIR","ADM"] },
  { to: "/ti",        icon: BookOpen,        label: "Trabajos de Investigación", roles: ["EST","TUT","COO","DIR"] },
  { to: "/assignments",  icon: UserCheck,  label: "Asignaciones",             roles: ["EST","TUT","COO","DIR","ADM"] },
  { to: "/advances",     icon: TrendingUp, label: "Registro de Avances",       roles: ["EST","TUT"] },
  { to: "/milestones",   icon: CheckCircle,label: "Hitos y Cronograma",        roles: ["EST","TUT","COO","DIR"] },
  { to: "/sessions",  icon: Calendar,        label: "Sesiones", roles: ["EST","TUT","COO"] },
  { to: "/programs",    icon: GraduationCap, label: "Programas",                  roles: ["ADM","COO","DIR"] },
  { to: "/evaluations",icon: ClipboardList,  label: "Evaluaciones", roles: ["TUT","CEV","DIR","COO"] },
  { to: "/reports",   icon: BarChart2,       label: "Reportes", roles: ["COO","DIR","ADM"] },
  { to: "/users",     icon: User,            label: "Usuarios", roles: ["ADM","COO"] },
]

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, roles, clearAuth } = useAuthStore()
  const location = useLocation()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)

  const { data: unread } = useQuery({
    queryKey: ["unread-count"],
    queryFn: () => notifApi.unread().then(r => r.data),
    refetchInterval: 30_000,
  })

  const visible = navItems.filter(item => item.roles.some(r => roles.includes(r)))

  const handleLogout = () => { clearAuth(); navigate("/login") }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className={clsx(
        "fixed inset-y-0 left-0 z-50 w-64 bg-primary-700 text-white flex flex-col transform transition-transform duration-200 lg:relative lg:translate-x-0",
        sidebarOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        {/* Logo */}
        <div className="flex items-center gap-3 px-6 py-5 border-b border-primary-500/40">
          <div className="w-9 h-9 bg-white/20 rounded-lg flex items-center justify-center">
            <GraduationCap className="w-5 h-5" />
          </div>
          <div>
            <p className="font-bold text-sm leading-tight">SIGTPI</p>
            <p className="text-xs text-white/60 leading-tight">v2.0</p>
          </div>
          <button className="ml-auto lg:hidden" onClick={() => setSidebarOpen(false)}>
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {visible.map(item => (
            <Link
              key={item.to}
              to={item.to}
              onClick={() => setSidebarOpen(false)}
              className={clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                location.pathname.startsWith(item.to)
                  ? "bg-white/20 text-white"
                  : "text-white/70 hover:bg-white/10 hover:text-white"
              )}
            >
              <item.icon className="w-4 h-4 flex-shrink-0" />
              {item.label}
            </Link>
          ))}
        </nav>

        {/* User info bottom */}
        <div className="px-4 py-4 border-t border-primary-500/40">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center text-sm font-bold">
              {user?.full_name?.[0] ?? "U"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium truncate">{user?.full_name}</p>
              <p className="text-xs text-white/50 truncate">{roles[0]}</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-40 bg-black/50 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Topbar */}
        <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-4">
          <button className="lg:hidden" onClick={() => setSidebarOpen(true)}>
            <Menu className="w-5 h-5 text-gray-600" />
          </button>
          <div className="flex-1" />

          {/* Notifications */}
          <Link to="/notifications" className="relative p-2 text-gray-500 hover:text-primary-700 hover:bg-gray-100 rounded-lg">
            <Bell className="w-5 h-5" />
            {(unread?.unread_count ?? 0) > 0 && (
              <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-danger text-white text-xs rounded-full flex items-center justify-center">
                {unread?.unread_count}
              </span>
            )}
          </Link>

          {/* User menu */}
          <div className="relative">
            <button
              onClick={() => setUserMenuOpen(v => !v)}
              className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 text-sm"
            >
              <div className="w-7 h-7 bg-primary-700 text-white rounded-full flex items-center justify-center text-xs font-bold">
                {user?.full_name?.[0] ?? "U"}
              </div>
              <span className="hidden sm:block font-medium text-gray-700">{user?.full_name?.split(" ")[0]}</span>
              <ChevronDown className="w-4 h-4 text-gray-400" />
            </button>
            {userMenuOpen && (
              <div className="absolute right-0 mt-1 w-48 bg-white border border-gray-200 rounded-xl shadow-lg py-1 z-50">
                <Link to="/profile" className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50" onClick={() => setUserMenuOpen(false)}>
                  <User className="w-4 h-4" /> Mi perfil
                </Link>
                <button onClick={handleLogout} className="w-full flex items-center gap-2 px-4 py-2 text-sm text-danger hover:bg-gray-50">
                  <LogOut className="w-4 h-4" /> Cerrar sesión
                </button>
              </div>
            )}
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
