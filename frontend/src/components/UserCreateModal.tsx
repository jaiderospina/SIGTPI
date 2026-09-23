import { useMutation, useQueryClient, useQuery } from "@tanstack/react-query"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { userApi } from "@/services/api"
import { academicApi } from "@/services/academic"
import { X, UserPlus, Mail, User, Phone, BookOpen, FileText } from "lucide-react"

const DOC_TYPES = [
  { value:"CC",        label:"Cédula de Ciudadanía (CC)" },
  { value:"CE",        label:"Cédula de Extranjería (CE)" },
  { value:"TI",        label:"Tarjeta de Identidad (TI)" },
  { value:"PAS",       label:"Pasaporte" },
  { value:"NIT",       label:"NIT" },
]

const ROLES = [
  { value:"EST", label:"Estudiante" },
  { value:"TUT", label:"Tutor" },
  { value:"COO", label:"Coordinador" },
  { value:"DIR", label:"Director de Programa" },
  { value:"CEV", label:"Comité Evaluador" },
  { value:"EXT", label:"Evaluador Externo" },
  { value:"ADM", label:"Administrador" },
]

const AREAS = [
  "Ciberseguridad y Ciberdefensa",
  "Redes y Telecomunicaciones",
  "Ciencia de Datos e Inteligencia Artificial",
  "Ingeniería de Software",
  "Gestión de Sistemas de Información",
  "Investigación Académica",
]

const schema = z.object({
  full_name:         z.string().min(2, "Mínimo 2 caracteres"),
  email:             z.string().email("Correo inválido"),
  doc_type:          z.string().default("CC"),
  document_id:       z.string().optional(),
  phone:             z.string().optional(),
  area_of_expertise: z.string().optional(),
  initial_role:      z.string().default("EST"),
  program_id:        z.string().optional(),
})
type Form = z.infer<typeof schema>

export default function UserCreateModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient()
  const form = useForm<Form>({
    resolver: zodResolver(schema),
    defaultValues: { initial_role: "EST", doc_type: "CC" }
  })

  const { data: programsData } = useQuery({
    queryKey: ["programs"],
    queryFn: () => academicApi.programs().then(r => r.data?.items ?? r.data ?? []),
  })
  const programs: any[] = programsData ?? []

  const createMut = useMutation({
    mutationFn: (d: Form) => userApi.create({
      full_name:         d.full_name,
      email:             d.email,
      document_id:       d.document_id ? `${d.doc_type}-${d.document_id}` : undefined,
      phone:             d.phone || undefined,
      area_of_expertise: d.area_of_expertise || undefined,
      initial_role:      d.initial_role,
      program_id:        d.program_id || undefined,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] })
      onClose()
    },
  })

  const role = form.watch("initial_role")
  const needsProgram = ["EST","TUT","COO","DIR"].includes(role)

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-100 sticky top-0 bg-white">
          <h2 className="font-bold text-gray-900 flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-primary-500"/> Crear usuario
          </h2>
          <button onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg">
            <X className="w-5 h-5"/>
          </button>
        </div>

        <form onSubmit={form.handleSubmit(d => createMut.mutate(d))} className="p-6 space-y-4">
          {/* Nombre */}
          <div>
            <label className="label">Nombre completo *</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
              <input {...form.register("full_name")} className="input pl-10"
                placeholder="Nombre y apellidos completos"/>
            </div>
            {form.formState.errors.full_name && (
              <p className="text-xs text-red-500 mt-1">{form.formState.errors.full_name.message}</p>
            )}
          </div>

          {/* Correo */}
          <div>
            <label className="label">Correo institucional *</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
              <input {...form.register("email")} type="email" className="input pl-10"
                placeholder="usuario@institucion.edu.co"/>
            </div>
            {form.formState.errors.email && (
              <p className="text-xs text-red-500 mt-1">{form.formState.errors.email.message}</p>
            )}
            <p className="text-xs text-gray-400 mt-1">
              Se generará una contraseña temporal accesible en los logs del sistema.
            </p>
          </div>

          {/* Documento */}
          <div>
            <label className="label">Documento de identidad</label>
            <div className="flex gap-2">
              <select {...form.register("doc_type")} className="input w-52 flex-shrink-0">
                {DOC_TYPES.map(d => (
                  <option key={d.value} value={d.value}>{d.label}</option>
                ))}
              </select>
              <div className="relative flex-1">
                <FileText className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
                <input {...form.register("document_id")} className="input pl-10"
                  placeholder="Número"/>
              </div>
            </div>
          </div>

          {/* Teléfono */}
          <div>
            <label className="label">Teléfono</label>
            <div className="relative">
              <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
              <input {...form.register("phone")} className="input pl-10"
                placeholder="310 000 0000"/>
            </div>
          </div>

          {/* Rol */}
          <div>
            <label className="label">Rol inicial *</label>
            <select {...form.register("initial_role")} className="input">
              {ROLES.map(r => (
                <option key={r.value} value={r.value}>{r.label}</option>
              ))}
            </select>
          </div>

          {/* Programa */}
          {needsProgram && (
            <div>
              <label className="label">Programa de postgrado</label>
              {programs.length === 0 ? (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                  <p className="text-xs text-amber-700">
                    No hay programas creados. Ve a <strong>Programas</strong> para crear uno primero.
                  </p>
                </div>
              ) : (
                <select {...form.register("program_id")} className="input">
                  <option value="">Sin programa específico</option>
                  {programs.map((p: any) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.level})
                    </option>
                  ))}
                </select>
              )}
            </div>
          )}

          {/* Área */}
          <div>
            <label className="label">Área de especialización</label>
            <div className="relative">
              <BookOpen className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
              <select {...form.register("area_of_expertise")} className="input pl-10">
                <option value="">Selecciona área...</option>
                {AREAS.map(a => <option key={a} value={a}>{a}</option>)}
              </select>
            </div>
          </div>

          {/* Error */}
          {createMut.isError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-xs text-red-700 font-medium">
                {(createMut.error as any)?.response?.data?.detail ??
                 (createMut.error as any)?.message ??
                 "Error al crear usuario."}
              </p>
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary flex-1">
              Cancelar
            </button>
            <button type="submit" disabled={createMut.isPending} className="btn-primary flex-1">
              {createMut.isPending ? "Creando..." : "Crear usuario"}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
