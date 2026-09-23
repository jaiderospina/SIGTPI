import axios from "axios"
import { useAuthStore } from "@/store/auth"

const getHeaders = () => ({
  Authorization: `Bearer ${useAuthStore.getState().token}`
})

export interface DocumentVersion {
  id: string
  filename: string
  file_size: number
  mime_type: string
  sha256_hash: string
  version_number: number
  uploaded_by: string
  created_at: string
  similarity_percent: number | null
  is_signed: boolean
}

export interface Document {
  id: string
  ti_id: string
  milestone_id: string | null
  title: string
  description: string | null
  doc_type: string
  current_version: number
  versions: DocumentVersion[]
  created_at: string
  updated_at: string
}

export const documentsApi = {
  list: (ti_id: string) =>
    axios.get(`/api/documents/documents/ti/${ti_id}`, { headers: getHeaders() })
      .then(r => r.data),

  upload: (ti_id: string, formData: FormData) =>
    axios.post(`/api/documents/documents/upload`, formData, {
      headers: { ...getHeaders(), "Content-Type": "multipart/form-data" }
    }).then(r => r.data),

  download: (doc_id: string, version?: number) => {
    const url = version
      ? `/api/documents/documents/${doc_id}/download?version=${version}`
      : `/api/documents/documents/${doc_id}/download`
    const link = document.createElement("a")
    link.href = url
    link.setAttribute("download", "")
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  },

  getSimilarity: (doc_id: string) =>
    axios.get(`/api/documents/documents/${doc_id}/similarity`, { headers: getHeaders() })
      .then(r => r.data),

  sign: (doc_id: string, doc_hash: string, doc_type: string) =>
    axios.post("/api/pki/pki/sign", {
      document_id: doc_id,
      document_type: doc_type,
      document_hash: doc_hash,
      signer_id: useAuthStore.getState().user?.id,
    }, { headers: getHeaders() }).then(r => r.data),
}
