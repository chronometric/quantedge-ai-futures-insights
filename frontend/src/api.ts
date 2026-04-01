import { apiKeyHeaders, getApiBase } from './config'
import type { InsightPayload, OhlcvBar } from './types'

async function parseJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export async function fetchSymbols(): Promise<string[]> {
  const base = getApiBase()
  const res = await fetch(`${base}/v1/symbols`)
  const data = await parseJson<{ symbols: string[] }>(res)
  return data.symbols
}

export async function fetchBars(symbol: string, limit = 300): Promise<OhlcvBar[]> {
  const base = getApiBase()
  const q = new URLSearchParams({ interval: '5m', limit: String(limit) })
  const res = await fetch(`${base}/v1/market/${encodeURIComponent(symbol)}/bars?${q}`)
  const data = await parseJson<{ bars: OhlcvBar[] }>(res)
  return data.bars
}

export async function fetchHealth(): Promise<{ status: string; version: string }> {
  const base = getApiBase()
  const res = await fetch(`${base}/v1/health`)
  return parseJson(res)
}

export async function requestInsight(symbol: string): Promise<InsightPayload> {
  const base = getApiBase()
  const res = await fetch(`${base}/v1/insights`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...apiKeyHeaders() },
    body: JSON.stringify({
      symbol,
      interval: '5m',
      include_narrative: true,
      lookback: 120,
    }),
  })
  return parseJson(res)
}

export function mergeBarSeries(prev: OhlcvBar[], incoming: OhlcvBar): OhlcvBar[] {
  const t = incoming.time_close
  const idx = prev.findIndex((b) => b.time_close === t)
  if (idx >= 0) {
    const next = [...prev]
    next[idx] = incoming
    return next
  }
  return [...prev, incoming].slice(-500)
}
