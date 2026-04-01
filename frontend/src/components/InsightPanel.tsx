import type { InsightPayload } from '../types'

function biasClass(bias: string): string {
  if (bias === 'bullish') {
    return 'bias bullish'
  }
  if (bias === 'bearish') {
    return 'bias bearish'
  }
  return 'bias neutral'
}

export function InsightPanel({ insight }: { insight: InsightPayload | null }) {
  if (!insight) {
    return (
      <section className="panel insight-panel" aria-label="Insight">
        <h2>Insight</h2>
        <p className="muted">
          Subscribe to the WebSocket or request an insight to see narrative and structure.
        </p>
      </section>
    )
  }

  const { structured, narrative, disclaimer } = insight

  return (
    <section className="panel insight-panel" aria-label="Insight">
      <h2>Insight</h2>
      <p className="insight-meta">
        <span className={biasClass(structured.bias)}>{structured.bias}</span>
        <span className="muted">{new Date(insight.generated_at).toLocaleString()}</span>
      </p>
      <p className="insight-summary">{narrative.summary}</p>
      {structured.key_levels.length > 0 ? (
        <div className="levels">
          <h3>Key levels</h3>
          <ul>
            {structured.key_levels.map((lv) => (
              <li key={`${lv.price}-${lv.role}`}>
                <strong>{lv.price.toFixed(2)}</strong> — {lv.role}
                {lv.priority !== undefined ? ` (p${lv.priority})` : ''}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {structured.risk_notes.length > 0 ? (
        <div className="risk">
          <h3>Risk notes</h3>
          <ul>
            {structured.risk_notes.map((n) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {disclaimer ? <p className="disclaimer">{disclaimer}</p> : null}
    </section>
  )
}
