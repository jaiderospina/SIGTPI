import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useAuthStore } from "@/store/auth"
import { tiApi } from "@/services/api"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Link, useNavigate } from "react-router-dom"
import ProgressBar from "@/components/ProgressBar"
import {
  TrendingUp, BookOpen, Check, AlertCircle,
  ChevronRight, Plus, ArrowLeft
} from "lucide-react"
import { format, parseISO } from "date-fns"
import { es } from "date-fns/locale"
import clsx from "clsx"

const schema = z.object({
  ti_id:            z.string().uuid(),
  period:           z.string().regex(/^\d{4}-[12]$/, "Formato: AAAA-1 o AAAA-2"),
  activities_done:  z.string().min(20, "Describe las actividades con detalle (mín. 20 caracteres)"),
  progress_percent: z.number().min(0).max(100),
  obstacles:        z.string().optional(),
  action_plan:      z.string().optional(),
})
type Form = z.infer<typeof schema>

const PERIODS = ["2024-1","2024-2","2025-1","2025-2","2026-1","2026-2"]

export default function AdvanceRegister() {
  const { user, hasRole } = useAuthStore()
  const qc = useQueryClient()
  const navigate = useNavigate()
  const [msg, setMsg] = useState<{type:"ok"|"err";text:string}|null>(null)
  const [selectedTI, setSelectedTI] = useState<string>("")
  const [showForm, setShowForm] = useState(false)

  const { data: tis, isLoading } = useQuery({
    queryKey: ["my-tis-advance"],
    queryFn: () => {
      const params = hasRole("EST") ? { student_id: user?.id }
        : hasRole("TUT") ? { tutor_id: user?.id }
        : {}
      return tiApi.list(params).then(r => r.data)
    },
  })

  const form = useForm<Form>({ resolver: zodResolver(schema) })

  const submitMut = useMutation({
    mutationFn: (d: Form) => tiApi.advance(d),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["my-tis-advance"] })
      qc.invalidateQueries({ queryKey: ["ti", selectedTI] })
      setShowForm(false)
      form.reset()
      setMsg({ type:"ok", text:"Avance registrado correctamente." })
      setTimeout(() => setMsg(null), 4000)
    },
    onError: (e:any) => setMsg({ type:"err", text: e.response?.data?.detail ?? "Error al registrar avance." }),
  })

  const openForm = (tiId: string) => {
    setSelectedTI(tiId)
    form.setValue("ti_id", tiId)
    setShowForm(true)
  }

  const items = tis?.items ?? []

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-900">Registro de Avances</h1>
        <p className="text-sm text-gray-500 mt-0.5">Registra el progreso periódico de tus investigaciones</p>
      </div>

      {msg && (
        <div className={clsx("flex items-center gap-2 p-3 rounded-lg mb-4 text-sm",
          msg.type==="ok" ? "bg-green-50 text-green-700 border border-green-200"
                          : "bg-red-50 text-red-700 border border-red-200")}>
          {msg.type==="ok" ? <Check className="w-4 h-4"/> : <AlertCircle className="w-4 h-4"/>}
          {msg.text}
        </div>
      )}

      {isLoading && <div className="space-y-3">{[1,2].map(i=><div key={i} className="h-32 bg-gray-100 rounded-xl animate-pulse"/>)}</div>}

      <div className="space-y-4">
        {items.map((ti:any) => (
          <div key={ti.id} className="card">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-gray-900 truncate">{ti.title}</h3>
                <p className="text-xs text-gray-500 mt-0.5">{ti.knowledge_area}</p>
              </div>
              <span className={clsx("text-xs px-2 py-0.5 rounded-full font-medium flex-shrink-0 ml-3",
                ti.status==="in_progress" ? "bg-blue-100 text-blue-700" :
                ti.status==="approved" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600")}>
                {ti.status}
              </span>
            </div>
            <ProgressBar value={ti.progress_percent} label="Avance actual"/>

            {/* Last advances */}
            {ti.advances?.length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-100">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Últimos avances</p>
                <div className="space-y-2">
                  {ti.advances.slice(-2).map((a:any) => (
                    <div key={a.id} className="flex items-center gap-3 p-2 bg-gray-50 rounded-lg">
                      <span className="text-xs font-bold text-primary-700 bg-primary-50 px-2 py-0.5 rounded">{a.period}</span>
                      <p className="text-xs text-gray-600 flex-1 truncate">{a.activities_done}</p>
                      <span className="text-xs font-semibold text-success">{a.progress_percent}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex gap-2 mt-4">
              {hasRole("EST") && ti.status !== "approved" && (
                <button onClick={() => openForm(ti.id)} className="btn-primary text-sm flex items-center gap-2">
                  <Plus className="w-4 h-4"/> Registrar avance
                </button>
              )}
              <Link to={`/ti/${ti.id}`} className="btn-secondary text-sm flex items-center gap-1.5">
                Ver TI completo <ChevronRight className="w-3.5 h-3.5"/>
              </Link>
            </div>
          </div>
        ))}
      </div>

      {/* Advance Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-gray-100 sticky top-0 bg-white">
              <h2 className="font-bold text-gray-900">Registrar avance periódico</h2>
              <button onClick={() => { setShowForm(false); form.reset() }}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg">
                <span className="w-5 h-5">✕</span>
              </button>
            </div>
            <form onSubmit={form.handleSubmit(d => submitMut.mutate(d))} className="p-6 space-y-4">
              <input type="hidden" {...form.register("ti_id")}/>
              <div>
                <label className="label">Período académico *</label>
                <select {...form.register("period")} className="input">
                  <option value="">Selecciona el período...</option>
                  {PERIODS.map(p => <option key={p} value={p}>{p}</option>)}
                </select>
                {form.formState.errors.period && <p className="text-xs text-red-500 mt-1">{form.formState.errors.period.message}</p>}
              </div>
              <div>
                <label className="label">Actividades realizadas *</label>
                <textarea {...form.register("activities_done")} rows={5} className="input resize-none"
                  placeholder="Describe detalladamente las actividades de investigación realizadas en este período: revisión de literatura, experimentos, análisis de datos, redacción, etc."/>
                {form.formState.errors.activities_done && <p className="text-xs text-red-500 mt-1">{form.formState.errors.activities_done.message}</p>}
              </div>
              <div>
                <label className="label">Porcentaje de avance: {form.watch("progress_percent") ?? 0}%</label>
                <input {...form.register("progress_percent", { valueAsNumber:true })}
                  type="range" min="0" max="100" step="5" className="w-full accent-primary-700"/>
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>0%</span><span>50%</span><span>100%</span>
                </div>
              </div>
              <div>
                <label className="label">Obstáculos o dificultades</label>
                <textarea {...form.register("obstacles")} rows={2} className="input resize-none"
                  placeholder="Dificultades encontradas, limitaciones de recursos, problemas metodológicos, etc."/>
              </div>
              <div>
                <label className="label">Plan de acción para el próximo período</label>
                <textarea {...form.register("action_plan")} rows={2} className="input resize-none"
                  placeholder="Actividades planificadas, estrategias para superar obstáculos, objetivos del siguiente período."/>
              </div>
              {submitMut.isError && (
                <p className="text-xs text-red-600 bg-red-50 p-2 rounded-lg">
                  {(submitMut.error as any)?.response?.data?.detail ?? "Error al registrar."}
                </p>
              )}
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => { setShowForm(false); form.reset() }}
                  className="btn-secondary flex-1">Cancelar</button>
                <button type="submit" disabled={submitMut.isPending} className="btn-primary flex-1">
                  {submitMut.isPending ? "Registrando..." : "Registrar avance"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
