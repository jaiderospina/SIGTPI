import { useState } from "react"
import axios from "axios"
import { useMutation, useQueryClient, useQuery } from "@tanstack/react-query"
import { useAuthStore } from "@/store/auth"
import { academicApi, tutoringApi } from "@/services/academic"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { X, BookOpen } from "lucide-react"
import clsx from "clsx"

const schema = z.object({
  assignment_id: z.string().uuid("Selecciona una asignación activa"),
  student_id:    z.string().uuid(),
  tutor_id:      z.string().uuid(),
  program_id:    z.string().uuid(),
  title:         z.string().min(10, "Mínimo 10 caracteres"),
  knowledge_area:z.string().min(5, "Selecciona área"),
  problem_statement: z.string().optional(),
  objectives:    z.string().optional(),
  methodology:   z.string().optional(),
})
type Form = z.infer<typeof schema>

const AREAS = [
  "Ciberseguridad y Ciberdefensa",
  "Redes y Telecomunicaciones",
  "Ciencia de Datos e Inteligencia Artificial",
  "Ingeniería de Software",
  "Gestión de Sistemas de Información",
]

interface Props { onClose: () => void; onSuccess: () => void }

export default function TICreateModal({ onClose, onSuccess }: Props) {
  const { token } = useAuthStore()
  const qc = useQueryClient()
  
  const { data: assignments } = useQuery({
    queryKey: ["assignments-active"],
    queryFn: () => tutoringApi.list({ page_size: 100 }),
  })

  const form = useForm<Form>({ resolver: zodResolver(schema) })
  
  const createMut = useMutation({
    mutationFn: (d: Form) => 
      axios.post("/api/ti/ti", d, {
        headers: { Authorization: `Bearer ${token}` }
      }).then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tis"] })
      onSuccess()
      onClose()
    },
  })

  const activeAssignments = (assignments?.items ?? assignments ?? [])
    .filter((a: any) => a.status === "active")

  const onAssignmentChange = (id: string) => {
    const a = activeAssignments.find((x: any) => x.id === id)
    if (a) {
      form.setValue("student_id", a.student_id)
      form.setValue("tutor_id", a.tutor_id)
      form.setValue("program_id", a.program_id)
      if (a.preliminary_title) form.setValue("title", a.preliminary_title)
      if (a.research_area) form.setValue("knowledge_area", a.research_area)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-100 sticky top-0 bg-white">
          <h2 className="font-bold text-gray-900 flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-primary-500"/> Registrar Trabajo de Investigación
          </h2>
          <button onClick={onClose} className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg">
            <X className="w-5 h-5"/>
          </button>
        </div>

        <form onSubmit={form.handleSubmit(d => createMut.mutate(d))} className="p-6 space-y-4">
          <div>
            <label className="label">Asignación de tutoría activa *</label>
            <select {...form.register("assignment_id")} className="input"
              onChange={e => { form.register("assignment_id").onChange(e); onAssignmentChange(e.target.value) }}>
              <option value="">Selecciona la asignación...</option>
              {activeAssignments.map((a: any) => (
                <option key={a.id} value={a.id}>
                  {a.preliminary_title ?? a.research_area}
                </option>
              ))}
            </select>
            {form.formState.errors.assignment_id && (
              <p className="text-xs text-red-500 mt-1">{form.formState.errors.assignment_id.message}</p>
            )}
            {activeAssignments.length === 0 && (
              <p className="text-xs text-amber-600 mt-1">
                No hay asignaciones activas. Primero crea una asignación de tutoría.
              </p>
            )}
          </div>

          <input type="hidden" {...form.register("student_id")}/>
          <input type="hidden" {...form.register("tutor_id")}/>
          <input type="hidden" {...form.register("program_id")}/>

          <div>
            <label className="label">Título del TI *</label>
            <input {...form.register("title")} className="input"
              placeholder="Título definitivo o tentativo del trabajo de investigación"/>
            {form.formState.errors.title && (
              <p className="text-xs text-red-500 mt-1">{form.formState.errors.title.message}</p>
            )}
          </div>

          <div>
            <label className="label">Área de conocimiento *</label>
            <select {...form.register("knowledge_area")} className="input">
              <option value="">Selecciona área...</option>
              {AREAS.map(a => <option key={a} value={a}>{a}</option>)}
            </select>
          </div>

          <div>
            <label className="label">Planteamiento del problema</label>
            <textarea {...form.register("problem_statement")} rows={3}
              className="input resize-none"
              placeholder="Describe el problema de investigación que abordará el trabajo..."/>
          </div>

          <div>
            <label className="label">Objetivo general</label>
            <textarea {...form.register("objectives")} rows={2}
              className="input resize-none"
              placeholder="Objetivo principal que se busca alcanzar con la investigación..."/>
          </div>

          <div>
            <label className="label">Metodología propuesta</label>
            <textarea {...form.register("methodology")} rows={2}
              className="input resize-none"
              placeholder="Enfoque metodológico: experimental, descriptivo, mixto..."/>
          </div>

          {createMut.isError && (
            <p className="text-xs text-red-600 bg-red-50 p-2 rounded-lg">
              {(createMut.error as any)?.response?.data?.detail ?? "Error al crear el TI."}
            </p>
          )}

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">Cancelar</button>
            <button type="submit" disabled={createMut.isPending || activeAssignments.length === 0}
              className="btn-primary flex-1">
              {createMut.isPending ? "Creando..." : "Crear TI"}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
