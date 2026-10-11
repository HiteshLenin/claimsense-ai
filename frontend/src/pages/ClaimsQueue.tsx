import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import Badge from '../components/Badge'

/** SDD screen: claims queue — claim number, status, severity, priority, risk, age. */
export default function ClaimsQueue() {
  const [claims, setClaims] = useState<any[]>([])
  useEffect(() => { api.listClaims().then(setClaims).catch(console.error) }, [])
  return (
    <section>
      <h2 className="page-title">Claims queue</h2>
      <p className="page-sub">{claims.length} claim{claims.length === 1 ? '' : 's'} · click Review to run the AI analysis</p>
      {claims.length === 0 ? (
        <div className="card"><p className="muted">No claims yet. Create one from “New claim”.</p></div>
      ) : (
        <table className="table">
          <thead>
            <tr><th>Policy</th><th>Type</th><th>Amount</th><th>Status</th><th></th></tr>
          </thead>
          <tbody>
            {claims.map((c) => (
              <tr key={c.id}>
                <td><strong>{c.policy_number}</strong></td>
                <td className="muted">{c.loss_type}</td>
                <td>${Number(c.amount).toLocaleString()}</td>
                <td><Badge tone={c.status}>{c.status.replace('_', ' ')}</Badge></td>
                <td><Link to={`/claims/${c.id}/review`}>Review →</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
