import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useAuthStore } from "@/store/auth"
import { authApi } from "@/services/api"
import axios from "axios"
import { GraduationCap, Eye, EyeOff, Lock, Mail, Shield } from "lucide-react"

const schema = z.object({
  email:     z.string().email("Email inválido"),
  password:  z.string().min(1, "Contraseña requerida"),
  totp_code: z.string().optional(),
})
type Form = z.infer<typeof schema>

export default function Login() {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [showPass, setShowPass] = useState(false)
  const [needsTotp, setNeedsTotp] = useState(false)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm<Form>({
    resolver: zodResolver(schema)
  })

  const onSubmit = async (data: Form) => {
    setLoading(true)
    setError("")
    try {
      // Step 1: Login → get token
      const res = await authApi.login(data.email, data.password, data.totp_code)

      if (res.data.requires_totp) {
        setNeedsTotp(true)
        setLoading(false)
        return
      }

      const token = res.data.access_token

      // Step 2: Get user profile WITH token in header (store not set yet)
      const meRes = await axios.get("/api/auth/me", {
        headers: { Authorization: `Bearer ${token}` }
      })
      const user = meRes.data
      const roles = user.roles
        ?.filter((r: { is_active: boolean }) => r.is_active)
        .map((r: { role_code: string }) => r.role_code) ?? []

      // Step 3: Now save to store and redirect
      setAuth(token, user, roles)
      navigate("/dashboard")

    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } }
      setError(err?.response?.data?.detail ?? "Credenciales incorrectas")
    }
    setLoading(false)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-700 via-primary-500 to-info flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-white/20 rounded-2xl mb-4 backdrop-blur">
            <GraduationCap className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white">SIGTPI</h1>
          <p className="text-white/70 text-sm mt-1">Sistema de Gestión de Tutorías de Postgrado</p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <h2 className="text-xl font-bold text-gray-800 mb-6">
            {needsTotp ? "Verificación MFA" : "Iniciar sesión"}
          </h2>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {!needsTotp && (
              <>
                <div>
                  <label className="label">Correo electrónico</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input {...register("email")} type="email"
                      placeholder="usuario@institucion.edu.co"
                      className="input pl-10" autoComplete="email" />
                  </div>
                  {errors.email && <p className="text-xs text-red-500 mt-1">{errors.email.message}</p>}
                </div>
                <div>
                  <label className="label">Contraseña</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input {...register("password")}
                      type={showPass ? "text" : "password"}
                      className="input pl-10 pr-10"
                      autoComplete="current-password" />
                    <button type="button" onClick={() => setShowPass(v => !v)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                      {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {errors.password && <p className="text-xs text-red-500 mt-1">{errors.password.message}</p>}
                </div>
              </>
            )}

            {needsTotp && (
              <div>
                <div className="flex items-center gap-2 mb-4 text-purple-600">
                  <Shield className="w-5 h-5" />
                  <p className="text-sm font-medium">Ingresa el código de tu autenticador</p>
                </div>
                <input {...register("totp_code")} type="text" inputMode="numeric"
                  placeholder="000000" maxLength={6}
                  className="input text-center text-2xl tracking-widest font-mono" autoFocus />
              </div>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full mt-2">
              {loading ? "Verificando..." : needsTotp ? "Verificar código" : "Ingresar"}
            </button>
          </form>

          <p className="text-xs text-center text-gray-400 mt-6">
            Sistema de uso interno — Institución académica
          </p>
        </div>
      </div>
    </div>
  )
}
