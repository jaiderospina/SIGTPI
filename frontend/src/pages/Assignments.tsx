import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useAuthStore } from "@/store/auth"
import { tutoringApi, academicApi } from "@/services/academic"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import EmptyState from "@/components/EmptyState"
import {
  Users, Plus, X, Check, Clock, ChevronRight,
  UserCheck, AlertCircle, BookOpen, ArrowRight
} from "lucide-react"
import clsx from "clsx"

const statusCfg: Record<string, { label: string; cls: string }> = {
  pending:  { label: "Pendiente",  cls: "badge-warning" },
  accepted: { label: "Aceptada",   cls: "badge-active"  },
  active:   { label: "Activa",     cls: "badge-active"  },
  rejected: { label: "Rechazada",  cls: "badge-danger"  },
  closed:   { label: "Cerrada",    cls: "badge-gray"    },
}

const AREAS = [
  "Ciberseguridad y Ciberdefensa",
  "Redes y Telecomunicaciones",
  "Ciencia de Datos e Inteligencia Artificial",
  "Ingeniería de Software",
  "Gestión de Sistemas de Información",
]

const requestSchema = z.object({
  student_id:       z.string().uuid("Selecciona un estudiante"),
  tutor_id:         z.string().uuid("Selecciona un tutor"),
  program_id:       z.string().uuid("Selecciona un programa"),
  research_area:    z.string().min(5, "Selecciona o escribe el área"),
  preliminary_title:z.string().min(10, "Mínimo 10 caracteres"),
  notes:            z.string().optional(),
})
type RequestForm = z.infer<typeof requestSchema>

const rejectSchema = z.object({
  rejection_reason: z.string().min(10, "Mínimo 10 caracteres"),
})

export default function Assignments() {
  const { user, hasRole } = useAuthStore()
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [rejectId, setRejectId] = useState<string|null>(null)
  const [msg, setMsg] = useState<{type:"ok"|"err";text:string}|null>(null)

  const flash = (type:"ok"|"err", text:string) => {
    setMsg({type,text})
    setTimeout(()=>setMsg(null),4000)
  }

  const params = hasRole("TUT") ? { tutor_id: user?.id }
    : hasRole("EST") ? { student_id: user?.id } : {}

  const { data, isLoading } = useQuery({
    queryKey: ["assignments", params],
    queryFn: () => tutoringApi.list(params),
  })

  const { data: programs } = useQuery({
    queryKey: ["programs"],
    queryFn: () => academicApi.programs(),
    enabled: hasRole("COO","DIR","ADM"),
  })

  const { data: users } = useQuery({
    queryKey: ["users-dir"],
    queryFn: () => import("axios").then(({default:ax}) =>
      ax.get("/api/users/users", {
        headers: { Authorization: `Bearer ${useAuthStore.getState().token}` },
        params: { page_size: 100 }
      }).then(r => r.data.items)
    ),
    enabled: hasRole("COO","DIR","ADM"),
  })

  const form = useForm<RequestForm>({ resolver: zodResolver(requestSchema) })
  const rejectForm = useForm<z.infer<typeof rejectSchema>>({ resolver: zodResolver(rejectSchema) })

  const createMut = useMutation({
    mutationFn: (d: RequestForm) => tutoringApi.create({ ...d, assigned_by: user?.id }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["assignments"] })
      setShowForm(false)
      form.reset()
      flash("ok","Solicitud de tutoría creada. El tutor recibirá notificación.")
    },
    onError: (e:any) => flash("err", e.response?.data?.detail ?? "Error al crear solicitud."),
  })

  const respondMut = useMutation({
    mutationFn: ({ id, accept, reason }: { id:string; accept:boolean; reason?:string }) =>
      tutoringApi.respond(id, { accept, rejection_reason: reason }),
    onSuccess: (_,vars) => {
      qc.invalidateQueries({ queryKey: ["assignments"] })
      setRejectId(null)
      rejectForm.reset()
      flash("ok", vars.accept ? "Tutoría aceptada exitosamente." : "Tutoría rechazada.")
    },
    onError: (e:any) => flash("err", e.response?.data?.detail ?? "Error al responder."),
  })

  const tutors = users?.filter((u:any) => u.role_codes?.includes("TUT")) ?? []
  const students = users?.filter((u:any) => u.role_codes?.includes("EST")) ?? []
  const items = data?.items ?? data ?? []

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Asignaciones de Tutoría</h1>
          <p className="text-sm text-gray-500 mt-0.5">{items.length} registro{items.length!==1?"s":""}</p>
        </div>
        {hasRole("COO","DIR","ADM") && (
          <button onClick={() => setShowForm(true)} className="btn-primary flex items-center gap-2 text-sm">
            <Plus className="w-4 h-4"/> Nueva asignación
          </button>
        )}
      </div>

      {msg && (
        <div className={clsx("flex items-center gap-2 p-3 rounded-lg mb-4 text-sm",
          msg.type==="ok" ? "bg-green-50 text-green-700 border border-green-200"
                          : "bg-red-50 text-red-700 border border-red-200")}>
          {msg.type==="ok" ? <Check className="w-4 h-4"/> : <AlertCircle className="w-4 h-4"/>}
          {msg.text}
        </div>
      )}

      {/* Pending actions for TUT */}
      {hasRole("TUT") && items.filter((a:any)=>a.status==="pending").length > 0 && (
        <div className="card border-l-4 border-warning mb-4">
          <p className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <Clock className="w-4 h-4 text-warning"/> Solicitudes pendientes de respuesta
          </p>
          {items.filter((a:any)=>a.status==="pending").map((a:any) => (
            <div key={a.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg mb-2">
              <div>
                <p className="text-sm font-medium text-gray-800">{a.preliminary_title ?? a.research_area}</p>
                <p className="text-xs text-gray-500">{a.research_area}</p>
              </div>
              <div className="flex gap-2">
                <button onClick={() => setRejectId(a.id)}
                  className="flex items-center gap-1 text-xs btn-secondary py-1.5 px-3 text-red-600 border-red-200">
                  <X className="w-3 h-3"/> Rechazar
                </button>
                <button onClick={() => respondMut.mutate({ id: a.id, accept: true })}
                  className="flex items-center gap-1 text-xs btn-primary py-1.5 px-3">
                  <Check className="w-3 h-3"/> Aceptar
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {isLoading && <div className="space-y-2">{[1,2,3].map(i=><div key={i} className="h-16 bg-gray-100 rounded-xl animate-pulse"/>)}</div>}

      {!isLoading && items.length===0 && (
        <EmptyState icon={Users} title="Sin asignaciones"
          description={hasRole("COO","DIR","ADM") ? "Crea la primera asignación de tutoría." : "No tienes asignaciones de tutoría aún."}/>
      )}

      <div className="space-y-3">
        {items.filter((a:any)=>a.status!=="pending" || !hasRole("TUT")).map((a:any) => {
          const cfg = statusCfg[a.status] ?? { label: a.status, cls: "badge-gray" }
          return (
            <div key={a.id} className="card flex items-center gap-4">
              <div className="w-10 h-10 bg-primary-50 rounded-xl flex items-center justify-center flex-shrink-0">
                <UserCheck className="w-5 h-5 text-primary-700"/>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <p className="font-medium text-gray-900 text-sm truncate">
                    {a.preliminary_title ?? a.research_area}
                  </p>
                  <span className={cfg.cls}>{cfg.label}</span>
                </div>
                <p className="text-xs text-gray-500">{a.research_area}</p>
                {a.rejection_reason && (
                  <p className="text-xs text-red-500 mt-1">Motivo: {a.rejection_reason}</p>
                )}
              </div>
              <ChevronRight className="w-4 h-4 text-gray-300 flex-shrink-0"/>
            </div>
          )
        })}
      </div>

      {/* New Assignment Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-gray-100 sticky top-0 bg-white">
              <h2 className="font-bold text-gray-900">Nueva asignación de tutoría</h2>
              <button onClick={() => { setShowForm(false); form.reset() }}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg">
                <X className="w-5 h-5"/>
              </button>
            </div>
            <form onSubmit={form.handleSubmit(d => createMut.mutate(d))} className="p-6 space-y-4">
              <div>
                <label className="label">Estudiante *</label>
                <select {...form.register("student_id")} className="input">
                  <option value="">Selecciona estudiante...</option>
                  {students.map((s:any) => (
                    <option key={s.id} value={s.id}>{s.full_name} — {s.email}</option>
                  ))}
                </select>
                {form.formState.errors.student_id && <p className="text-xs text-red-500 mt-1">{form.formState.errors.student_id.message}</p>}
              </div>
              <div>
                <label className="label">Tutor *</label>
                <select {...form.register("tutor_id")} className="input">
                  <option value="">Selecciona tutor...</option>
                  {tutors.map((t:any) => (
                    <option key={t.id} value={t.id}>{t.full_name} — {t.area_of_expertise ?? t.email}</option>
                  ))}
                </select>
                {form.formState.errors.tutor_id && <p className="text-xs text-red-500 mt-1">{form.formState.errors.tutor_id.message}</p>}
              </div>
              <div>
                <label className="label">Programa *</label>
                <select {...form.register("program_id")} className="input">
                  <option value="">Selecciona programa...</option>
                  {programs?.map((p:any) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
                {form.formState.errors.program_id && <p className="text-xs text-red-500 mt-1">{form.formState.errors.program_id.message}</p>}
              </div>
              <div>
                <label className="label">Área de investigación *</label>
                <select {...form.register("research_area")} className="input">
                  <option value="">Selecciona área...</option>
                  {AREAS.map(a => <option key={a} value={a}>{a}</option>)}
                </select>
                {form.formState.errors.research_area && <p className="text-xs text-red-500 mt-1">{form.formState.errors.research_area.message}</p>}
              </div>
              <div>
                <label className="label">Título preliminar del TI *</label>
                <input {...form.register("preliminary_title")} className="input"
                  placeholder="Título tentativo de la investigación"/>
                {form.formState.errors.preliminary_title && <p className="text-xs text-red-500 mt-1">{form.formState.errors.preliminary_title.message}</p>}
              </div>
              <div>
                <label className="label">Notas adicionales</label>
                <textarea {...form.register("notes")} rows={3} className="input resize-none"
                  placeholder="Observaciones, justificación de la selección del tutor, etc."/>
              </div>
              {createMut.isError && (
                <p className="text-xs text-red-600 bg-red-50 p-2 rounded-lg">
                  {(createMut.error as any)?.response?.data?.detail ?? "Error al crear asignación."}
                </p>
              )}
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => { setShowForm(false); form.reset() }}
                  className="btn-secondary flex-1">Cancelar</button>
                <button type="submit" disabled={createMut.isPending} className="btn-primary flex-1">
                  {createMut.isPending ? "Creando..." : "Crear asignación"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reject Modal */}
      {rejectId && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
            <h2 className="font-bold text-gray-900 mb-4">Rechazar asignación</h2>
            <div className="space-y-4">
              <div>
                <label className="label">Motivo del rechazo *</label>
                <textarea {...rejectForm.register("rejection_reason")} rows={4}
                  className="input resize-none"
                  placeholder="Explica el motivo: carga académica, área de especialización incompatible, etc."/>
                {rejectForm.formState.errors.rejection_reason && (
                  <p className="text-xs text-red-500 mt-1">{rejectForm.formState.errors.rejection_reason.message}</p>
                )}
              </div>
              <div className="flex gap-3">
                <button onClick={() => { setRejectId(null); rejectForm.reset() }}
                  className="btn-secondary flex-1">Cancelar</button>
                <button
                  onClick={() => rejectForm.handleSubmit(d =>
                    respondMut.mutate({ id: rejectId, accept: false, reason: d.rejection_reason })
                  )()}
                  disabled={respondMut.isPending}
                  className="btn-danger flex-1">
                  {respondMut.isPending ? "Rechazando..." : "Confirmar rechazo"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
