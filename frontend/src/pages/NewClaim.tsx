import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

/** SDD screen: new claim form. */
export default function NewClaim() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ policy_number: '', loss_date: '', loss_type: 'collision', description: '', amount: '' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const set = (k: string) => (e: any) => setForm({ ...form, [k]: e.target.value })

  async function submit(e: any) {
    e.preventDefault()
    setSaving(true); setError('')
    try {
      await api.createClaim({ ...form, amount: Number(form.amount), loss_date: new Date(form.loss_date).toISOString() })
      navigate('/')
    } catch (err) {
      setError(String(err)); setSaving(false)
    }
  }

  return (
    <section>
      <h2 className="page-title">New claim</h2>
      <p className="page-sub">Intake a claim — it lands in the queue as open.</p>
      <div className="card" style={{ maxWidth: 560 }}>
        {error && <p className="alert-error">{error}</p>}
        <form onSubmit={submit}>
          <div className="field">
            <label>Policy number</label>
            <input placeholder="POL-100234" value={form.policy_number} onChange={set('policy_number')} required />
          </div>
          <div className="field">
            <label>Loss date</label>
            <input type="date" value={form.loss_date} onChange={set('loss_date')} required />
          </div>
          <div className="field">
            <label>Loss type</label>
            <select value={form.loss_type} onChange={set('loss_type')}>
              <option>collision</option><option>theft</option><option>vandalism</option><option>weather</option>
            </select>
          </div>
          <div className="field">
            <label>What happened?</label>
            <textarea placeholder="Describe the incident…" value={form.description} onChange={set('description')} required />
          </div>
          <div className="field">
            <label>Claimed amount ($)</label>
            <input type="number" min="1" placeholder="2500" value={form.amount} onChange={set('amount')} required />
          </div>
          <button className="btn" type="submit" disabled={saving}>{saving ? 'Creating…' : 'Create claim'}</button>
        </form>
      </div>
    </section>
  )
}
