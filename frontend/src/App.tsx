import { useCallback, useEffect, useState } from 'react'

import './App.css'
import { fetchBars, fetchHealth, fetchSymbols, mergeBarSeries, requestInsight } from './api'
import { ConnectionStatus } from './components/ConnectionStatus'
import { InsightPanel } from './components/InsightPanel'
import { MarketChart } from './components/MarketChart'
import { useMarketStream } from './hooks/useMarketStream'
import type { InsightPayload, OhlcvBar } from './types'

export default function App() {
  const [symbols, setSymbols] = useState<string[]>([])
  const [symbol, setSymbol] = useState('ES')
  const [bars, setBars] = useState<OhlcvBar[]>([])
  const [insight, setInsight] = useState<InsightPayload | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [insightsLoading, setInsightsLoading] = useState(false)
  const [apiOk, setApiOk] = useState<boolean | null>(null)

  const onBar = useCallback((bar: OhlcvBar) => {
    setBars((prev) => {
      if (bar.symbol.toUpperCase() !== symbol.toUpperCase()) {
        return prev
      }
      return mergeBarSeries(prev, bar)
    })
  }, [symbol])
  const onInsight = useCallback((ins: InsightPayload) => {
    if (ins.symbol.toUpperCase() !== symbol.toUpperCase()) {
      return
    }
    setInsight(ins)
  }, [symbol])
  const { connected, streamError } = useMarketStream(symbol, { onBar, onInsight })

  useEffect(() => {
    fetchSymbols()
      .then((s) => {
        setSymbols(s)
        setSymbol((cur) => (s.includes(cur) ? cur : (s[0] ?? cur)))
      })
      .catch((e: unknown) => {
        setLoadError(String(e))
      })
  }, [])

  useEffect(() => {
    let cancelled = false
    fetchHealth()
      .then(() => {
        if (!cancelled) {
          setApiOk(true)
        }
      })
      .catch(() => {
        if (!cancelled) {
          setApiOk(false)
        }
      })
    const interval = setInterval(() => {
      fetchHealth()
        .then(() => {
          setApiOk(true)
        })
        .catch(() => {
          setApiOk(false)
        })
    }, 30_000)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    setLoadError(null)
    fetchBars(symbol)
      .then((b) => {
        if (!cancelled) {
          setBars([...b].sort((a, x) => a.time_open.localeCompare(x.time_open)))
        }
      })
      .catch((e: unknown) => {
        if (!cancelled) {
          setLoadError(String(e))
        }
      })
    return () => {
      cancelled = true
    }
  }, [symbol])

  async function handleInsightRequest() {
    setInsightsLoading(true)
    setLoadError(null)
    try {
      const ins = await requestInsight(symbol)
      setInsight(ins)
    } catch (e: unknown) {
      setLoadError(String(e))
    } finally {
      setInsightsLoading(false)
    }
  }

  return (
    <main className="app">
      <header className="app-header">
        <h1>QuantEdge AI</h1>
        <p className="tagline">Real-Time Futures Insights Engine</p>
        <ConnectionStatus apiOk={apiOk} wsConnected={connected} streamError={streamError} />
      </header>

      <section className="toolbar" aria-label="Controls">
        <label className="field">
          <span>Symbol</span>
          <select
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            aria-label="Trading symbol"
          >
            {(symbols.length ? symbols : [symbol]).map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <button type="button" onClick={handleInsightRequest} disabled={insightsLoading}>
          {insightsLoading ? 'Generating…' : 'Generate insight'}
        </button>
      </section>

      {loadError ? (
        <div className="banner error" role="alert">
          {loadError}
        </div>
      ) : null}

      <section className="grid" aria-label="Dashboard">
        <div className="panel chart-panel">
          <h2>5m chart — close & volume</h2>
          <MarketChart bars={bars} symbol={symbol} />
        </div>
        <InsightPanel insight={insight} />
      </section>
    </main>
  )
}
