import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useAuthStore } from "@/store/auth"
import { evalApi, tiApi } from "@/services/api"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import EmptyState from "@/components/EmptyState"
import { ClipboardList, Plus, X, Check, Star, AlertCircle, ChevronDown, ChevronUp } from "lucide-react"
import { format, parseISO } from "date-fns"
import { es } from "date-fns/locale"
import clsx from "clsx"

const scoreSchema = z.object({
  evaluation_id:  z.string().uuid(),
  criterion_id:   z.string().uuid(),
  score:          z.number().min(0).max(5),
  comments:       z.string().optional(),
})

const dictamenSchema = z.object({
  dictamen:  z.enum(["approved","conditional","rejected"]),
  comments:  z.string().min(10, "Mínimo 10 caracteres"),
})

const DICTAMEN_LABELS: Record<string, string> = {
  approved:    "Aprobado",
  conditional: "Aprobado con condiciones",
  rejected:    "Rechazado",
}
const DICTAMEN_COLORS: Record<string, string> = {
  approved:    "bg-green-100 text-green-700",
  conditional: "bg-yellow-100 text-yellow-700",
  rejected:    "bg-red-100 text-red-700",
}

export default function Evaluations() {
  const { user, hasRole } = useAuthStore()
  const qc = useQueryClient()
  const [expanded, setExpanded] = useState<string|null>(null)
  const [scoringEval, setScoringEval] = useState<any|null>(null)
  const [dictamenEval, setDictamenEval] = useState<string|null>(null)
  const [msg, setMsg] = useState<{type:"ok"|"err"; text:string}|null>(null)

  const flash = (type:"ok"|"err", text:string) => {
    setMsg({type,text}); setTimeout(() => setMsg(null), 4000)
  }

  // Load TIs for context
  const { data: tis } = useQuery({
    queryKey: ["tis-eval"],
    queryFn: () => tiApi.list(
      hasRole("EST") ? { student_id: user?.id } :
      hasRole("TUT") ? { tutor_id: user?.id } : {}
    ).then(r => r.data),
  })

  const { data: rubrics } = useQuery({
    queryKey: ["rubrics"],
    queryFn: () => evalApi.rubrics().then(r => r.data),
  })

  const scoreForm = useForm<z.infer<typeof scoreSchema>>({ resolver: zodResolver(scoreSchema) })
  const dictamenForm = useForm<z.infer<typeof dictamenSchema>>({ resolver: zodResolver(dictamenSchema) })

  const submitScore = useMutation({
    mutationFn: (d: z.infer<typeof scoreSchema>) => evalApi.score(d),
    onSuccess: () => {
      setScoringEval(null); scoreForm.reset()
      qc.invalidateQueries({ queryKey: ["evaluations"] })
      flash("ok", "Puntaje registrado correctamente.")
    },
    onError: (e:any) => flash("err", e.response?.data?.detail ?? "Error al registrar puntaje."),
  })

  const submitDictamen = useMutation({
    mutationFn: ({ id, data }: { id:string; data:z.infer<typeof dictamenSchema> }) =>
      evalApi.dictamen(id, data),
    onSuccess: () => {
      setDictamenEval(null); dictamenForm.reset()
      qc.invalidateQueries({ queryKey: ["evaluations"] })
      flash("ok", "Dictamen emitido y registrado oficialmente.")
    },
    onError: (e:any) => flash("err", e.response?.data?.detail ?? "Error al emitir dictamen."),
  })

  const items: any[] = tis?.items ?? []

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-900">Evaluaciones y Rúbricas</h1>
        <p className="text-sm text-gray-500 mt-0.5">Evaluaciones formales de trabajos de investigación</p>
      </div>

      {msg && (
        <div className={clsx("flex items-center gap-2 p-3 rounded-lg mb-4 text-sm",
          msg.type==="ok" ? "bg-green-50 text-green-700 border border-green-200"
                          : "bg-red-50 text-red-700 border border-red-200")}>
          {msg.type==="ok" ? <Check className="w-4 h-4"/> : <AlertCircle className="w-4 h-4"/>}
          {msg.text}
        </div>
      )}

      {/* Rubrics summary for DIR/COO */}
      {hasRole("DIR","COO","ADM") && (
        <div className="card mb-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-800">Rúbricas configuradas</h3>
            <span className="text-sm text-gray-500">{(rubrics ?? []).length} rúbricas</span>
          </div>
          {(rubrics ?? []).length === 0 ? (
            <p className="text-sm text-gray-400">No hay rúbricas configuradas. Las rúbricas se crean por el administrador.</p>
          ) : (
            <div className="space-y-2">
              {(rubrics ?? []).map((r: any) => (
                <div key={r.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="text-sm font-medium text-gray-800">{r.name}</p>
                    <p className="text-xs text-gray-500">{r.evaluation_type} · {r.criteria?.length ?? 0} criterios</p>
                  </div>
                  <span className="text-xs bg-primary-50 text-primary-700 px-2 py-0.5 rounded-full">
                    Peso total: {r.total_weight ?? 100}%
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TI evaluations */}
      {items.length === 0 && (
        <EmptyState icon={ClipboardList} title="Sin evaluaciones"
          description="Las evaluaciones aparecerán cuando haya hitos formales en los TIs asignados."/>
      )}

      <div className="space-y-4">
        {items.map((ti: any) => (
          <div key={ti.id} className="card">
            <button className="w-full flex items-center justify-between"
              onClick={() => setExpanded(expanded === ti.id ? null : ti.id)}>
              <div className="text-left">
                <h3 className="font-semibold text-gray-900 text-sm">{ti.title}</h3>
                <p className="text-xs text-gray-500">{ti.knowledge_area} · Avance: {ti.progress_percent}%</p>
              </div>
              <div className="flex items-center gap-2">
                {(ti.evaluations ?? []).length > 0 && (
                  <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full">
                    {ti.evaluations.length} evaluación{ti.evaluations.length > 1 ? "es" : ""}
                  </span>
                )}
                {expanded === ti.id
                  ? <ChevronUp className="w-4 h-4 text-gray-400"/>
                  : <ChevronDown className="w-4 h-4 text-gray-400"/>}
              </div>
            </button>

            {expanded === ti.id && (
              <div className="mt-4 pt-4 border-t border-gray-100 space-y-3">
                {(ti.evaluations ?? []).length === 0 ? (
                  <p className="text-sm text-gray-400">No hay evaluaciones formales para este TI aún.</p>
                ) : (
                  (ti.evaluations ?? []).map((ev: any) => (
                    <div key={ev.id} className="p-3 bg-gray-50 rounded-xl">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <p className="text-sm font-medium text-gray-800">{ev.evaluation_type}</p>
                          <p className="text-xs text-gray-500">
                            {format(parseISO(ev.created_at), "d MMM yyyy", { locale: es })}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          {ev.dictamen && (
                            <span className={clsx("text-xs px-2 py-0.5 rounded-full font-medium",
                              DICTAMEN_COLORS[ev.dictamen] ?? "bg-gray-100 text-gray-600")}>
                              {DICTAMEN_LABELS[ev.dictamen] ?? ev.dictamen}
                            </span>
                          )}
                          {ev.consolidated_score != null && (
                            <div className="flex items-center gap-1 text-sm font-bold text-primary-700">
                              <Star className="w-3.5 h-3.5"/>
                              {ev.consolidated_score.toFixed(1)}/5.0
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="flex gap-2">
                        {hasRole("TUT","CEV","COO","DIR") && ev.status !== "published" && (
                          <button
                            onClick={() => { setScoringEval(ev); scoreForm.setValue("evaluation_id", ev.id) }}
                            className="btn-primary text-xs py-1.5 px-3 flex items-center gap-1.5">
                            <Star className="w-3 h-3"/> Puntuar
                          </button>
                        )}
                        {hasRole("DIR","COO") && !ev.dictamen && ev.status !== "draft" && (
                          <button
                            onClick={() => { setDictamenEval(ev.id); dictamenForm.reset() }}
                            className="btn-secondary text-xs py-1.5 px-3 flex items-center gap-1.5">
                            <Check className="w-3 h-3"/> Emitir dictamen
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Score Modal */}
      {scoringEval && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-5">
              <h2 className="font-bold text-gray-900">Registrar puntaje</h2>
              <button onClick={() => setScoringEval(null)} className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg">
                <X className="w-5 h-5"/>
              </button>
            </div>
            <form onSubmit={scoreForm.handleSubmit(d => submitScore.mutate(d))} className="space-y-4">
              <input type="hidden" {...scoreForm.register("evaluation_id")}/>
              <div>
                <label className="label">Criterio a evaluar</label>
                <select {...scoreForm.register("criterion_id")} className="input">
                  <option value="">Selecciona criterio...</option>
                  {(rubrics ?? []).flatMap((r:any) => r.criteria ?? []).map((c:any) => (
                    <option key={c.id} value={c.id}>{c.name} (peso: {c.weight}%)</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Puntaje: {scoreForm.watch("score") ?? 0}/5.0</label>
                <input {...scoreForm.register("score", { valueAsNumber: true })}
                  type="range" min="0" max="5" step="0.5"
                  className="w-full accent-primary-700"/>
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>0 — Deficiente</span><span>2.5 — Aceptable</span><span>5 — Excelente</span>
                </div>
              </div>
              <div>
                <label className="label">Comentarios</label>
                <textarea {...scoreForm.register("comments")} rows={3}
                  className="input resize-none"
                  placeholder="Observaciones específicas sobre este criterio..."/>
              </div>
              <div className="flex gap-3">
                <button type="button" onClick={() => setScoringEval(null)} className="btn-secondary flex-1">Cancelar</button>
                <button type="submit" disabled={submitScore.isPending} className="btn-primary flex-1">
                  {submitScore.isPending ? "Guardando..." : "Registrar puntaje"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Dictamen Modal */}
      {dictamenEval && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-5">
              <h2 className="font-bold text-gray-900">Emitir dictamen oficial</h2>
              <button onClick={() => setDictamenEval(null)} className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg">
                <X className="w-5 h-5"/>
              </button>
            </div>
            <form onSubmit={dictamenForm.handleSubmit(d => submitDictamen.mutate({ id: dictamenEval, data: d }))}
              className="space-y-4">
              <div>
                <label className="label">Resultado *</label>
                <div className="grid grid-cols-1 gap-2">
                  {Object.entries(DICTAMEN_LABELS).map(([val, label]) => (
                    <label key={val} className={clsx(
                      "flex items-center gap-3 p-3 border-2 rounded-xl cursor-pointer transition-colors",
                      dictamenForm.watch("dictamen") === val
                        ? val==="approved" ? "border-green-500 bg-green-50"
                          : val==="rejected" ? "border-red-400 bg-red-50"
                          : "border-yellow-400 bg-yellow-50"
                        : "border-gray-200 hover:border-gray-300"
                    )}>
                      <input type="radio" {...dictamenForm.register("dictamen")} value={val} className="hidden"/>
                      <div className={clsx("w-3 h-3 rounded-full",
                        dictamenForm.watch("dictamen") === val
                          ? val==="approved" ? "bg-green-500"
                            : val==="rejected" ? "bg-red-500" : "bg-yellow-500"
                          : "bg-gray-300"
                      )}/>
                      <span className="text-sm font-medium">{label}</span>
                    </label>
                  ))}
                </div>
              </div>
              <div>
                <label className="label">Fundamentación del dictamen *</label>
                <textarea {...dictamenForm.register("comments")} rows={4}
                  className="input resize-none"
                  placeholder="Justificación del dictamen, condiciones específicas si aplica..."/>
                {dictamenForm.formState.errors.comments && (
                  <p className="text-xs text-red-500 mt-1">{dictamenForm.formState.errors.comments.message}</p>
                )}
              </div>
              <div className="flex gap-3">
                <button type="button" onClick={() => setDictamenEval(null)} className="btn-secondary flex-1">Cancelar</button>
                <button type="submit" disabled={submitDictamen.isPending} className="btn-primary flex-1">
                  {submitDictamen.isPending ? "Emitiendo..." : "Confirmar dictamen"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
