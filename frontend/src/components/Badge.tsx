/** Pill badge. tone maps to a .b-<tone> class in index.css: "open", "high", "flagged"… */
export default function Badge({ tone, children }: { tone: string; children: React.ReactNode }) {
  return <span className={`badge b-${tone}`}>{children}</span>
}
