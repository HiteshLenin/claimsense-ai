import { useState } from 'react'
import { api } from '../api'

/** SDD screen: decision panel — adjuster action, MANDATORY rationale,
 *  recorded against the claim version being reviewed. */
export default function DecisionPanel({ claimId, claimVersion, onDecided }: {
  claimId: string; claimVersion: number; onDecided?: () => void
}) {
  const [action, setAction] = useState('approve')
  const [rationale, setRationale] = useState('')
  const [saving, setSaving] = useState(false)
  const [done, setDone] = useState(false)
  const [error, setError] = useState('')

  async function submit() {
    if (rationale.trim().length < 10) { setError('Rationale is required (min 10 chars).'); return }
    setSaving(true); setError('')
    try {
      await api.recordDecision(claimId, { action, rationale, recorded_by: 'adjuster-1' })
      setDone(true)
      onDecided?.()
    } catch (e) {
      setError(String(e))
    } finally {
      setSaving(false)
    }
  }

  if (done) {
    return <div className="card"><p className="alert-ok" style={{ margin: 0 }}>
      Decision recorded for claim version {claimVersion}. The claim is now decided.
    </p></div>
  }

  return (
    <div className="card">
      <h3>Adjuster decision <span className="muted" style={{ fontWeight: 'normal' }}>(claim version {claimVersion})</span></h3>
      <p className="muted" style={{ marginTop: 0 }}>AI output is advisory — this decision is the only thing that changes the claim's disposition.</p>
      {error && <p className="alert-error">{error}</p>}
      <div className="field">
        <label>Action</label>
        <select value={action} onChange={(e) => setAction(e.target.value)}>
          <option value="approve">Approve</option>
          <option value="deny">Deny</option>
          <option value="request_info">Request info</option>
          <option value="refer">Refer to SIU</option>
        </select>
      </div>
      <div className="field">
        <label>Rationale (required, min 10 characters)</label>
        <textarea value={rationale} onChange={(e) => setRationale(e.target.value)}
          placeholder="Why is this the right call? Reference the analysis above." />
      </div>
      <button className="btn" onClick={submit} disabled={saving}>{saving ? 'Recording…' : 'Record decision'}</button>
    </div>
  )
}
