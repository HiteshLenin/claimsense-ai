/** One place for all backend calls. Pages import from here,
 *  so if an endpoint changes you edit one file, not five. */
const BASE = '/api'

async function req(path: string, opts: RequestInit = {}) {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  })
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`)
  return res.json()
}

export const api = {
  listClaims: () => req('/claims'),
  getClaim: (claimId: string) => req(`/claims/${claimId}`),
  createClaim: (payload: object) =>
    req('/claims', { method: 'POST', body: JSON.stringify(payload) }),
  uploadDocument: (claimId: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return fetch(`${BASE}/claims/${claimId}/documents`, { method: 'POST', body: form }).then((r) => r.json())
  },
  startAnalysis: (claimId: string) => req(`/claims/${claimId}/analyses`, { method: 'POST' }),
  getAnalysis: (analysisId: string) => req(`/analyses/${analysisId}`),
  recordDecision: (claimId: string, payload: object) =>
    req(`/claims/${claimId}/decisions`, { method: 'POST', body: JSON.stringify(payload) }),
}
