import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { documentsApi, type Document, type DocumentVersion } from "@/services/documents"
import { useAuthStore } from "@/store/auth"
import {
  FileText, Download, Clock, Shield, AlertTriangle,
  ChevronDown, ChevronUp, CheckCircle, Hash
} from "lucide-react"
import { format, parseISO } from "date-fns"
import { es } from "date-fns/locale"
import clsx from "clsx"

const similarityColor = (pct: number | null) => {
  if (pct === null) return "text-gray-400"
  if (pct <= 15) return "text-green-600"
  if (pct <= 30) return "text-yellow-600"
  return "text-red-600"
}

const similarityBg = (pct: number | null) => {
  if (pct === null) return "bg-gray-100"
  if (pct <= 15) return "bg-green-50 border-green-200"
  if (pct <= 30) return "bg-yellow-50 border-yellow-200"
  return "bg-red-50 border-red-200"
}

interface Props { doc: Document; tiId: string }

export default function DocumentCard({ doc, tiId }: Props) {
  const [expanded, setExpanded] = useState(false)
  const [signing, setSigning] = useState(false)
  const [signMsg, setSignMsg] = useState<string|null>(null)
  const { hasRole } = useAuthStore()
  const qc = useQueryClient()

  const latest = doc.versions[doc.versions.length - 1]
  const simPct = latest?.similarity_percent ?? null

  const handleSign = async () => {
    if (!latest) return
    setSigning(true)
    setSignMsg(null)
    try {
      await documentsApi.sign(doc.id, latest.sha256_hash, doc.doc_type)
      setSignMsg("✓ Documento firmado digitalmente")
      qc.invalidateQueries({ queryKey: ["documents", tiId] })
    } catch (e: any) {
      setSignMsg("✗ " + (e.response?.data?.detail ?? "Error al firmar"))
    }
    setSigning(false)
  }

  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden bg-white">
      {/* Header */}
      <div className="flex items-start gap-3 p-4">
        <div className="w-10 h-10 bg-primary-50 rounded-lg flex items-center justify-center flex-shrink-0">
          <FileText className="w-5 h-5 text-primary-700"/>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h4 className="font-medium text-gray-900 text-sm">{doc.title}</h4>
              {doc.description && <p className="text-xs text-gray-500 mt-0.5">{doc.description}</p>}
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              {latest?.is_signed && (
                <span className="flex items-center gap-1 text-xs text-green-700 bg-green-50 px-2 py-0.5 rounded-full border border-green-200">
                  <Shield className="w-3 h-3"/> Firmado
                </span>
              )}
              {simPct !== null && (
                <span className={clsx("text-xs font-medium px-2 py-0.5 rounded-full border",
                  similarityBg(simPct), similarityColor(simPct))}>
                  {simPct}% similitud
                </span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3"/>
              {latest ? format(parseISO(latest.created_at), "d MMM yyyy", { locale: es }) : "—"}
            </span>
            <span>v{doc.current_version}</span>
            <span>{doc.versions.length} versión{doc.versions.length !== 1 ? "es" : ""}</span>
            <span className="bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">{doc.doc_type}</span>
          </div>
        </div>
      </div>

      {/* Similarity alert */}
      {simPct !== null && simPct > 30 && (
        <div className="mx-4 mb-3 flex items-center gap-2 p-2.5 bg-red-50 rounded-lg border border-red-200 text-xs text-red-700">
          <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0"/>
          Similitud alta ({simPct}%). El tutor debe revisar este documento antes de aprobarlo.
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2 px-4 pb-4">
        <button onClick={() => documentsApi.download(doc.id)}
          className="flex items-center gap-1.5 text-xs btn-secondary py-1.5 px-3">
          <Download className="w-3.5 h-3.5"/> Descargar
        </button>
        {!latest?.is_signed && hasRole("TUT","COO","DIR","ADM") && (
          <button onClick={handleSign} disabled={signing}
            className="flex items-center gap-1.5 text-xs btn-primary py-1.5 px-3">
            <Shield className="w-3.5 h-3.5"/>
            {signing ? "Firmando..." : "Firmar digitalmente"}
          </button>
        )}
        <button onClick={() => setExpanded(v => !v)}
          className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 ml-auto">
          {expanded ? <ChevronUp className="w-3.5 h-3.5"/> : <ChevronDown className="w-3.5 h-3.5"/>}
          {expanded ? "Ocultar" : "Ver versiones"}
        </button>
      </div>

      {signMsg && (
        <p className={clsx("px-4 pb-3 text-xs", signMsg.startsWith("✓") ? "text-green-600" : "text-red-600")}>
          {signMsg}
        </p>
      )}

      {/* Version history */}
      {expanded && (
        <div className="border-t border-gray-100 bg-gray-50 p-4">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Historial de versiones</p>
          <div className="space-y-2">
            {[...doc.versions].reverse().map((v: DocumentVersion) => (
              <div key={v.id} className="flex items-center gap-3 p-2.5 bg-white rounded-lg border border-gray-100">
                <div className="w-7 h-7 bg-primary-700 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0">
                  v{v.version_number}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-gray-800 truncate">{v.filename}</p>
                  <div className="flex items-center gap-2 text-xs text-gray-400 mt-0.5">
                    <span>{format(parseISO(v.created_at), "d MMM yyyy HH:mm", { locale: es })}</span>
                    <span>{(v.file_size / 1024).toFixed(0)} KB</span>
                    {v.is_signed && <span className="text-green-600 flex items-center gap-0.5"><Shield className="w-3 h-3"/>Firmado</span>}
                  </div>
                  <div className="flex items-center gap-1 text-xs text-gray-300 mt-0.5 font-mono">
                    <Hash className="w-3 h-3"/>
                    {v.sha256_hash.slice(0,16)}…
                  </div>
                </div>
                <div className="flex items-center gap-1 flex-shrink-0">
                  {v.similarity_percent !== null && (
                    <span className={clsx("text-xs font-medium", similarityColor(v.similarity_percent))}>
                      {v.similarity_percent}%
                    </span>
                  )}
                  <button onClick={() => documentsApi.download(doc.id, v.version_number)}
                    className="p-1.5 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg">
                    <Download className="w-3.5 h-3.5"/>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
