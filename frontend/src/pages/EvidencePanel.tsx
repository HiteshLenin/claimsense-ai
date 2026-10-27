import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api'

type DocRow = { name: string; status: string }

export default function EvidencePanel() {
  const { claimId } = useParams<{ claimId: string }>()
  const [docs, setDocs] = useState<DocRow[]>([])
  const [msg, setMsg] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!claimId) return
    api.listDocuments(claimId)
      .then((rows: any[]) => setDocs(rows.map((d) => ({
        name: d.filename,
        status: d.extraction_status || 'pending',
      }))))
      .catch(() => {})
  }, [claimId])

  async function onPick(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0]
    e.target.value = ''
    if (!f || !claimId) return
    setBusy(true)
    setMsg('')
    try {
      const r: any = await api.uploadDocument(claimId, f)
      if (r && r.id) {
        setDocs((prev) => [...prev, { name: r.filename || f.name, status: r.extraction_status || 'pending' }])
        setMsg(`Uploaded ${r.filename || f.name}`)
      } else if (r && r.detail) {
        setMsg(String(r.detail))
      } else {
        setMsg('Upload finished, but the server response was unexpected.')
      }
    } catch {
      setMsg('Upload failed — is the backend running?')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="card">
      <h3>Evidence</h3>
      <p className="muted">Upload claim documents — PDF, PNG or JPG, up to 25MB. Exact duplicates are refused.</p>
      <input type="file" accept=".pdf,.png,.jpg,.jpeg" onChange={onPick} disabled={busy} />
      {msg && <p>{msg}</p>}
      {docs.length > 0 && (
        <table className="table">
          <thead><tr><th>File</th><th>Status</th></tr></thead>
          <tbody>
            {docs.map((d, i) => (
              <tr key={i}><td>{d.name}</td><td>{d.status}</td></tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
