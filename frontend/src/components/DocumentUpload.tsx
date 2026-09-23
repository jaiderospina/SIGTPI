import { useState, useRef } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { documentsApi } from "@/services/documents"
import { Upload, File, X, CheckCircle } from "lucide-react"
import clsx from "clsx"

interface Props {
  tiId: string
  milestoneId?: string
  onClose: () => void
}

const DOC_TYPES = [
  { value:"anteproject",    label:"Anteproyecto" },
  { value:"advance",        label:"Avance de investigación" },
  { value:"chapter",        label:"Capítulo" },
  { value:"full_draft",     label:"Borrador completo" },
  { value:"final",          label:"Documento final" },
  { value:"minutes",        label:"Acta de sesión" },
  { value:"other",          label:"Otro" },
]

export default function DocumentUpload({ tiId, milestoneId, onClose }: Props) {
  const qc = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File|null>(null)
  const [title, setTitle] = useState("")
  const [docType, setDocType] = useState("advance")
  const [description, setDescription] = useState("")
  const [drag, setDrag] = useState(false)
  const [progress, setProgress] = useState(0)
  const [done, setDone] = useState(false)

  const upload = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error("No file")
      const fd = new FormData()
      fd.append("file", file)
      fd.append("ti_id", tiId)
      fd.append("title", title || file.name)
      fd.append("doc_type", docType)
      fd.append("description", description)
      if (milestoneId) fd.append("milestone_id", milestoneId)
      return documentsApi.upload(tiId, fd)
    },
    onSuccess: () => {
      setDone(true)
      qc.invalidateQueries({ queryKey: ["documents", tiId] })
      setTimeout(onClose, 1500)
    },
  })

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDrag(false)
    const f = e.dataTransfer.files[0]
    if (f) setFile(f)
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024*1024) return `${(bytes/1024).toFixed(0)} KB`
    return `${(bytes/1024/1024).toFixed(1)} MB`
  }

  if (done) return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl p-8 text-center max-w-sm w-full">
        <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3"/>
        <p className="font-semibold text-gray-800">Documento cargado exitosamente</p>
        <p className="text-sm text-gray-500 mt-1">El análisis de similitud se ejecutará en segundo plano.</p>
      </div>
    </div>
  )

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg">
        <div className="flex items-center justify-between p-6 border-b border-gray-100">
          <h2 className="font-bold text-gray-900">Cargar documento</h2>
          <button onClick={onClose} className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg">
            <X className="w-5 h-5"/>
          </button>
        </div>

        <div className="p-6 space-y-4">
          {/* Drop zone */}
          <div
            onDragOver={e => { e.preventDefault(); setDrag(true) }}
            onDragLeave={() => setDrag(false)}
            onDrop={handleDrop}
            onClick={() => fileRef.current?.click()}
            className={clsx(
              "border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors",
              drag ? "border-primary-500 bg-primary-50" : "border-gray-200 hover:border-primary-300 hover:bg-gray-50",
              file && "border-green-300 bg-green-50"
            )}>
            <input ref={fileRef} type="file" className="hidden"
              accept=".pdf,.doc,.docx,.odt,.txt"
              onChange={e => e.target.files?.[0] && setFile(e.target.files[0])}/>
            {file ? (
              <div>
                <File className="w-8 h-8 text-green-600 mx-auto mb-2"/>
                <p className="font-medium text-gray-800 text-sm">{file.name}</p>
                <p className="text-xs text-gray-500 mt-1">{formatSize(file.size)}</p>
              </div>
            ) : (
              <div>
                <Upload className="w-8 h-8 text-gray-300 mx-auto mb-2"/>
                <p className="text-sm font-medium text-gray-600">Arrastra un archivo o haz clic para seleccionar</p>
                <p className="text-xs text-gray-400 mt-1">PDF, DOCX, ODT, TXT · Máx. 50 MB</p>
              </div>
            )}
          </div>

          <div>
            <label className="label">Título del documento</label>
            <input value={title} onChange={e => setTitle(e.target.value)}
              placeholder={file?.name ?? "Ej: Capítulo 3 — Metodología"}
              className="input"/>
          </div>

          <div>
            <label className="label">Tipo de documento</label>
            <select value={docType} onChange={e => setDocType(e.target.value)} className="input">
              {DOC_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>

          <div>
            <label className="label">Descripción (opcional)</label>
            <textarea value={description} onChange={e => setDescription(e.target.value)}
              rows={2} placeholder="Breve descripción del contenido o cambios en esta versión..."
              className="input resize-none"/>
          </div>

          {upload.isError && (
            <p className="text-xs text-red-600 bg-red-50 p-2 rounded-lg">
              {(upload.error as any)?.response?.data?.detail ?? "Error al cargar el archivo."}
            </p>
          )}
        </div>

        <div className="flex gap-3 p-6 pt-0">
          <button onClick={onClose} className="btn-secondary flex-1">Cancelar</button>
          <button onClick={() => upload.mutate()} disabled={!file || upload.isPending} className="btn-primary flex-1">
            {upload.isPending ? "Cargando..." : "Cargar documento"}
          </button>
        </div>
      </div>
    </div>
  )
}
