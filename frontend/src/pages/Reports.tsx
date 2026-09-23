import { useQuery } from "@tanstack/react-query"
import { reportApi } from "@/services/api"
import { useAuthStore } from "@/store/auth"
import StatCard from "@/components/StatCard"
import ProgressBar from "@/components/ProgressBar"
import {
  GraduationCap, Users, Clock, TrendingUp,
  AlertTriangle, BookOpen, BarChart2, CheckCircle
} from "lucide-react"
import clsx from "clsx"

export default function Reports() {
  const { hasRole } = useAuthStore()

  const { data: dash, isLoading } = useQuery({
    queryKey: ["report-dashboard"],
    queryFn: () => reportApi.dashboard().then(r => r.data),
    staleTime: 60_000,
  })

  const { data: tiKpi } = useQuery({
    queryKey: ["report-ti-status"],
    queryFn: () => reportApi.tiStatus().then(r => r.data),
    staleTime: 60_000,
  })

  if (isLoading) return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[1,2,3,4].map(i => <div key={i} className="h-28 bg-gray-100 rounded-xl animate-pulse"/>)}
      </div>
      <div className="h-64 bg-gray-100 rounded-xl animate-pulse"/>
    </div>
  )

  const stats = dash ?? {}
  const ti = tiKpi ?? {}

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900">Reportes y KPIs</h1>
        <p className="text-sm text-gray-500 mt-0.5">Panel ejecutivo del programa de postgrado</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="TIs Activos"
          value={stats.active_tis ?? ti.active ?? "—"}
          icon={BookOpen}
          color="blue"
        />
        <StatCard
          title="Estudiantes Activos"
          value={stats.active_students ?? "—"}
          icon={Users}
          color="green"
        />
        <StatCard
          title="Tutores Activos"
          value={stats.active_tutors ?? "—"}
          icon={GraduationCap}
          color="purple"
        />
        <StatCard
          title="TIs en Riesgo"
          value={stats.at_risk_tis ?? ti.at_risk ?? "—"}
          icon={AlertTriangle}
          color="red"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* TI Status breakdown */}
        <div className="card">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <BarChart2 className="w-4 h-4 text-primary-500"/> Estado de TIs
          </h3>
          <div className="space-y-3">
            {[
              { label:"En desarrollo",  key:"in_progress", color:"bg-blue-500" },
              { label:"En revisión",    key:"in_review",   color:"bg-yellow-500" },
              { label:"Aprobados",      key:"approved",    color:"bg-green-500" },
              { label:"En riesgo",      key:"at_risk",     color:"bg-red-500" },
            ].map(({ label, key, color }) => {
              const count = ti[key] ?? stats[key] ?? 0
              const total = (ti.total ?? stats.active_tis ?? 1) || 1
              const pct = Math.round((count / total) * 100)
              return (
                <div key={key}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">{label}</span>
                    <span className="font-semibold text-gray-800">{count}</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className={clsx("h-full rounded-full transition-all", color)}
                      style={{ width: `${pct}%` }}/>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* KPI Metrics */}
        <div className="card">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-primary-500"/> Métricas clave
          </h3>
          <div className="space-y-4">
            {[
              { label:"Tasa de titulación oportuna", value: stats.graduation_rate, suffix:"%" },
              { label:"Tiempo promedio titulación",  value: stats.avg_graduation_months, suffix:" meses" },
              { label:"Tasa de abandono",            value: stats.dropout_rate, suffix:"%" },
              { label:"Promedio sesiones/TI",        value: stats.avg_sessions_per_ti, suffix:"" },
            ].map(({ label, value, suffix }) => (
              <div key={label} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-600">{label}</span>
                <span className="text-lg font-bold text-primary-700">
                  {value != null ? `${typeof value === 'number' ? value.toFixed(1) : value}${suffix}` : "—"}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Tutor workload table */}
      {stats.tutor_workload?.length > 0 && (
        <div className="card">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Users className="w-4 h-4 text-primary-500"/> Carga de tutores
          </h3>
          <div className="space-y-2">
            {stats.tutor_workload.map((t: any) => (
              <div key={t.tutor_id} className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
                <div className="w-8 h-8 bg-primary-700 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
                  {(t.full_name ?? "T").split(" ").map((w:string)=>w[0]).join("").slice(0,2)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">{t.full_name}</p>
                  <ProgressBar value={Math.min((t.active_tis / 8) * 100, 100)} size="sm"/>
                </div>
                <div className="text-right flex-shrink-0">
                  <p className="text-sm font-bold text-gray-800">{t.active_tis}</p>
                  <p className="text-xs text-gray-400">TIs</p>
                </div>
                {t.active_tis >= 8 && (
                  <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full flex-shrink-0">
                    Sobrecargado
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Alerts summary */}
      {stats.active_alerts > 0 && (
        <div className="card border-l-4 border-red-400">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0"/>
            <div>
              <p className="font-semibold text-gray-800">
                {stats.active_alerts} alerta{stats.active_alerts !== 1 ? "s" : ""} activa{stats.active_alerts !== 1 ? "s" : ""}
              </p>
              <p className="text-sm text-gray-500">
                {stats.level3_alerts ?? 0} de nivel crítico (L3/L4) requieren atención inmediata.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* No data state */}
      {!dash && !tiKpi && (
        <div className="card text-center py-12">
          <BarChart2 className="w-12 h-12 text-gray-200 mx-auto mb-3"/>
          <p className="font-medium text-gray-500">Los reportes se generan a partir de los datos del sistema</p>
          <p className="text-sm text-gray-400 mt-1">Crea asignaciones, TIs y sesiones para ver métricas.</p>
        </div>
      )}
    </div>
  )
}
