import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { Link } from "react-router-dom"
import { useAuthStore } from "@/store/auth"
import { tiApi } from "@/services/api"
import ProgressBar from "@/components/ProgressBar"
import AlertBadge from "@/components/AlertBadge"
import EmptyState from "@/components/EmptyState"
import { BookOpen, Plus, ChevronRight, AlertTriangle } from "lucide-react"
import TICreateModal from "@/components/TICreateModal"
import type { TI, Alert } from "@/types"

const statusLabel: Record<string, string> = {
  draft: "Borrador", anteproject: "Anteproyecto", in_progress: "En progreso",
  preliminary_defense: "Def. Preliminar", final_defense: "Def. Final",
  approved: "Aprobado", withdrawn: "Retirado",
}

export default function TIList() {
  const { user, hasRole } = useAuthStore()
  const [showCreate, setShowCreate] = useState(false)
  const qc = useQueryClient()
  const params = hasRole("EST") ? { student_id: user?.id } : hasRole("TUT") ? { tutor_id: user?.id } : {}

  const { data, isLoading } = useQuery({
    queryKey: ["tis", params],
    queryFn: () => tiApi.list(params).then(r => r.data),
  })

  return (
    <div className="max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Trabajos de Investigación</h1>
          <p className="text-sm text-gray-500 mt-0.5">{data?.total ?? 0} registros</p>
        </div>
        {hasRole("ADM","COO") && (
          <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" /> Nuevo TI
          </button>
        )}
      </div>

      {isLoading && (
        <div className="space-y-3">
          {[1,2,3].map(i => <div key={i} className="card h-24 animate-pulse bg-gray-100" />)}
        </div>
      )}

      {!isLoading && data?.items?.length === 0 && (
        <EmptyState icon={BookOpen} title="No hay TIs registrados"
          description="Los trabajos de investigación aparecerán aquí una vez asignados." />
      )}

      <div className="space-y-3">
        {data?.items?.map((ti: TI & { active_alerts?: number }) => (
          <Link key={ti.id} to={`/ti/${ti.id}`}
            className="card flex items-center gap-4 hover:border-primary-500/30 hover:shadow-md transition-all group">
            <div className="w-10 h-10 bg-primary-50 rounded-xl flex items-center justify-center flex-shrink-0 group-hover:bg-primary-700 transition-colors">
              <BookOpen className="w-5 h-5 text-primary-700 group-hover:text-white transition-colors" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <p className="font-medium text-gray-900 truncate">{ti.title}</p>
                <span className="badge-gray flex-shrink-0">{statusLabel[ti.status] ?? ti.status}</span>
              </div>
              <p className="text-xs text-gray-500 mb-2">{ti.knowledge_area}</p>
              <ProgressBar value={ti.progress_percent} size="sm" />
            </div>
            {(ti.active_alerts ?? 0) > 0 && (
              <div className="flex items-center gap-1 text-danger flex-shrink-0">
                <AlertTriangle className="w-4 h-4" />
                <span className="text-xs font-medium">{ti.active_alerts}</span>
              </div>
            )}
            <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-primary-500 flex-shrink-0" />
          </Link>
        ))}
      </div>

      {showCreate && (
        <TICreateModal
          onClose={() => setShowCreate(false)}
          onSuccess={() => qc.invalidateQueries({ queryKey: ["tis"] })}
        />
      )}
    </div>
  )
}
