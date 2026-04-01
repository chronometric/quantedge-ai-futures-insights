export interface OhlcvBar {
  schema_version: string
  symbol: string
  interval: string
  time_open: string
  time_close: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  source?: string
}

export interface InsightPayload {
  schema_version: string
  insight_id: string
  symbol: string
  interval?: string
  generated_at: string
  structured: {
    bias: string
    key_levels: Array<{ price: number; role: string; priority?: number }>
    scenarios: Array<{ name: string; condition: string; implication?: string }>
    risk_notes: string[]
  }
  narrative: { summary: string }
  disclaimer?: string
  retrieval?: { chunk_ids: string[]; kb_version: string }
}

export type WsInbound =
  | { type: 'bar'; schema_version?: string; data: OhlcvBar }
  | { type: 'insight'; schema_version?: string; data: InsightPayload }
  | { type: 'pong' }
  | { type: 'subscribed'; channels?: unknown }
  | { type: 'unsubscribed' }
  | { type: 'error'; code?: string; message?: string }
