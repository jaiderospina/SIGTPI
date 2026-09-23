import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { useParams, Link } from "react-router-dom"
import { useAuthStore } from "@/store/auth"
import { tiApi } from "@/services/api"
import { documentsApi } from "@/services/documents"
import DocumentCard from "@/components/DocumentCard"
import DocumentUpload from "@/components/DocumentUpload"
import EmptyState from "@/components/EmptyState"
import { ArrowLeft, Upload, FileText, Shield, AlertTriangle } from "lucide-react"
import ProgressBar from "@/components/ProgressBar"

export default function TIDocuments() {
  const { id } = useParams<{ id: string }>()
  const { token, hasRole } = useAuthStore()
  const [showUpload, setShowUpload] = useState(false)

  const { data: ti } = useQuery({
    queryKey: ["ti", id],
    queryFn: () => tiApi.get(id!).then(r => r.data),
    enabled: !!id,
  })

  const { data: docs, isLoading } = useQuery({
    queryKey: ["documents", id],
    queryFn: () => documentsApi.list(id!),
    enabled: !!id,
  })

  const canUpload = hasRole("EST","TUT","COO","ADM")
  const docsArr = docs?.items ?? docs ?? []
  const highSimilarity = docsArr.filter((d: any) => {
    const v = d.versions?.[d.versions.length-1]
    return v?.similarity_percent !== null && v?.similarity_percent > 30
  })

  return (
    <div className="max-w-4xl mx-auto">
      <Link to={`/ti/${id}`} className="flex items-center gap-2 text-sm text-gray-500 hover:text-primary-700 mb-6 group">
        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform"/> Volver al TI
      </Link>

      {ti && (
        <div className="card mb-6">
          <h1 className="font-bold text-gray-900 mb-1">{ti.title}</h1>
          <p className="text-sm text-gray-500 mb-3">{ti.knowledge_area}</p>
          <ProgressBar value={ti.progress_percent} label="Avance general"/>
        </div>
      )}

      {/* Alert: high similarity docs */}
      {highSimilarity.length > 0 && (
        <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-xl mb-4">
          <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5"/>
          <div>
            <p className="text-sm font-semibold text-red-700">{highSimilarity.length} documento{highSimilarity.length>1?"s":""} con similitud alta</p>
            <p className="text-xs text-red-600 mt-0.5">Requieren revisión del tutor antes de continuar.</p>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Repositorio documental</h2>
          <p className="text-sm text-gray-500">{docsArr.length} documento{docsArr.length !== 1 ? "s" : ""}</p>
        </div>
        {canUpload && (
          <button onClick={() => setShowUpload(true)}
            className="btn-primary flex items-center gap-2 text-sm">
            <Upload className="w-4 h-4"/> Cargar documento
          </button>
        )}
      </div>

      {isLoading && (
        <div className="space-y-3">
          {[1,2,3].map(i => <div key={i} className="h-24 bg-gray-100 rounded-xl animate-pulse"/>)}
        </div>
      )}

      {!isLoading && docsArr.length === 0 && (
        <EmptyState icon={FileText} title="Sin documentos"
          description="Carga el primer documento de este trabajo de investigación."
          action={canUpload ? (
            <button onClick={() => setShowUpload(true)} className="btn-primary text-sm flex items-center gap-2">
              <Upload className="w-4 h-4"/> Cargar primer documento
            </button>
          ) : undefined}
        />
      )}

      <div className="space-y-3">
        {docsArr.map((doc: any) => (
          <DocumentCard key={doc.id} doc={doc} tiId={id!}/>
        ))}
      </div>

      {showUpload && (
        <DocumentUpload tiId={id!} onClose={() => setShowUpload(false)}/>
      )}
    </div>
  )
}
