/** SDD screen: policy admin — policy versions + ingestion status. */
export default function PolicyAdmin() {
  return (
    <section>
      <h2 className="page-title">Policy admin</h2>
      <p className="page-sub">Policy packs and their AI-ready chunks.</p>
      <div className="card">
        <p className="muted" style={{ margin: 0 }}>
          Nothing ingested yet. Policy document upload and versioning arrive with the RAG phase —
          this is where each policy version and its indexed chunks will be listed.
        </p>
      </div>
    </section>
  )
}
