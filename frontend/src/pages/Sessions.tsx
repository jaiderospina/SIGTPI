import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useAuthStore } from "@/store/auth"
import { sessionApi, tiApi } from "@/services/api"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import EmptyState from "@/components/EmptyState"
import {
  Calendar, Video, MapPin, Clock, CheckCircle,
  XCircle, Plus, X, Check, AlertCircle, FileText
} from "lucide-react"
import { format, parseISO, addDays } from "date-fns"
import { es } from "date-fns/locale"
import clsx from "clsx"
import type { Session } from "@/types"
import axios from "axios"

const sessionSchema = z.object({
  ti_id:           z.string().uuid("Selecciona un TI"),
  tutor_id:        z.string().uuid(),
  student_id:      z.string().uuid(),
  scheduled_at:    z.string().min(1, "Selecciona fecha y hora"),
  duration_minutes:z.number().min(15).max(480),
  modality:        z.enum(["virtual","presential","hybrid"]),
  agenda:          z.string().optional(),
})
type SessionForm = z.infer<typeof sessionSchema>

const minutesSchema = z.object({
  topics_covered:      z.string().min(20, "Mínimo 20 caracteres"),
  agreements:          z.string().optional(),
  tutor_observations:  z.string().optional(),
  commitments:         z.array(z.object({
    description: z.string().min(5),
    deadline:    z.string().optional(),
  })).default([]),
})
type MinutesForm = z.infer<typeof minutesSchema>

const statusCfg: Record<string, { label:string; cls:string; icon:React.ElementType }> = {
  scheduled:   { label:"Programada",   cls:"badge-gray",    icon:Clock },
  confirmed:   { label:"Confirmada",   cls:"badge-active",  icon:CheckCircle },
  completed:   { label:"Realizada",    cls:"badge-active",  icon:CheckCircle },
  cancelled:   { label:"Cancelada",    cls:"badge-danger",  icon:XCircle },
  rescheduled: { label:"Reprogramada", cls:"badge-warning", icon:Clock },
}

export default function Sessions() {
  const { user, token, hasRole } = useAuthStore()
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [showMinutes, setShowMinutes] = useState<string|null>(null)
  const [newCommitment, setNewCommitment] = useState("")
  const [msg, setMsg] = useState<{type:"ok"|"err";text:string}|null>(null)

  const headers = { Authorization: `Bearer ${token}` }
  const flash = (type:"ok"|"err", text:string) => {
    setMsg({type,text}); setTimeout(()=>setMsg(null),4000)
  }

  const params = hasRole("EST") ? { student_id: user?.id }
    : hasRole("TUT") ? { tutor_id: user?.id } : {}

  const { data, isLoading } = useQuery({
    queryKey: ["sessions", params],
    queryFn: () => sessionApi.list(params).then(r => r.data),
  })

  const { data: myTIs } = useQuery({
    queryKey: ["tis-for-session"],
    queryFn: () => {
      const params: Record<string,unknown> = hasRole("EST") ? { student_id: user?.id }
        : hasRole("TUT") ? { tutor_id: user?.id }
        : { page_size: 100 } // ADM/COO/DIR see all TIs
      return tiApi.list(params).then(r => r.data)
    },
  })

  const sessionForm = useForm<SessionForm>({ resolver: zodResolver(sessionSchema), defaultValues: {
    duration_minutes: 60, modality: "virtual"
  }})

  const minutesForm = useForm<MinutesForm>({ resolver: zodResolver(minutesSchema), defaultValues: {
    commitments: []
  }})

  const createMut = useMutation({
    mutationFn: (d: SessionForm) => sessionApi.create({
      ...d, scheduled_at: new Date(d.scheduled_at).toISOString()
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sessions"] })
      setShowCreate(false); sessionForm.reset()
      flash("ok","Sesión programada. Se generó sala virtual automáticamente.")
    },
    onError: (e:any) => flash("err", e.response?.data?.detail ?? "Error al programar sesión."),
  })

  const completeMut = useMutation({
    mutationFn: (id:string) => sessionApi.complete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["sessions"] }); flash("ok","Sesión marcada como completada.") },
  })

  const cancelMut = useMutation({
    mutationFn: (id:string) => sessionApi.cancel(id, "Cancelada desde la plataforma."),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["sessions"] }); flash("ok","Sesión cancelada.") },
  })

  const minutesMut = useMutation({
    mutationFn: ({ sessionId, data }: { sessionId:string; data:MinutesForm }) =>
      sessionApi.createMinutes({ session_id: sessionId, ...data }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sessions"] })
      setShowMinutes(null); minutesForm.reset()
      flash("ok","Acta de sesión registrada exitosamente.")
    },
    onError: (e:any) => flash("err", e.response?.data?.detail ?? "Error al registrar acta."),
  })

  const addCommitment = () => {
    if (!newCommitment.trim()) return
    const current = minutesForm.getValues("commitments") ?? []
    minutesForm.setValue("commitments", [...current, { description: newCommitment }])
    setNewCommitment("")
  }

  const tis = myTIs?.items ?? []
  const sessions = data?.items ?? []

  // Auto-fill tutor/student from selected TI
  const onTIChange = (tiId:string) => {
    const ti = tis.find((t:any) => t.id === tiId)
    if (ti) {
      sessionForm.setValue("tutor_id", ti.tutor_id)
      sessionForm.setValue("student_id", ti.student_id)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Sesiones de Tutoría</h1>
          <p className="text-sm text-gray-500 mt-0.5">{sessions.length} sesión{sessions.length!==1?"es":""}</p>
        </div>
        {hasRole("TUT","EST","COO","ADM") && (
          <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2 text-sm">
            <Plus className="w-4 h-4"/> Programar sesión
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

      {isLoading && <div className="space-y-2">{[1,2,3].map(i=><div key={i} className="h-20 bg-gray-100 rounded-xl animate-pulse"/>)}</div>}

      {!isLoading && sessions.length===0 && (
        <EmptyState icon={Calendar} title="Sin sesiones"
          description="Programa la primera sesión de tutoría."
          action={<button onClick={()=>setShowCreate(true)} className="btn-primary text-sm flex items-center gap-2"><Plus className="w-4 h-4"/>Programar sesión</button>}/>
      )}

      <div className="space-y-3">
        {sessions.map((s:Session & {has_minutes?:boolean}) => {
          const cfg = statusCfg[s.status] ?? { label:s.status, cls:"badge-gray", icon:Clock }
          const StatusIcon = cfg.icon
          const isPast = new Date(s.scheduled_at) < new Date()
          return (
            <div key={s.id} className="card">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 bg-primary-50 rounded-xl flex flex-col items-center justify-center flex-shrink-0">
                  <p className="text-xl font-bold text-primary-700 leading-none">
                    {format(parseISO(s.scheduled_at),"d")}
                  </p>
                  <p className="text-xs text-primary-500 uppercase">
                    {format(parseISO(s.scheduled_at),"MMM",{locale:es})}
                  </p>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span className={cfg.cls}><StatusIcon className="w-3 h-3 inline mr-1"/>{cfg.label}</span>
                    {s.has_minutes && <span className="badge-gray"><FileText className="w-3 h-3 inline mr-1"/>Con acta</span>}
                  </div>
                  <div className="flex items-center gap-3 text-xs text-gray-500">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3"/>
                      {format(parseISO(s.scheduled_at),"HH:mm")} · {s.duration_minutes}min
                    </span>
                    <span className="flex items-center gap-1">
                      {s.modality==="virtual" ? <Video className="w-3 h-3"/> : <MapPin className="w-3 h-3"/>}
                      {s.modality==="virtual" ? "Virtual" : "Presencial"}
                    </span>
                  </div>
                  {s.agenda && <p className="text-xs text-gray-400 mt-1 truncate">{s.agenda}</p>}
                </div>
                <div className="flex flex-col gap-1.5 flex-shrink-0">
                  {s.meeting_url && s.status!=="cancelled" && (
                    <a href={s.meeting_url} target="_blank" rel="noopener noreferrer"
                      className="btn-primary text-xs py-1.5 px-3 flex items-center gap-1.5">
                      <Video className="w-3.5 h-3.5"/> Unirse
                    </a>
                  )}
                  {hasRole("TUT") && s.status==="scheduled" && isPast && (
                    <button onClick={() => completeMut.mutate(s.id)}
                      className="btn-secondary text-xs py-1.5 px-3 text-green-700 border-green-200">
                      Marcar completa
                    </button>
                  )}
                  {hasRole("TUT") && s.status==="completed" && !s.has_minutes && (
                    <button onClick={() => setShowMinutes(s.id)}
                      className="btn-secondary text-xs py-1.5 px-3 flex items-center gap-1.5">
                      <FileText className="w-3.5 h-3.5"/> Registrar acta
                    </button>
                  )}
                  {(s.status==="scheduled"||s.status==="confirmed") && (
                    <button onClick={() => cancelMut.mutate(s.id)}
                      className="text-xs text-gray-400 hover:text-red-500 text-center">
                      Cancelar
                    </button>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Create session modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-gray-100 sticky top-0 bg-white">
              <h2 className="font-bold text-gray-900">Programar sesión de tutoría</h2>
              <button onClick={()=>{setShowCreate(false);sessionForm.reset()}}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg">
                <X className="w-5 h-5"/>
              </button>
            </div>
            <form onSubmit={sessionForm.handleSubmit(d=>createMut.mutate(d))} className="p-6 space-y-4">
              <div>
                <label className="label">Trabajo de Investigación *</label>
                <select {...sessionForm.register("ti_id")} className="input"
                  onChange={e => { sessionForm.register("ti_id").onChange(e); onTIChange(e.target.value) }}>
                  <option value="">Selecciona el TI...</option>
                  {tis.map((t:any) => <option key={t.id} value={t.id}>{t.title}</option>)}
                </select>
                {sessionForm.formState.errors.ti_id && <p className="text-xs text-red-500 mt-1">{sessionForm.formState.errors.ti_id.message}</p>}
              </div>
              <input type="hidden" {...sessionForm.register("tutor_id")}/>
              <input type="hidden" {...sessionForm.register("student_id")}/>
              <div>
                <label className="label">Fecha y hora *</label>
                <input {...sessionForm.register("scheduled_at")} type="datetime-local"
                  min={new Date().toISOString().slice(0,16)} className="input"/>
                {sessionForm.formState.errors.scheduled_at && <p className="text-xs text-red-500 mt-1">{sessionForm.formState.errors.scheduled_at.message}</p>}
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Duración (minutos)</label>
                  <input {...sessionForm.register("duration_minutes",{valueAsNumber:true})}
                    type="number" min="15" max="480" step="15" className="input"/>
                </div>
                <div>
                  <label className="label">Modalidad</label>
                  <select {...sessionForm.register("modality")} className="input">
                    <option value="virtual">Virtual (Jitsi)</option>
                    <option value="presential">Presencial</option>
                    <option value="hybrid">Híbrida</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="label">Agenda (opcional)</label>
                <textarea {...sessionForm.register("agenda")} rows={2} className="input resize-none"
                  placeholder="Temas a tratar, objetivos de la sesión..."/>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={()=>{setShowCreate(false);sessionForm.reset()}} className="btn-secondary flex-1">Cancelar</button>
                <button type="submit" disabled={createMut.isPending} className="btn-primary flex-1">
                  {createMut.isPending ? "Programando..." : "Programar sesión"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Minutes modal */}
      {showMinutes && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-gray-100 sticky top-0 bg-white">
              <h2 className="font-bold text-gray-900">Registrar acta de sesión</h2>
              <button onClick={()=>{setShowMinutes(null);minutesForm.reset()}}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg">
                <X className="w-5 h-5"/>
              </button>
            </div>
            <form onSubmit={minutesForm.handleSubmit(d=>minutesMut.mutate({sessionId:showMinutes,data:d}))}
              className="p-6 space-y-4">
              <div>
                <label className="label">Temas tratados *</label>
                <textarea {...minutesForm.register("topics_covered")} rows={4} className="input resize-none"
                  placeholder="Describe los temas discutidos, avances revisados, metodología analizada..."/>
                {minutesForm.formState.errors.topics_covered && <p className="text-xs text-red-500 mt-1">{minutesForm.formState.errors.topics_covered.message}</p>}
              </div>
              <div>
                <label className="label">Acuerdos y conclusiones</label>
                <textarea {...minutesForm.register("agreements")} rows={3} className="input resize-none"
                  placeholder="Acuerdos alcanzados, decisiones tomadas..."/>
              </div>
              <div>
                <label className="label">Compromisos del estudiante</label>
                <div className="space-y-2 mb-2">
                  {(minutesForm.watch("commitments") ?? []).map((c,i) => (
                    <div key={i} className="flex items-center gap-2 p-2.5 bg-blue-50 rounded-lg">
                      <Check className="w-3.5 h-3.5 text-blue-600 flex-shrink-0"/>
                      <p className="text-sm flex-1">{c.description}</p>
                      <button type="button"
                        onClick={() => minutesForm.setValue("commitments",
                          (minutesForm.getValues("commitments")||[]).filter((_,j)=>j!==i))}
                        className="text-gray-400 hover:text-red-500">
                        <X className="w-3.5 h-3.5"/>
                      </button>
                    </div>
                  ))}
                </div>
                <div className="flex gap-2">
                  <input value={newCommitment} onChange={e=>setNewCommitment(e.target.value)}
                    placeholder="Nuevo compromiso..." className="input flex-1 text-sm"
                    onKeyDown={e => { if(e.key==="Enter"){e.preventDefault();addCommitment()} }}/>
                  <button type="button" onClick={addCommitment} className="btn-secondary text-sm px-3">
                    <Plus className="w-4 h-4"/>
                  </button>
                </div>
              </div>
              <div>
                <label className="label">Observaciones del tutor</label>
                <textarea {...minutesForm.register("tutor_observations")} rows={2} className="input resize-none"
                  placeholder="Recomendaciones, evaluación del avance, próximos pasos..."/>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={()=>{setShowMinutes(null);minutesForm.reset()}} className="btn-secondary flex-1">Cancelar</button>
                <button type="submit" disabled={minutesMut.isPending} className="btn-primary flex-1">
                  {minutesMut.isPending ? "Guardando..." : "Guardar acta"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
