import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useParams, Link } from "react-router-dom"
import { useAuthStore } from "@/store/auth"
import axios from "axios"
import { useState } from "react"
import { ArrowLeft, Mail, Phone, BookOpen, Shield, Plus, X, Check } from "lucide-react"
import clsx from "clsx"

const ROLE_CODES = ["ADM","DIR","COO","TUT","EST","CEV","COT","EXT"]
const roleLabel: Record<string,string> = {
  ADM:"Administrador", DIR:"Director", COO:"Coordinador",
  TUT:"Tutor", EST:"Estudiante", CEV:"Comité Evaluador",
  COT:"Co-Tutor", EXT:"Evaluador Externo",
}
const roleColor: Record<string,string> = {
  ADM:"bg-red-100 text-red-700", DIR:"bg-purple-100 text-purple-700",
  COO:"bg-blue-100 text-blue-700", TUT:"bg-green-100 text-green-700",
  EST:"bg-yellow-100 text-yellow-700", CEV:"bg-orange-100 text-orange-700",
  COT:"bg-teal-100 text-teal-700", EXT:"bg-gray-100 text-gray-600",
}

export default function UserDetail() {
  const { id } = useParams<{ id: string }>()
  const { token, hasRole } = useAuthStore()
  const qc = useQueryClient()
  const headers = { Authorization: `Bearer ${token}` }
  const [addRole, setAddRole] = useState("")
  const [msg, setMsg] = useState<{type:"ok"|"err", text:string}|null>(null)

  const { data: profile, isLoading } = useQuery({
    queryKey: ["user-profile", id],
    queryFn: () => axios.get(`/api/users/users/${id}`, { headers }).then(r => r.data),
    enabled: !!id,
  })

  const assignRole = useMutation({
    mutationFn: (role_code: string) =>
      axios.post("/api/users/roles/assign", { user_id: id, role_code }, { headers }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["user-profile", id] })
      setAddRole("")
      setMsg({ type:"ok", text:"Rol asignado correctamente." })
      setTimeout(() => setMsg(null), 3000)
    },
    onError: (e: any) => setMsg({ type:"err", text: e.response?.data?.detail ?? "Error al asignar rol." }),
  })

  const revokeRole = useMutation({
    mutationFn: ({ role_code }: { role_code: string }) =>
      axios.post("/api/users/roles/revoke", { user_id: id, role_code }, { headers }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["user-profile", id] })
      setMsg({ type:"ok", text:"Rol revocado." })
      setTimeout(() => setMsg(null), 3000)
    },
    onError: (e: any) => setMsg({ type:"err", text: e.response?.data?.detail ?? "Error." }),
  })

  const changeStatus = useMutation({
    mutationFn: (status: string) =>
      axios.patch(`/api/users/users/${id}/status`, { status }, { headers }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["user-profile", id] })
      setMsg({ type:"ok", text:"Estado actualizado." })
      setTimeout(() => setMsg(null), 3000)
    },
  })

  if (isLoading) return (
    <div className="max-w-2xl mx-auto space-y-4">
      {[1,2,3].map(i => <div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse"/>)}
    </div>
  )
  if (!profile) return <p className="text-center text-gray-400 mt-16">Usuario no encontrado.</p>

  const initials = profile.full_name.split(" ").map((w:string) => w[0]).join("").slice(0,2).toUpperCase()
  const activeRoles = profile.roles?.filter((r:any) => r.is_active) ?? []
  const canManage = hasRole("ADM","COO","DIR")

  return (
    <div className="max-w-2xl mx-auto">
      <Link to="/users" className="flex items-center gap-2 text-sm text-gray-500 hover:text-primary-700 mb-6 group">
        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform"/>
        Volver al directorio
      </Link>

      {msg && (
        <div className={clsx("flex items-center gap-2 p-3 rounded-lg mb-4 text-sm",
          msg.type==="ok" ? "bg-green-50 text-green-700 border border-green-200"
                          : "bg-red-50 text-red-700 border border-red-200")}>
          {msg.type==="ok" ? <Check className="w-4 h-4"/> : <X className="w-4 h-4"/>}
          {msg.text}
        </div>
      )}

      {/* Profile header */}
      <div className="card mb-4">
        <div className="flex items-start gap-5">
          {profile.photo_url ? (
            <img src={profile.photo_url} alt={profile.full_name}
              className="w-20 h-20 rounded-full ring-4 ring-primary-100 object-cover flex-shrink-0"
              onError={e => { (e.target as HTMLImageElement).style.display="none" }}/>
          ) : (
            <div className="w-20 h-20 rounded-full bg-primary-700 text-white flex items-center justify-center text-2xl font-bold flex-shrink-0">
              {initials}
            </div>
          )}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div>
                <h1 className="text-xl font-bold text-gray-900">{profile.full_name}</h1>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {activeRoles.map((r:any) => (
                    <span key={r.id} className={clsx("text-xs px-2 py-0.5 rounded-full font-medium",
                      roleColor[r.role_code] ?? "bg-gray-100 text-gray-600")}>
                      {roleLabel[r.role_code] ?? r.role_code}
                    </span>
                  ))}
                </div>
              </div>
              {canManage && (
                <button
                  onClick={() => changeStatus.mutate(profile.status === "active" ? "inactive" : "active")}
                  className={clsx("text-xs px-3 py-1.5 rounded-full font-medium border transition-colors flex-shrink-0",
                    profile.status === "active"
                      ? "bg-green-50 text-green-700 border-green-200 hover:bg-red-50 hover:text-red-700 hover:border-red-200"
                      : "bg-gray-50 text-gray-500 border-gray-200 hover:bg-green-50 hover:text-green-700 hover:border-green-200")}>
                  {profile.status === "active" ? "Activo" : "Inactivo"}
                </button>
              )}
            </div>
            <div className="mt-3 space-y-1.5">
              <p className="flex items-center gap-2 text-sm text-gray-600">
                <Mail className="w-3.5 h-3.5 text-gray-400"/>{profile.email}
              </p>
              {profile.phone && (
                <p className="flex items-center gap-2 text-sm text-gray-600">
                  <Phone className="w-3.5 h-3.5 text-gray-400"/>{profile.phone}
                </p>
              )}
              {profile.area_of_expertise && (
                <p className="flex items-center gap-2 text-sm text-gray-600">
                  <BookOpen className="w-3.5 h-3.5 text-gray-400"/>{profile.area_of_expertise}
                </p>
              )}
            </div>
          </div>
        </div>
        {profile.bio && (
          <div className="mt-4 pt-4 border-t border-gray-100">
            <p className="text-sm text-gray-600 leading-relaxed">{profile.bio}</p>
          </div>
        )}
      </div>

      {/* Role management */}
      {canManage && (
        <div className="card mb-4">
          <h2 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <Shield className="w-4 h-4 text-primary-500"/> Gestión de roles
          </h2>
          <div className="space-y-2 mb-4">
            {profile.roles?.map((r:any) => (
              <div key={r.id} className="flex items-center justify-between p-2.5 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <span className={clsx("text-xs font-semibold px-2.5 py-1 rounded-full",
                    roleColor[r.role_code] ?? "bg-gray-100 text-gray-600")}>
                    {roleLabel[r.role_code] ?? r.role_code}
                  </span>
                  <span className={clsx("text-xs", r.is_active ? "text-green-600" : "text-gray-400")}>
                    {r.is_active ? "Activo" : "Inactivo"}
                  </span>
                </div>
                {r.is_active && (
                  <button onClick={() => revokeRole.mutate({ role_code: r.role_code })}
                    className="text-xs text-red-500 hover:text-red-700 flex items-center gap-1 px-2 py-1 rounded hover:bg-red-50">
                    <X className="w-3 h-3"/> Revocar
                  </button>
                )}
              </div>
            ))}
          </div>

          <div className="flex gap-2">
            <select value={addRole} onChange={e => setAddRole(e.target.value)} className="input flex-1 text-sm">
              <option value="">Selecciona rol a asignar...</option>
              {ROLE_CODES.filter(rc => !activeRoles.find((r:any) => r.role_code === rc)).map(rc => (
                <option key={rc} value={rc}>{roleLabel[rc]}</option>
              ))}
            </select>
            <button onClick={() => addRole && assignRole.mutate(addRole)}
              disabled={!addRole || assignRole.isPending}
              className="btn-primary flex items-center gap-1.5 text-sm px-4">
              <Plus className="w-4 h-4"/> Asignar
            </button>
          </div>
        </div>
      )}

      {/* TIs related */}
      <div className="card">
        <h2 className="font-semibold text-gray-800 mb-3">Trabajos de investigación</h2>
        <Link to={`/ti?${activeRoles.find((r:any) => r.role_code==="EST") ? "student_id" : "tutor_id"}=${id}`}
          className="text-sm text-primary-600 hover:underline">
          Ver TIs relacionados →
        </Link>
      </div>
    </div>
  )
}
