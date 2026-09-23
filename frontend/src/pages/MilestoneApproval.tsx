import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useAuthStore } from "@/store/auth"
import { tiApi } from "@/services/api"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Link } from "react-router-dom"
import ProgressBar from "@/components/ProgressBar"
import EmptyState from "@/components/EmptyState"
import {
  CheckCircle, Clock, X, Check,
  AlertTriangle, ChevronRight, ClipboardList
} from "lucide-react"
import { format, parseISO } from "date-fns"
import { es } from "date-fns/locale"
import clsx from "clsx"
import axios from "axios"

const schema = z.object({
  approved:        z.boolean(),
  rejection_notes: z.string().optional(),
})

const statusColor: Record<string,string> = {
  pending:   "bg-yellow-100 text-yellow-700 border-yellow-200",
  in_review: "bg-blue-100 text-blue-700 border-blue-200",
  approved:  "bg-green-100 text-green-700 border-green-200",
  rejected:  "bg-red-100 text-red-700 border-red-200",
  overdue:   "bg-orange-100 text-orange-700 border-orange-200",
}

export default function MilestoneApproval() {
  const { user, token, hasRole } = useAuthStore()
  const qc = useQueryClient()
  const [selected, setSelected] = useState<{tiId:string;milestoneId:string;name:string}|null>(null)
  const [msg, setMsg] = useState<{type:"ok"|"err";text:string}|null>(null)

  const form = useForm<z.infer<typeof schema>>({ resolver: zodResolver(schema) })

  const params: Record<string,unknown> = hasRole("EST") ? { student_id: user?.id }
    : hasRole("TUT") ? { tutor_id: user?.id }
    : {}  // ADM/COO/DIR see all

  const { data, isLoading } = useQuery({
    queryKey: ["tis-milestones", params],
    queryFn: () => tiApi.list(params).then(r => r.data),
  })

  const approveMut = useMutation({
    mutationFn: ({ milestoneId, approved, rejection_notes }:
      { milestoneId:string; approved:boolean; rejection_notes?:string }) =>
      axios.post(
        `/api/ti/ti/milestones/${milestoneId}/approve`,
        { approved, rejection_notes },
        { headers: { Authorization: `Bearer ${token}` } }
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tis-milestones"] })
      setSelected(null)
      form.reset()
      setMsg({ type:"ok", text:"Hito actualizado correctamente." })
      setTimeout(() => setMsg(null), 4000)
    },
    onError: (e:any) => setMsg({ type:"err", text: e.response?.data?.detail ?? "Error." }),
  })

  const items = data?.items ?? []
  const pendingMilestones = items.flatMap((ti:any) =>
    (ti.milestones ?? [])
      .filter((m:any) => m.status === "pending" || m.status === "in_review")
      .map((m:any) => ({ ...m, tiId: ti.id, tiTitle: ti.title }))
  )

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-900">Hitos y Cronograma</h1>
        <p className="text-sm text-gray-500 mt-0.5">Seguimiento y aprobación de hitos del cronograma</p>
      </div>

      {msg && (
        <div className={clsx("flex items-center gap-2 p-3 rounded-lg mb-4 text-sm",
          msg.type==="ok" ? "bg-green-50 text-green-700 border border-green-200"
                          : "bg-red-50 text-red-700 border border-red-200")}>
          {msg.type==="ok" ? <Check className="w-4 h-4"/> : <AlertTriangle className="w-4 h-4"/>}
          {msg.text}
        </div>
      )}

      {/* Pending approvals for TUT */}
      {hasRole("TUT","COO","DIR") && pendingMilestones.length > 0 && (
        <div className="card border-l-4 border-primary-500 mb-6">
          <p className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Clock className="w-4 h-4 text-primary-500"/>
            {pendingMilestones.length} hito{pendingMilestones.length>1?"s":""} pendiente{pendingMilestones.length>1?"s":""} de revisión
          </p>
          <div className="space-y-2">
            {pendingMilestones.map((m:any) => (
              <div key={m.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800">{m.name}</p>
                  <p className="text-xs text-gray-500 truncate">{m.tiTitle}</p>
                  <p className="text-xs text-gray-400">
                    Planificado: {format(parseISO(m.planned_date), "d MMM yyyy", { locale: es })}
                    {m.is_critical && <span className="ml-2 text-red-500 font-medium">● Crítico</span>}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={clsx("text-xs px-2 py-0.5 rounded-full border", statusColor[m.status])}>
                    {m.status}
                  </span>
                  <button
                    onClick={() => setSelected({ tiId:m.tiId, milestoneId:m.id, name:m.name })}
                    className="btn-primary text-xs py-1.5 px-3">
                    Revisar
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {isLoading && <div className="space-y-3">{[1,2].map(i=><div key={i} className="h-40 bg-gray-100 rounded-xl animate-pulse"/>)}</div>}

      {!isLoading && items.length === 0 && (
        <EmptyState icon={ClipboardList} title="Sin TIs asignados"
          description="Los hitos aparecerán cuando tengas trabajos de investigación activos."/>
      )}

      {/* TI milestone list */}
      <div className="space-y-4">
        {items.map((ti:any) => (
          <div key={ti.id} className="card">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-semibold text-gray-900 text-sm">{ti.title}</h3>
                <p className="text-xs text-gray-500">{ti.knowledge_area}</p>
              </div>
              <Link to={`/ti/${ti.id}`} className="text-xs text-primary-600 hover:underline flex-shrink-0">
                Ver TI →
              </Link>
            </div>
            <ProgressBar value={ti.progress_percent} size="sm"/>
            <div className="mt-4 space-y-2">
              {(ti.milestones ?? []).map((m:any) => (
                <div key={m.id} className="flex items-center gap-3 p-2.5 rounded-lg bg-gray-50">
                  <div className={clsx("w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0",
                    m.status==="approved" ? "bg-green-100" : m.status==="rejected" ? "bg-red-100" : "bg-gray-200")}>
                    {m.status==="approved" ? <CheckCircle className="w-4 h-4 text-green-600"/> :
                     m.status==="rejected" ? <X className="w-4 h-4 text-red-500"/> :
                     <Clock className="w-4 h-4 text-gray-400"/>}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-gray-800">{m.name}</p>
                    <p className="text-xs text-gray-400">
                      {format(parseISO(m.planned_date), "d MMM yyyy", { locale: es })}
                      {m.is_critical && <span className="ml-1 text-red-500">● Crítico</span>}
                    </p>
                  </div>
                  <span className={clsx("text-xs px-2 py-0.5 rounded-full border flex-shrink-0", statusColor[m.status] ?? "bg-gray-100 text-gray-600 border-gray-200")}>
                    {m.status}
                  </span>
                  {hasRole("TUT","COO","DIR") && (m.status==="pending"||m.status==="in_review") && (
                    <button onClick={() => setSelected({ tiId:ti.id, milestoneId:m.id, name:m.name })}
                      className="text-xs text-primary-600 hover:underline flex-shrink-0">
                      Aprobar
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Approval Modal */}
      {selected && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
            <h2 className="font-bold text-gray-900 mb-1">Revisar hito</h2>
            <p className="text-sm text-gray-600 mb-5 p-3 bg-gray-50 rounded-lg">{selected.name}</p>
            <form onSubmit={form.handleSubmit(d => approveMut.mutate({ milestoneId: selected.milestoneId, ...d }))}
              className="space-y-4">
              <div>
                <label className="label">Resultado de la revisión *</label>
                <div className="grid grid-cols-2 gap-2">
                  <label className={clsx("flex items-center gap-2 p-3 border-2 rounded-xl cursor-pointer transition-colors",
                    form.watch("approved")===true ? "border-green-500 bg-green-50" : "border-gray-200 hover:border-gray-300")}>
                    <input type="radio" {...form.register("approved", { setValueAs: v => v === "true" })} value="true" className="hidden"/>
                    <CheckCircle className={clsx("w-5 h-5", form.watch("approved")===true ? "text-green-600" : "text-gray-300")}/>
                    <span className="text-sm font-medium">Aprobar</span>
                  </label>
                  <label className={clsx("flex items-center gap-2 p-3 border-2 rounded-xl cursor-pointer transition-colors",
                    form.watch("approved")===false ? "border-red-400 bg-red-50" : "border-gray-200 hover:border-gray-300")}>
                    <input type="radio" {...form.register("approved", { setValueAs: v => v === "true" })} value="false" className="hidden"/>
                    <X className={clsx("w-5 h-5", form.watch("approved")===false ? "text-red-500" : "text-gray-300")}/>
                    <span className="text-sm font-medium">Rechazar</span>
                  </label>
                </div>
              </div>
              {form.watch("approved") === false && (
                <div>
                  <label className="label">Motivo del rechazo</label>
                  <textarea {...form.register("rejection_notes")} rows={3}
                    className="input resize-none"
                    placeholder="Indica qué debe corregir el estudiante antes de aprobar este hito."/>
                </div>
              )}
              <div className="flex gap-3">
                <button type="button" onClick={() => { setSelected(null); form.reset() }}
                  className="btn-secondary flex-1">Cancelar</button>
                <button type="submit" disabled={approveMut.isPending
                  || form.watch("approved") === undefined}
                  className={clsx("flex-1", form.watch("approved") ? "btn-primary" : "btn-danger")}>
                  {approveMut.isPending ? "Guardando..." :
                   form.watch("approved") ? "Aprobar hito" : "Rechazar hito"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
