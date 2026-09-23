import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useAuthStore } from "@/store/auth"
import { userApi } from "@/services/api"
import { Link } from "react-router-dom"
import UserCreateModal from "@/components/UserCreateModal"
import EmptyState from "@/components/EmptyState"
import {
  Users as UsersIcon, Search, Plus, UserCheck,
  Phone, BookOpen, ToggleLeft, ToggleRight, AlertCircle
} from "lucide-react"
import clsx from "clsx"

const roleLabel: Record<string,string> = {
  ADM:"Administrador", DIR:"Director", COO:"Coordinador",
  TUT:"Tutor", EST:"Estudiante", CEV:"Comité", COT:"Co-Tutor", EXT:"Externo",
}
const roleColor: Record<string,string> = {
  ADM:"bg-red-100 text-red-700", DIR:"bg-purple-100 text-purple-700",
  COO:"bg-blue-100 text-blue-700", TUT:"bg-green-100 text-green-700",
  EST:"bg-yellow-100 text-yellow-700", CEV:"bg-orange-100 text-orange-700",
  COT:"bg-teal-100 text-teal-700", EXT:"bg-gray-100 text-gray-600",
}
const ROLE_FILTERS = ["Todos","ADM","COO","DIR","TUT","EST","CEV","EXT"]

export default function Users() {
  const { hasRole } = useAuthStore()
  const qc = useQueryClient()
  const [search, setSearch] = useState("")
  const [roleFilter, setRoleFilter] = useState("Todos")
  const [showCreate, setShowCreate] = useState(false)
  const [selected, setSelected] = useState<string|null>(null)

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["users", search, roleFilter],
    queryFn: () => userApi.list({
      search: search || undefined,
      role_code: roleFilter !== "Todos" ? roleFilter : undefined,
      page_size: 50,
    }).then(r => r.data),
    staleTime: 30_000,
    retry: 1,
  })

  const statusMut = useMutation({
    mutationFn: ({ id, status }: { id:string; status:string }) =>
      userApi.status(id, status),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] })
      setSelected(null)
    },
  })

  const users: any[] = data?.items ?? []
  const selectedUser = users.find(u => u.id === selected)
  const initials = (name: string) =>
    name.split(" ").map(w => w[0]).join("").slice(0,2).toUpperCase()

  // Error state — distinguish from empty
  if (isError) {
    const msg = (error as any)?.response?.data?.detail ?? "No se pudo conectar al servicio de usuarios."
    return (
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl font-bold text-gray-900">Directorio de Usuarios</h1>
          {hasRole("ADM","COO") && (
            <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2 text-sm">
              <Plus className="w-4 h-4"/> Nuevo usuario
            </button>
          )}
        </div>
        <div className="card flex items-start gap-4 border-l-4 border-red-400">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5"/>
          <div>
            <p className="font-semibold text-red-700">Error al cargar usuarios</p>
            <p className="text-sm text-red-600 mt-1 font-mono">{msg}</p>
            <button onClick={() => refetch()} className="btn-secondary text-sm mt-3">
              Reintentar
            </button>
          </div>
        </div>
        {showCreate && <UserCreateModal onClose={() => setShowCreate(false)}/>}
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Directorio de Usuarios</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {isLoading ? "Cargando..." : `${data?.total ?? 0} usuarios registrados`}
          </p>
        </div>
        {hasRole("ADM","COO") && (
          <button onClick={() => setShowCreate(true)}
            className="btn-primary flex items-center gap-2 text-sm">
            <Plus className="w-4 h-4"/> Nuevo usuario
          </button>
        )}
      </div>

      <div className="flex gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex gap-2 mb-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
              <input value={search} onChange={e => setSearch(e.target.value)}
                placeholder="Buscar por nombre o correo..."
                className="input pl-10 text-sm"/>
            </div>
            <select value={roleFilter} onChange={e => setRoleFilter(e.target.value)}
              className="input w-40 text-sm">
              {ROLE_FILTERS.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>

          {isLoading && (
            <div className="space-y-2">
              {[1,2,3,4,5].map(i => (
                <div key={i} className="h-16 bg-gray-100 rounded-xl animate-pulse"/>
              ))}
            </div>
          )}

          {!isLoading && users.length === 0 && (
            <EmptyState icon={UsersIcon} title="Sin usuarios"
              description={search
                ? "Ningún usuario coincide con la búsqueda."
                : "No hay usuarios registrados aún."}
              action={hasRole("ADM","COO") && !search ? (
                <button onClick={() => setShowCreate(true)}
                  className="btn-primary text-sm flex items-center gap-2">
                  <Plus className="w-4 h-4"/> Crear usuario
                </button>
              ) : undefined}
            />
          )}

          <div className="space-y-1.5">
            {users.map((u: any) => {
              const activeRoles = u.roles?.filter((r:any) => r.is_active)
                ?? (u.role_codes ?? []).map((rc:string) => ({ role_code: rc, is_active: true }))
              const isActive = u.status === "active"
              return (
                <button key={u.id}
                  onClick={() => setSelected(u.id === selected ? null : u.id)}
                  className={clsx(
                    "w-full flex items-center gap-3 p-3 rounded-xl border text-left transition-all",
                    selected === u.id
                      ? "border-primary-300 bg-primary-50"
                      : "border-gray-100 bg-white hover:border-gray-200 hover:bg-gray-50"
                  )}>
                  <div className={clsx(
                    "w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0",
                    isActive ? "bg-primary-700 text-white" : "bg-gray-200 text-gray-500"
                  )}>
                    {initials(u.full_name)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-gray-900 truncate">{u.full_name}</p>
                      {!isActive && <span className="text-xs text-gray-400">(inactivo)</span>}
                    </div>
                    <p className="text-xs text-gray-500 truncate">{u.email}</p>
                  </div>
                  <div className="flex gap-1 flex-shrink-0">
                    {(u.role_codes ?? activeRoles.map((r:any) => r.role_code)).slice(0,2).map((rc:string) => (
                      <span key={rc} className={clsx("text-xs px-1.5 py-0.5 rounded-full font-medium",
                        roleColor[rc] ?? "bg-gray-100 text-gray-600")}>
                        {roleLabel[rc] ?? rc}
                      </span>
                    ))}
                  </div>
                </button>
              )
            })}
          </div>
        </div>

        {selectedUser && (
          <div className="w-72 flex-shrink-0">
            <div className="card sticky top-4">
              <div className="text-center mb-4">
                <div className={clsx(
                  "w-16 h-16 rounded-full flex items-center justify-center text-xl font-bold mx-auto mb-3",
                  selectedUser.status==="active" ? "bg-primary-700 text-white" : "bg-gray-200 text-gray-500"
                )}>
                  {initials(selectedUser.full_name)}
                </div>
                <h3 className="font-bold text-gray-900">{selectedUser.full_name}</h3>
                <p className="text-xs text-gray-500 mt-0.5">{selectedUser.email}</p>
              </div>

              <div className="space-y-2 text-sm mb-4">
                {selectedUser.phone && (
                  <div className="flex items-center gap-2 text-gray-600">
                    <Phone className="w-3.5 h-3.5 text-gray-400"/>
                    {selectedUser.phone}
                  </div>
                )}
                {selectedUser.area_of_expertise && (
                  <div className="flex items-center gap-2 text-gray-600">
                    <BookOpen className="w-3.5 h-3.5 text-gray-400"/>
                    <span className="truncate">{selectedUser.area_of_expertise}</span>
                  </div>
                )}
              </div>

              <div className="flex flex-wrap gap-1.5 mb-4">
                {(selectedUser.role_codes ?? []).map((rc:string) => (
                  <span key={rc} className={clsx("text-xs px-2 py-0.5 rounded-full font-medium",
                    roleColor[rc] ?? "bg-gray-100 text-gray-600")}>
                    {roleLabel[rc] ?? rc}
                  </span>
                ))}
              </div>

              <div className="space-y-2">
                <Link to={`/users/${selectedUser.id}`}
                  className="btn-primary w-full text-sm text-center flex items-center justify-center gap-2">
                  <UserCheck className="w-4 h-4"/> Gestionar perfil
                </Link>
                {hasRole("ADM","COO") && (
                  <button onClick={() => statusMut.mutate({
                    id: selectedUser.id,
                    status: selectedUser.status === "active" ? "inactive" : "active"
                  })} className={clsx(
                    "w-full text-sm flex items-center justify-center gap-2 py-2 px-4 rounded-lg border transition-colors",
                    selectedUser.status === "active"
                      ? "text-red-600 border-red-200 hover:bg-red-50"
                      : "text-green-700 border-green-200 hover:bg-green-50"
                  )}>
                    {selectedUser.status === "active"
                      ? <><ToggleLeft className="w-4 h-4"/> Desactivar</>
                      : <><ToggleRight className="w-4 h-4"/> Activar</>}
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {showCreate && <UserCreateModal onClose={() => setShowCreate(false)}/>}
    </div>
  )
}
