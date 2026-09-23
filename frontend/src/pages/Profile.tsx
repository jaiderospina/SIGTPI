import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useAuthStore } from "@/store/auth"
import axios from "axios"
import {
  User, Mail, Phone, BookOpen, Shield, Key,
  Check, AlertCircle, Smartphone, Copy, EyeOff, Eye
} from "lucide-react"
import clsx from "clsx"

const profileSchema = z.object({
  full_name:         z.string().min(2, "Mínimo 2 caracteres"),
  phone:             z.string().optional(),
  bio:               z.string().optional(),
  area_of_expertise: z.string().optional(),
})
type ProfileForm = z.infer<typeof profileSchema>

const passwordSchema = z.object({
  current_password: z.string().min(1, "Requerido"),
  new_password:     z.string().min(10, "Mínimo 10 caracteres")
    .regex(/[A-Z]/, "Debe incluir mayúscula")
    .regex(/[0-9]/, "Debe incluir número")
    .regex(/[!@#$%^&*]/, "Debe incluir símbolo (!@#$%^&*)"),
  confirm_password: z.string(),
}).refine(d => d.new_password === d.confirm_password, {
  message: "Las contraseñas no coinciden",
  path: ["confirm_password"],
})
type PasswordForm = z.infer<typeof passwordSchema>

const AREAS = [
  "Ciberseguridad y Ciberdefensa",
  "Redes y Telecomunicaciones",
  "Ciencia de Datos e Inteligencia Artificial",
  "Ingeniería de Software",
  "Gestión de Sistemas de Información",
  "Administración de Sistemas",
  "Investigación Académica",
]

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

function Alert({ type, text }: { type:"ok"|"err"; text:string }) {
  return (
    <div className={clsx("flex items-center gap-2 p-3 rounded-lg text-sm mb-4",
      type==="ok" ? "bg-green-50 text-green-700 border border-green-200"
                  : "bg-red-50 text-red-700 border border-red-200")}>
      {type==="ok" ? <Check className="w-4 h-4 flex-shrink-0"/> : <AlertCircle className="w-4 h-4 flex-shrink-0"/>}
      {text}
    </div>
  )
}

export default function Profile() {
  const { token } = useAuthStore()
  const qc = useQueryClient()
  const [tab, setTab] = useState<"info"|"security"|"roles">("info")
  const [msg, setMsg] = useState<{type:"ok"|"err"; text:string}|null>(null)
  const [showPass, setShowPass] = useState({ cur:false, new:false, con:false })
  const [totpSetup, setTotpSetup] = useState<{secret:string; qr_uri:string; backup_codes:string[]}|null>(null)
  const [totpCode, setTotpCode] = useState("")
  const [copied, setCopied] = useState(false)

  const headers = { Authorization: `Bearer ${token}` }
  const flash = (type:"ok"|"err", text:string) => {
    setMsg({ type, text })
    setTimeout(() => setMsg(null), 4000)
  }

  // Load profile from USER-SERVICE (has full profile data)
  const { data: profile, isLoading } = useQuery({
    queryKey: ["my-full-profile"],
    queryFn: () => axios.get("/api/users/users/me", { headers }).then(r => r.data),
  })

  const profileForm = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema),
    values: {
      full_name:         profile?.full_name ?? "",
      phone:             profile?.phone ?? "",
      bio:               profile?.bio ?? "",
      area_of_expertise: profile?.area_of_expertise ?? "",
    }
  })

  const passwordForm = useForm<PasswordForm>({ resolver: zodResolver(passwordSchema) })

  // Update profile in USER-SERVICE using /me endpoint (no ID needed)
  const updateProfile = useMutation({
    mutationFn: (data: ProfileForm) =>
      axios.patch(`/api/users/users/${profile?.id}`, data, { headers }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["my-full-profile"] })
      flash("ok", "Perfil actualizado correctamente.")
    },
    onError: (e:any) => flash("err", e.response?.data?.detail ?? "Error al guardar. Verifica los campos."),
  })

  const changePassword = useMutation({
    mutationFn: (data: PasswordForm) =>
      axios.post("/api/auth/password/change", {
        current_password: data.current_password,
        new_password: data.new_password,
      }, { headers }),
    onSuccess: () => {
      passwordForm.reset()
      flash("ok", "Contraseña actualizada. Tendrás que volver a iniciar sesión.")
    },
    onError: (e:any) => flash("err", e.response?.data?.detail ?? "Contraseña actual incorrecta."),
  })

  const setupMFA = useMutation({
    mutationFn: () => axios.post("/api/auth/mfa/setup", {}, { headers }),
    onSuccess: (r) => setTotpSetup(r.data),
    onError: (e:any) => flash("err", e.response?.data?.detail ?? "Error al iniciar MFA."),
  })

  const verifyMFA = useMutation({
    mutationFn: () => axios.post("/api/auth/mfa/verify", { totp_code: totpCode }, { headers }),
    onSuccess: () => {
      setTotpSetup(null)
      setTotpCode("")
      qc.invalidateQueries({ queryKey: ["my-full-profile"] })
      flash("ok", "MFA activado. Tu cuenta ahora requiere código al iniciar sesión.")
    },
    onError: () => flash("err", "Código incorrecto. Verifica tu app autenticadora."),
  })

  const disableMFA = useMutation({
    mutationFn: () => axios.post("/api/auth/mfa/disable", {}, { headers }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["my-full-profile"] })
      flash("ok", "MFA desactivado.")
    },
  })

  const copySecret = () => {
    if (totpSetup?.secret) {
      navigator.clipboard.writeText(totpSetup.secret)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  if (isLoading) return (
    <div className="max-w-2xl mx-auto space-y-4">
      {[1,2,3].map(i => <div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse"/>)}
    </div>
  )

  const initials = (profile?.full_name ?? "U").split(" ").map((w:string)=>w[0]).join("").slice(0,2).toUpperCase()

  return (
    <div className="max-w-2xl mx-auto">
      {/* Header */}
      <div className="card mb-6">
        <div className="flex items-center gap-5">
          <div className="w-20 h-20 rounded-full bg-primary-700 text-white flex items-center justify-center text-2xl font-bold flex-shrink-0">
            {initials}
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-bold text-gray-900">{profile?.full_name}</h1>
            <p className="text-sm text-gray-500">{profile?.email}</p>
            <div className="flex flex-wrap gap-1.5 mt-2">
              {profile?.roles?.filter((r:any)=>r.is_active).map((r:any)=>(
                <span key={r.id} className={clsx("text-xs px-2 py-0.5 rounded-full font-medium",
                  roleColor[r.role_code] ?? "bg-gray-100 text-gray-600")}>
                  {roleLabel[r.role_code] ?? r.role_code}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 rounded-xl p-1 mb-6">
        {(["info","security","roles"] as const).map(t => (
          <button key={t} onClick={() => { setTab(t); setMsg(null) }}
            className={clsx("flex-1 py-2 rounded-lg text-sm font-medium transition-all",
              tab===t ? "bg-white shadow-sm text-primary-700" : "text-gray-500 hover:text-gray-700")}>
            {t==="info" ? "Información" : t==="security" ? "Seguridad" : "Roles"}
          </button>
        ))}
      </div>

      {msg && <Alert type={msg.type} text={msg.text}/>}

      {/* ── Tab: Info ─────────────────────────────────────────────────────── */}
      {tab==="info" && (
        <div className="card">
          <h2 className="font-semibold text-gray-800 mb-5">Información personal</h2>
          <form onSubmit={profileForm.handleSubmit(d => updateProfile.mutate(d))} className="space-y-4">

            <div>
              <label className="label">Nombre completo *</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
                <input {...profileForm.register("full_name")} className="input pl-10"
                  placeholder="Nombre y apellidos"/>
              </div>
              {profileForm.formState.errors.full_name && (
                <p className="text-xs text-red-500 mt-1">{profileForm.formState.errors.full_name.message}</p>
              )}
            </div>

            <div>
              <label className="label">Correo electrónico</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
                <input value={profile?.email ?? ""} disabled className="input pl-10 bg-gray-50 text-gray-400 cursor-not-allowed"/>
              </div>
              <p className="text-xs text-gray-400 mt-1">El correo institucional no se puede modificar.</p>
            </div>

            <div>
              <label className="label">Teléfono</label>
              <div className="relative">
                <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
                <input {...profileForm.register("phone")} className="input pl-10" placeholder="310 000 0000"/>
              </div>
            </div>

            <div>
              <label className="label">Área de especialización</label>
              <div className="relative">
                <BookOpen className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/>
                <select {...profileForm.register("area_of_expertise")} className="input pl-10">
                  <option value="">Selecciona un área...</option>
                  {AREAS.map(a => <option key={a} value={a}>{a}</option>)}
                </select>
              </div>
            </div>

            <div>
              <label className="label">Biografía / Presentación</label>
              <textarea {...profileForm.register("bio")} rows={4} className="input resize-none"
                placeholder="Describe tu experiencia, líneas de investigación e intereses..."/>
            </div>

            <button type="submit" disabled={updateProfile.isPending} className="btn-primary w-full">
              {updateProfile.isPending ? "Guardando..." : "Guardar cambios"}
            </button>
          </form>
        </div>
      )}

      {/* ── Tab: Security ─────────────────────────────────────────────────── */}
      {tab==="security" && (
        <div className="space-y-4">
          {/* Password */}
          <div className="card">
            <h2 className="font-semibold text-gray-800 mb-5">Cambiar contraseña</h2>
            <form onSubmit={passwordForm.handleSubmit(d => changePassword.mutate(d))} className="space-y-4">
              {([
                ["current_password","Contraseña actual","cur"],
                ["new_password","Nueva contraseña","new"],
                ["confirm_password","Confirmar nueva contraseña","con"],
              ] as const).map(([field,label,key]) => (
                <div key={field}>
                  <label className="label">{label}</label>
                  <div className="relative">
                    <input {...passwordForm.register(field)}
                      type={showPass[key] ? "text" : "password"}
                      className="input pr-10"/>
                    <button type="button"
                      onClick={() => setShowPass(p => ({ ...p, [key]: !p[key] }))}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                      {showPass[key] ? <EyeOff className="w-4 h-4"/> : <Eye className="w-4 h-4"/>}
                    </button>
                  </div>
                  {passwordForm.formState.errors[field] && (
                    <p className="text-xs text-red-500 mt-1">{passwordForm.formState.errors[field]?.message}</p>
                  )}
                </div>
              ))}
              <p className="text-xs text-gray-400">Mínimo 10 caracteres · Una mayúscula · Un número · Un símbolo (!@#$%^&*)</p>
              <button type="submit" disabled={changePassword.isPending} className="btn-primary w-full">
                {changePassword.isPending ? "Cambiando..." : "Cambiar contraseña"}
              </button>
            </form>
          </div>

          {/* MFA */}
          <div className="card">
            <h2 className="font-semibold text-gray-800 mb-2 flex items-center gap-2">
              <Smartphone className="w-4 h-4 text-primary-500"/>
              Autenticación de dos factores (MFA)
            </h2>

            {!totpSetup && !profile?.totp_enabled && (
              <div>
                <p className="text-sm text-gray-600 mb-4">
                  Añade una capa extra de seguridad. Necesitarás Google Authenticator, Authy u otra app TOTP.
                </p>
                <button onClick={() => setupMFA.mutate()} disabled={setupMFA.isPending}
                  className="btn-primary flex items-center gap-2 text-sm">
                  <Shield className="w-4 h-4"/>
                  {setupMFA.isPending ? "Generando..." : "Activar MFA"}
                </button>
              </div>
            )}

            {totpSetup && (
              <div className="space-y-4">
                <p className="text-sm text-gray-600">
                  Escanea el código QR con tu app autenticadora, o introduce la clave manual:
                </p>
                {/* QR Code rendered as text URI (can be enhanced with qrcode library) */}
                <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
                  <p className="text-xs text-gray-500 mb-2 font-medium">URI de configuración:</p>
                  <div className="flex items-center gap-2">
                    <code className="text-xs bg-white border border-gray-200 rounded p-2 flex-1 break-all text-gray-700">
                      {totpSetup.qr_uri}
                    </code>
                    <button onClick={copySecret}
                      className="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg flex-shrink-0">
                      {copied ? <Check className="w-4 h-4 text-green-500"/> : <Copy className="w-4 h-4"/>}
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-3 mb-1 font-medium">Clave secreta:</p>
                  <code className="text-sm font-mono bg-white border border-gray-200 rounded p-2 block tracking-widest text-center text-primary-700">
                    {totpSetup.secret}
                  </code>
                </div>
                <div>
                  <label className="label">Código de verificación</label>
                  <input value={totpCode} onChange={e => setTotpCode(e.target.value)}
                    type="text" inputMode="numeric" maxLength={6} placeholder="000000"
                    className="input text-center text-xl tracking-widest font-mono"/>
                  <p className="text-xs text-gray-400 mt-1">Introduce el código de 6 dígitos de tu app autenticadora.</p>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => setTotpSetup(null)} className="btn-secondary flex-1 text-sm">Cancelar</button>
                  <button onClick={() => verifyMFA.mutate()} disabled={totpCode.length!==6 || verifyMFA.isPending}
                    className="btn-primary flex-1 text-sm">
                    {verifyMFA.isPending ? "Verificando..." : "Confirmar y activar"}
                  </button>
                </div>
                {totpSetup.backup_codes?.length > 0 && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-3">
                    <p className="text-xs font-semibold text-yellow-800 mb-2">Códigos de respaldo (guárdalos en lugar seguro):</p>
                    <div className="grid grid-cols-2 gap-1">
                      {totpSetup.backup_codes.map((c,i) => (
                        <code key={i} className="text-xs font-mono text-yellow-700 bg-yellow-100 rounded px-2 py-1 text-center">{c}</code>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {profile?.totp_enabled && !totpSetup && (
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <Check className="w-4 h-4 text-green-600"/>
                  <p className="text-sm font-medium text-green-700">MFA activo — tu cuenta está protegida</p>
                </div>
                <button onClick={() => disableMFA.mutate()} disabled={disableMFA.isPending}
                  className="btn-secondary text-sm text-red-600 border-red-200 hover:bg-red-50">
                  {disableMFA.isPending ? "Desactivando..." : "Desactivar MFA"}
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Tab: Roles ─────────────────────────────────────────────────────── */}
      {tab==="roles" && (
        <div className="card">
          <h2 className="font-semibold text-gray-800 mb-5">Mis roles y permisos</h2>
          {(!profile?.roles || profile.roles.length===0) ? (
            <p className="text-sm text-gray-400">No tienes roles asignados.</p>
          ) : (
            <div className="space-y-3">
              {profile.roles.map((r:any) => (
                <div key={r.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className={clsx("text-sm font-semibold px-3 py-1 rounded-full",
                    roleColor[r.role_code] ?? "bg-gray-100 text-gray-600")}>
                    {roleLabel[r.role_code] ?? r.role_code}
                  </span>
                  <span className={clsx("text-xs px-2 py-0.5 rounded-full",
                    r.is_active ? "bg-green-100 text-green-600" : "bg-gray-100 text-gray-400")}>
                    {r.is_active ? "Activo" : "Inactivo"}
                  </span>
                </div>
              ))}
            </div>
          )}
          <p className="text-xs text-gray-400 mt-4">
            Para modificar roles contacta al administrador del sistema.
          </p>
        </div>
      )}
    </div>
  )
}
