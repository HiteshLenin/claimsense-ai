import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import Badge from '../components/Badge'
import DecisionPanel from './DecisionPanel'

/** SDD screen: review workspace — claim facts, AI severity/priority,
 *  blended fraud risk with reasons, ML score, and the adjuster decision. */
export default function ReviewWorkspace() {
  const { claimId } = useParams<{ claimId: string }>()
  const [claim, setClaim] = useState<any>(null)
  const [analysis, setAnalysis] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  function refreshClaim() {
    if (!claimId) return
    api.getClaim(claimId).then(setClaim).catch((e) => setError(String(e)))
  }
  useEffect(() => { refreshClaim() }, [claimId])

  async function runAnalysis() {
    if (!claimId) return
    setLoading(true)
    setError('')
    try {
      setAnalysis(await api.startAnalysis(claimId))
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  const meterColor = !analysis ? '#ccc'
    : analysis.risk_band === 'high' ? 'var(--bad)'
    : analysis.risk_band === 'medium' ? 'var(--warn)' : 'var(--ok)'

  return (
    <section>
      <Link to="/" className="back-link">← Back to queue</Link>
      <h2 className="page-title">Review workspace</h2>
      {error && <p className="alert-error">{error}</p>}
      {!claim && !error && <p className="muted">Loading claim…</p>}
      {claim && (
        <div className="card">
          <h3>{claim.policy_number} <Badge tone={claim.status}>{claim.status.replace('_', ' ')}</Badge></h3>
          <div className="fact-grid">
            <div className="fact"><div className="k">Type</div><div className="v">{claim.loss_type}</div></div>
            <div className="fact"><div className="k">Amount</div><div className="v">${Number(claim.amount).toLocaleString()}</div></div>
            <div className="fact"><div className="k">Loss date</div><div className="v">{new Date(claim.loss_date).toLocaleDateString()}</div></div>
            <div className="fact"><div className="k">Version</div><div className="v">{claim.version}</div></div>
          </div>
          <p className="muted">{claim.description}</p>
        </div>
      )}
      <div className="card">
        <h3>AI analysis</h3>
        <button className="btn" onClick={runAnalysis} disabled={loading || !claim}>
          {loading ? 'Analyzing…' : analysis ? 'Re-run analysis' : 'Run analysis'}
        </button>
        {analysis && (
          <div style={{ marginTop: 16 }}>
            <p className="muted" style={{ marginTop: 0 }}>Model {analysis.model_version}</p>
            <div className="fact-grid">
              <div className="fact"><div className="k">Severity</div><div className="v"><Badge tone={analysis.severity}>{analysis.severity}</Badge></div></div>
              <div className="fact"><div className="k">Priority</div><div className="v"><Badge tone={analysis.priority}>{analysis.priority}</Badge></div></div>
              <div className="fact"><div className="k">Risk band</div><div className="v"><Badge tone={analysis.risk_band}>{analysis.risk_band}</Badge></div></div>
            </div>
            <div>
              <strong>Risk score {analysis.risk_score}</strong>
              <div className="meter"><div style={{ width: `${Math.round(analysis.risk_score * 100)}%`, background: meterColor }} /></div>
            </div>
            {analysis.risk_reasons.length > 0 ? (
              <ul>{analysis.risk_reasons.map((r: any) => <li key={r.code}>{r.label} (+{r.weight})</li>)}</ul>
            ) : (
              <p className="muted">No rule red flags fired.</p>
            )}
            {analysis.ml && (
              <p>
                <strong>ML fraud score:</strong> {analysis.ml.fraud_probability}{' '}
                {analysis.ml.flagged
                  ? <Badge tone="flagged">⚑ flagged for review</Badge>
                  : <Badge tone="clear">not flagged</Badge>}
              </p>
            )}
          </div>
        )}
      </div>
      {claim && <DecisionPanel claimId={claim.id} claimVersion={claim.version} onDecided={refreshClaim} />}
    </section>
  )
}
