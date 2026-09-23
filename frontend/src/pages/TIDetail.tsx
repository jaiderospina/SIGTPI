import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useParams, Link } from "react-router-dom"
import { tiApi } from "@/services/api"
import { useAuthStore } from "@/store/auth"
import ProgressBar from "@/components/ProgressBar"
import AlertBadge from "@/components/AlertBadge"
import { format, parseISO } from "date-fns"
import { es } from "date-fns/locale"
import { CheckCircle, Clock, AlertTriangle, FileText, Zap } from "lucide-react"
import clsx from "clsx"
import type { Milestone, Advance, Alert } from "@/types"

const milestoneColor: Record<string, string> = {
  approved: "bg-success text-white", pending: "bg-gray-200 text-gray-600",
  in_review: "bg-warning-light text-warning", rejected: "bg-danger-light text-danger",
  overdue: "bg-red-100 text-red-700",
}

export default function TIDetail() {
  const { id } = useParams<{ id: string }>()
  const { hasRole } = useAuthStore()
  const qc = useQueryClient()

  const { data: ti, isLoading } = useQuery({
    queryKey: ["ti", id],
    queryFn: () => tiApi.get(id!).then(r => r.data),
  })

  const delayMut = useMutation({
    mutationFn: () => tiApi.alerts(),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["ti", id] }),
  })

  if (isLoading) return <div className="max-w-4xl mx-auto space-y-4">{[1,2,3].map(i=><div key={i} className="card h-32 animate-pulse bg-gray-100"/>)}</div>
  if (!ti) return <p className="text-center text-gray-500 mt-16">TI no encontrado</p>

  const activeAlerts = ti.alerts?.filter((a: Alert) => a.status === "active") ?? []

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="card">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-xl font-bold text-gray-900">{ti.title}</h1>
            <p className="text-sm text-gray-500 mt-1">{ti.knowledge_area}</p>
          </div>
          <span className="badge-active">{ti.status}</span>
        </div>
        <ProgressBar value={ti.progress_percent} label="Avance general" />
        {ti.estimated_defense && (
          <p className="text-xs text-gray-400 mt-3">
            Defensa estimada: {format(parseISO(ti.estimated_defense), "d MMM yyyy", { locale: es })}
          </p>
        )}
        <div className="flex gap-2 mt-4">
          <Link to={`/ti/${ti.id}/documents`}
            className="btn-secondary flex items-center gap-2 text-sm">
            <FileText className="w-4 h-4" /> Repositorio documental
          </Link>
          {hasRole("ADM","COO") && (
          <button onClick={() => delayMut.mutate()} disabled={delayMut.isPending}
            className="btn-secondary flex items-center gap-2 mt-4 text-sm">
            <Zap className="w-4 h-4" />
            {delayMut.isPending ? "Verificando..." : "Verificar retrasos"}
          </button>
          )}
        </div>
      </div>

      {/* Alerts */}
      {activeAlerts.length > 0 && (
        <div className="card border-l-4 border-danger">
          <h3 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-danger" /> Alertas activas
          </h3>
          <div className="space-y-2">
            {activeAlerts.map((a: Alert) => (
              <div key={a.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                <AlertBadge level={a.level} />
                <p className="text-sm text-gray-700 flex-1">{a.reason}</p>
                <p className="text-xs text-gray-400">
                  {format(parseISO(a.detected_at), "d MMM", { locale: es })}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Milestones */}
      <div className="card">
        <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-primary-500" /> Cronograma de hitos
        </h3>
        <div className="space-y-3">
          {ti.milestones?.map((m: Milestone) => (
            <div key={m.id} className="flex items-center gap-3">
              <div className={clsx("w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold",
                milestoneColor[m.status] ?? "bg-gray-100 text-gray-600")}>
                {m.status === "approved" ? <CheckCircle className="w-4 h-4" /> : <Clock className="w-4 h-4" />}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-medium text-gray-800">{m.name}</p>
                  {m.is_critical && <span className="text-xs bg-red-100 text-red-600 px-1.5 py-0.5 rounded font-medium">Crítico</span>}
                </div>
                <p className="text-xs text-gray-400">
                  Planificado: {format(parseISO(m.planned_date), "d MMM yyyy", { locale: es })}
                  {m.actual_date && ` · Real: ${format(parseISO(m.actual_date), "d MMM yyyy", { locale: es })}`}
                </p>
              </div>
              <div className="text-right flex-shrink-0">
                <span className={clsx("text-xs font-medium px-2 py-0.5 rounded-full", milestoneColor[m.status])}>
                  {m.status}
                </span>
                <p className="text-xs text-gray-400 mt-0.5">{m.weight_percent}%</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Advances */}
      {ti.advances?.length > 0 && (
        <div className="card">
          <h3 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <FileText className="w-4 h-4 text-primary-500" /> Registro de avances
          </h3>
          <div className="space-y-4">
            {ti.advances.map((a: Advance) => (
              <div key={a.id} className="border-l-2 border-primary-500/30 pl-4">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-bold text-primary-700 bg-primary-50 px-2 py-0.5 rounded">{a.period}</span>
                  <span className="text-xs text-gray-400">{format(parseISO(a.registered_at), "d MMM yyyy", { locale: es })}</span>
                  <span className="text-xs font-medium text-success ml-auto">{a.progress_percent}%</span>
                </div>
                <p className="text-sm text-gray-700">{a.activities_done}</p>
                {a.obstacles && <p className="text-xs text-danger mt-1">⚠ {a.obstacles}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
