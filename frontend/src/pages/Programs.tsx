import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useAuthStore } from "@/store/auth"
import { academicApi } from "@/services/academic"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import EmptyState from "@/components/EmptyState"
import {
  GraduationCap, Plus, Pencil, Trash2, X,
  Check, AlertCircle, Clock, BookOpen
} from "lucide-react"
import clsx from "clsx"
import api from "@/services/api"

const schema = z.object({
  name:               z.string().min(5, "Mínimo 5 caracteres"),
  code:               z.string().min(2, "Código requerido").max(20),
  level:              z.enum(["maestria","doctorado","especializacion"]),
  duration_months:    z.number().min(6).max(120),
  description:        z.string().optional(),
  coordinator_email:  z.string().email("Correo inválido").optional().or(z.literal("")),
})
type Form = z.infer<typeof schema>

const LEVELS: Record<string,string> = {
  maestria:         "Maestría",
  doctorado:        "Doctorado",
  especializacion:  "Especialización",
}
const levelColor: Record<string,string> = {
  maestria:        "bg-blue-100 text-blue-700",
  doctorado:       "bg-purple-100 text-purple-700",
  especializacion: "bg-green-100 text-green-700",
}

export default function Programs() {
  const { hasRole } = useAuthStore()
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<any|null>(null)
  const [msg, setMsg] = useState<{type:"ok"|"err"; text:string}|null>(null)

  const flash = (type:"ok"|"err", text:string) => {
    setMsg({type,text}); setTimeout(()=>setMsg(null),4000)
  }

  const { data, isLoading, isError: listError, error: listErrorDetail } = useQuery({
    queryKey: ["programs"],
    queryFn: () => academicApi.programs().then(r => r.data?.items ?? r.data ?? []),
  })

  const form = useForm<Form>({
    resolver: zodResolver(schema),
    defaultValues: { level:"maestria", duration_months: 24 }
  })

  const saveMut = useMutation({
    mutationFn: (d: Form) => {
      return editing
        ? api.patch(`/api/academic/programs/${editing.id}`, d)
        : api.post("/api/academic/programs", d)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["programs"] })
      setShowForm(false); setEditing(null); form.reset()
      flash("ok", editing ? "Programa actualizado." : "Programa creado exitosamente.")
    },
    onError: () => { /* error shown inline in form via saveMut.isError */ },
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) =>
      api.delete(`/api/academic/programs/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["programs"] })
      flash("ok","Programa eliminado.")
    },
    onError: (e:any) => flash("err", e.response?.data?.detail ?? "Error al eliminar."),
  })

  const openEdit = (p: any) => {
    setEditing(p)
    form.reset({
      name: p.name, code: p.code ?? "",
      level: p.level ?? "maestria",
      duration_months: p.duration_months ?? 24,
      description: p.description ?? "",
      coordinator_email: p.coordinator_email ?? "",
    })
    setShowForm(true)
  }

  const programs: any[] = data ?? []

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Programas de Postgrado</h1>
          <p className="text-sm text-gray-500 mt-0.5">{programs.length} programa{programs.length!==1?"s":""} registrado{programs.length!==1?"s":""}</p>
        </div>
        {hasRole("ADM","COO","DIR") && (
          <button onClick={() => { setEditing(null); form.reset({ level:"maestria", duration_months:24 }); setShowForm(true) }}
            className="btn-primary flex items-center gap-2 text-sm">
            <Plus className="w-4 h-4"/> Nuevo programa
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

      {/* Service error — show when DB or service is down */}
      {listError && (
        <div className="card flex items-start gap-3 border-l-4 border-red-400 mb-4">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5"/>
          <div>
            <p className="font-semibold text-red-700 text-sm">Error al cargar programas</p>
            <p className="text-xs text-red-600 mt-1 font-mono">
              {(listErrorDetail as any)?.response?.data?.detail ?? "Servicio no disponible"}
            </p>
          </div>
        </div>
      )}

      {isLoading && (
        <div className="space-y-3">
          {[1,2,3].map(i => <div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse"/>)}
        </div>
      )}

      {!isLoading && programs.length === 0 && (
        <EmptyState icon={GraduationCap} title="Sin programas"
          description="Crea el primer programa de postgrado del sistema."
          action={hasRole("ADM","COO") ? (
            <button onClick={() => setShowForm(true)} className="btn-primary text-sm flex items-center gap-2">
              <Plus className="w-4 h-4"/> Crear programa
            </button>
          ) : undefined}
        />
      )}

      <div className="space-y-3">
        {programs.map((p: any) => (
          <div key={p.id} className="card flex items-start gap-4">
            <div className="w-12 h-12 bg-primary-50 rounded-xl flex items-center justify-center flex-shrink-0">
              <GraduationCap className="w-6 h-6 text-primary-700"/>
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <h3 className="font-semibold text-gray-900">{p.name}</h3>
                <span className={clsx("text-xs px-2 py-0.5 rounded-full font-medium",
                  levelColor[p.level] ?? "bg-gray-100 text-gray-600")}>
                  {LEVELS[p.level] ?? p.level}
                </span>
                {p.code && (
                  <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full font-mono">
                    {p.code}
                  </span>
                )}
                <span className={clsx("text-xs px-2 py-0.5 rounded-full",
                  p.status==="active" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-400")}>
                  {p.status==="active" ? "Activo" : "Inactivo"}
                </span>
              </div>
              {p.description && (
                <p className="text-sm text-gray-500 mb-2 line-clamp-2">{p.description}</p>
              )}
              <div className="flex items-center gap-4 text-xs text-gray-400">
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3"/> {p.duration_months} meses
                </span>
                {p.coordinator_email && (
                  <span>{p.coordinator_email}</span>
                )}
              </div>
            </div>
            {hasRole("ADM","COO","DIR") && (
              <div className="flex items-center gap-1 flex-shrink-0">
                <button onClick={() => openEdit(p)}
                  className="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg">
                  <Pencil className="w-4 h-4"/>
                </button>
                {hasRole("ADM") && (
                  <button onClick={() => {
                    if(confirm(`¿Eliminar el programa "${p.name}"?`)) deleteMut.mutate(p.id)
                  }} className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg">
                    <Trash2 className="w-4 h-4"/>
                  </button>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-gray-100 sticky top-0 bg-white">
              <h2 className="font-bold text-gray-900">
                {editing ? "Editar programa" : "Nuevo programa de postgrado"}
              </h2>
              <button onClick={() => { setShowForm(false); setEditing(null) }}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg">
                <X className="w-5 h-5"/>
              </button>
            </div>
            <form onSubmit={form.handleSubmit(d => saveMut.mutate(d))} className="p-6 space-y-4">
              <div>
                <label className="label">Nombre del programa *</label>
                <input {...form.register("name")} className="input"
                  placeholder="Ej: Maestría en Ciberseguridad y Ciberdefensa"/>
                {form.formState.errors.name && <p className="text-xs text-red-500 mt-1">{form.formState.errors.name.message}</p>}
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Código *</label>
                  <input {...form.register("code")} className="input"
                    placeholder="Ej: MCCS-01"/>
                  {form.formState.errors.code && <p className="text-xs text-red-500 mt-1">{form.formState.errors.code.message}</p>}
                </div>
                <div>
                  <label className="label">Nivel *</label>
                  <select {...form.register("level")} className="input">
                    <option value="maestria">Maestría</option>
                    <option value="doctorado">Doctorado</option>
                    <option value="especializacion">Especialización</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="label">Duración (meses) *</label>
                <input {...form.register("duration_months", {valueAsNumber:true})}
                  type="number" min="6" max="120" step="6" className="input"/>
              </div>
              <div>
                <label className="label">Descripción</label>
                <textarea {...form.register("description")} rows={3}
                  className="input resize-none"
                  placeholder="Descripción del programa, énfasis y objetivos..."/>
              </div>
              <div>
                <label className="label">Correo del coordinador</label>
                <input {...form.register("coordinator_email")} type="email"
                  className="input" placeholder="coordinador@institucion.edu.co"/>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => { setShowForm(false); setEditing(null) }}
                  className="btn-secondary flex-1">Cancelar</button>
                <button type="submit" disabled={saveMut.isPending} className="btn-primary flex-1">
                  {saveMut.isPending ? "Guardando..." : editing ? "Actualizar" : "Crear programa"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
