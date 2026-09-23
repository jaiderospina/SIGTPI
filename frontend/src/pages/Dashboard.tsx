import { useQuery } from "@tanstack/react-query"
import { useAuthStore } from "@/store/auth"
import { reportApi, tiApi, sessionApi } from "@/services/api"
import StatCard from "@/components/StatCard"
import ProgressBar from "@/components/ProgressBar"
import AlertBadge from "@/components/AlertBadge"
import { Link } from "react-router-dom"
import {
  BookOpen, Calendar, AlertTriangle, TrendingUp,
  Users, Clock, CheckCircle, BarChart2, Bell,
  ArrowRight, ClipboardList
} from "lucide-react"
import { format, parseISO } from "date-fns"
import { es } from "date-fns/locale"
import type { TI, Session, Alert } from "@/types"

export default function Dashboard() {
  const { user, roles, hasRole } = useAuthStore()

  const { data: dashSummary } = useQuery({
    queryKey: ["dash-summary"],
    queryFn: () => reportApi.dashboard().then(r => r.data),
    enabled: hasRole("COO","DIR","ADM"),
    staleTime: 60_000,
  })

  const { data: tiSummary, isLoading: loadingSummary } = useQuery({
    queryKey: ["ti-summary"],
    queryFn: () => reportApi.tiStatus().then(r => r.data),
    enabled: hasRole("COO","DIR","ADM"),
  })

  const { data: myTIs, isLoading: loadingMyTIs } = useQuery({
    queryKey: ["my-tis"],
    queryFn: () => tiApi.list({ student_id: user?.id }).then(r => r.data),
    enabled: hasRole("EST"),
  })

  const { data: tutorTIs } = useQuery({
    queryKey: ["tutor-tis"],
    queryFn: () => tiApi.list({ tutor_id: user?.id }).then(r => r.data),
    enabled: hasRole("TUT"),
  })

  const { data: sessions } = useQuery({
    queryKey: ["upcoming-sessions"],
    queryFn: () => sessionApi.list({
      student_id: hasRole("EST") ? user?.id : undefined,
      tutor_id:   hasRole("TUT") ? user?.id : undefined,
      status: "scheduled"
    }).then(r => r.data),
    enabled: hasRole("EST","TUT","COO"),
  })

  const firstName = user?.full_name?.split(" ")[0] ?? "Usuario"
  const hour = new Date().getHours()
  const greeting = hour < 12 ? "Buenos días" : hour < 18 ? "Buenas tardes" : "Buenas noches"
  const roleLabel: Record<string,string> = {
    ADM:"Administrador", COO:"Coordinador", DIR:"Director",
    TUT:"Tutor", EST:"Estudiante", CEV:"Comité Evaluador",
    COT:"Co-Tutor", EXT:"Evaluador Externo"
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">{greeting}, {firstName} 👋</h1>
        <div className="flex items-center gap-3 mt-1">
          <p className="text-gray-500 text-sm">
            {format(new Date(), "EEEE, d 'de' MMMM 'de' yyyy", { locale: es })}
          </p>
          {roles.slice(0,3).map(r => (
            <span key={r} className="text-xs bg-primary-50 text-primary-700 px-2 py-0.5 rounded-full font-medium">
              {roleLabel[r] ?? r}
            </span>
          ))}
        </div>
      </div>

      {/* ── ADM / COO / DIR ─────────────────────────────────────────────────── */}
      {hasRole("ADM","COO","DIR") && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {loadingSummary ? (
              [1,2,3,4].map(i => <div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse"/>)
            ) : (
              <>
                <StatCard title="TIs Activos" value={dashSummary?.active_tis ?? tiSummary?.total_tis ?? 0} icon={BookOpen} color="blue" />
                <StatCard title="Estudiantes" value={dashSummary?.total_students ?? 0} icon={Users} color="green" />
                <StatCard title="Tutores" value={dashSummary?.total_tutors ?? 0} icon={Users} color="purple" />
                <StatCard title="En riesgo" value={dashSummary?.active_alerts ?? tiSummary?.at_risk ?? 0} icon={AlertTriangle} color="red" />
                <StatCard title="Progreso prom." value={`${tiSummary?.avg_progress ?? 0}%`} icon={CheckCircle} color="purple" />
              </>
            )}
          </div>

          {/* Quick access cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
            {[
              { to:"/ti",         icon:BookOpen,      label:"Trabajos de Investigación", desc:"Gestionar TIs activos",       color:"blue"   },
              { to:"/sessions",   icon:Calendar,      label:"Sesiones",                  desc:"Sesiones programadas",        color:"green"  },
              { to:"/reports",    icon:BarChart2,     label:"Reportes y KPIs",           desc:"Indicadores del sistema",     color:"purple" },
            ].map(item => (
              <Link key={item.to} to={item.to}
                className="card flex items-center gap-4 hover:border-primary-300 hover:shadow-md transition-all group">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 bg-primary-50 group-hover:bg-primary-700 transition-colors`}>
                  <item.icon className="w-6 h-6 text-primary-700 group-hover:text-white transition-colors" />
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-gray-900 text-sm">{item.label}</p>
                  <p className="text-xs text-gray-500">{item.desc}</p>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-300 group-hover:text-primary-500 transition-colors" />
              </Link>
            ))}
          </div>

          {/* System status */}
          <div className="card">
            <h3 className="font-semibold text-gray-800 mb-4">Estado del sistema</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[
                { label:"auth-service",    port:8001 },
                { label:"user-service",    port:8002 },
                { label:"ti-management",   port:8005 },
                { label:"report-service",  port:8011 },
              ].map(svc => (
                <div key={svc.port} className="flex items-center gap-2 p-3 bg-green-50 rounded-lg">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  <div>
                    <p className="text-xs font-medium text-gray-700">{svc.label}</p>
                    <p className="text-xs text-gray-400">:{svc.port}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {/* ── EST ──────────────────────────────────────────────────────────────── */}
      {hasRole("EST") && (
        <div className="space-y-6">
          {loadingMyTIs ? (
            <div className="card h-32 animate-pulse bg-gray-100" />
          ) : myTIs?.items?.length === 0 ? (
            <div className="card text-center py-12">
              <BookOpen className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 font-medium">No tienes un Trabajo de Investigación registrado</p>
              <p className="text-sm text-gray-400 mt-1">Contacta a tu coordinador para iniciar el proceso</p>
            </div>
          ) : (
            myTIs?.items?.map((ti: TI) => (
              <Link key={ti.id} to={`/ti/${ti.id}`} className="card block hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h2 className="font-semibold text-gray-900">{ti.title}</h2>
                    <p className="text-sm text-gray-500 mt-0.5">{ti.knowledge_area}</p>
                  </div>
                  <span className="badge-active">{ti.status}</span>
                </div>
                <ProgressBar value={ti.progress_percent} label="Avance general" />
                {ti.alerts?.filter((a:Alert) => a.status==="active").length > 0 && (
                  <div className="mt-4 space-y-2">
                    {ti.alerts.filter((a:Alert) => a.status==="active").map((a:Alert) => (
                      <div key={a.id} className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg">
                        <AlertBadge level={a.level} />
                        <p className="text-xs text-gray-600">{a.reason}</p>
                      </div>
                    ))}
                  </div>
                )}
              </Link>
            ))
          )}

          {/* Quick links for student */}
          <div className="grid grid-cols-2 gap-4">
            <Link to="/sessions" className="card flex items-center gap-3 hover:shadow-md transition-shadow">
              <Calendar className="w-8 h-8 text-primary-500" />
              <div><p className="font-medium text-sm">Mis sesiones</p><p className="text-xs text-gray-400">{sessions?.total ?? 0} registradas</p></div>
            </Link>
            <Link to="/notifications" className="card flex items-center gap-3 hover:shadow-md transition-shadow">
              <Bell className="w-8 h-8 text-warning" />
              <div><p className="font-medium text-sm">Notificaciones</p><p className="text-xs text-gray-400">Ver todas</p></div>
            </Link>
          </div>
        </div>
      )}

      {/* ── TUT ──────────────────────────────────────────────────────────────── */}
      {hasRole("TUT") && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <StatCard title="Estudiantes activos" value={tutorTIs?.total ?? 0} icon={Users} color="blue" />
            <StatCard title="Sesiones programadas" value={sessions?.total ?? 0} icon={Calendar} color="green" />
            <StatCard title="TIs con alertas" value={
              tutorTIs?.items?.filter((t:TI) => (t.active_alerts ?? 0) > 0).length ?? 0
            } icon={AlertTriangle} color="red" />
          </div>

          {sessions?.items?.length > 0 && (
            <div className="card">
              <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                <Calendar className="w-4 h-4 text-primary-500" /> Próximas sesiones
              </h3>
              <div className="space-y-3">
                {sessions.items.slice(0,5).map((s:Session) => (
                  <div key={s.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    <div className="w-10 h-10 bg-primary-50 rounded-lg flex items-center justify-center flex-shrink-0">
                      <Clock className="w-5 h-5 text-primary-700" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium">{format(parseISO(s.scheduled_at),"d MMM, HH:mm",{locale:es})}</p>
                      <p className="text-xs text-gray-500">{s.modality} · {s.duration_minutes}min</p>
                    </div>
                    {s.meeting_url && (
                      <a href={s.meeting_url} target="_blank" rel="noopener noreferrer"
                        className="text-xs btn-primary py-1 px-3">Unirse</a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {tutorTIs?.items?.length > 0 && (
            <div className="card">
              <h3 className="font-semibold text-gray-800 mb-4">Mis estudiantes</h3>
              <div className="space-y-4">
                {tutorTIs.items.map((ti:TI) => (
                  <Link key={ti.id} to={`/ti/${ti.id}`} className="flex items-center gap-4 hover:bg-gray-50 p-2 rounded-lg -mx-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-800 truncate">{ti.title}</p>
                      <ProgressBar value={ti.progress_percent} size="sm" />
                    </div>
                    {(ti.active_alerts ?? 0) > 0 && (
                      <span className="badge-danger">{ti.active_alerts} alertas</span>
                    )}
                  </Link>
                ))}
              </div>
            </div>
          )}

          {(!tutorTIs?.items?.length) && (
            <div className="card text-center py-10">
              <Users className="w-10 h-10 text-gray-300 mx-auto mb-3"/>
              <p className="text-gray-500 font-medium">No tienes estudiantes asignados aún</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
