import { Link } from "react-router-dom"
import { GraduationCap } from "lucide-react"
export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center gap-4 text-center p-8">
      <GraduationCap className="w-16 h-16 text-gray-300" />
      <h1 className="text-4xl font-bold text-gray-800">404</h1>
      <p className="text-gray-500">Página no encontrada</p>
      <Link to="/dashboard" className="btn-primary">Ir al dashboard</Link>
    </div>
  )
}
