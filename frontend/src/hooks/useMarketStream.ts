import { useEffect, useLayoutEffect, useRef, useState } from 'react'

import { getApiBase, getWsUrl } from '../config'
import type { InsightPayload, OhlcvBar, WsInbound } from '../types'

export interface StreamHandlers {
  onBar: (bar: OhlcvBar) => void
  onInsight: (insight: InsightPayload) => void
}

function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null
}

function parseWsPayload(raw: unknown): WsInbound | null {
  if (!isRecord(raw) || typeof raw.type !== 'string') {
    return null
  }
  const t = raw.type
  if (t === 'pong') {
    return { type: 'pong' }
  }
  if (t === 'subscribed') {
    return { type: 'subscribed', channels: raw.channels }
  }
  if (t === 'unsubscribed') {
    return { type: 'unsubscribed' }
  }
  if (t === 'error') {
    return {
      type: 'error',
      code: typeof raw.code === 'string' ? raw.code : undefined,
      message: typeof raw.message === 'string' ? raw.message : undefined,
    }
  }
  if (t === 'bar' && isRecord(raw.data)) {
    return {
      type: 'bar',
      schema_version: String(raw.schema_version ?? ''),
      data: raw.data as unknown as OhlcvBar,
    }
  }
  if (t === 'insight' && isRecord(raw.data)) {
    return {
      type: 'insight',
      schema_version: String(raw.schema_version ?? ''),
      data: raw.data as unknown as InsightPayload,
    }
  }
  return null
}

export function useMarketStream(symbol: string, handlers: StreamHandlers) {
  const apiBase = getApiBase()
  const [connected, setConnected] = useState(false)
  const [streamError, setStreamError] = useState<string | null>(null)
  const handlersRef = useRef(handlers)
  useLayoutEffect(() => {
    handlersRef.current = handlers
  }, [handlers])

  useEffect(() => {
    let cancelled = false
    let ws: WebSocket | null = null
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null
    let attempt = 0

    const connect = () => {
      if (cancelled) {
        return
      }
      const url = getWsUrl(apiBase)
      ws?.close()
      ws = new WebSocket(url)

      ws.onopen = () => {
        if (cancelled) {
          return
        }
        setConnected(true)
        setStreamError(null)
        attempt = 0
        const sym = symbol.toUpperCase()
        ws?.send(
          JSON.stringify({
            type: 'subscribe',
            channels: [`market:${sym}:5m`, `insights:${sym}`],
          }),
        )
      }

      ws.onmessage = (ev) => {
        try {
          const parsed: unknown = JSON.parse(ev.data as string)
          const msg = parseWsPayload(parsed)
          if (!msg) {
            return
          }
          if (msg.type === 'bar') {
            handlersRef.current.onBar(msg.data)
          } else if (msg.type === 'insight') {
            handlersRef.current.onInsight(msg.data)
          } else if (msg.type === 'error') {
            setStreamError(msg.message ?? msg.code ?? 'stream error')
          }
        } catch {
          setStreamError('invalid WebSocket message')
        }
      }

      ws.onclose = () => {
        setConnected(false)
        if (!cancelled) {
          const delay = Math.min(30_000, 1000 * 2 ** attempt)
          attempt += 1
          reconnectTimer = setTimeout(connect, delay)
        }
      }

      ws.onerror = () => {
        ws?.close()
      }
    }

    connect()

    return () => {
      cancelled = true
      if (reconnectTimer !== null) {
        clearTimeout(reconnectTimer)
      }
      ws?.close()
      setConnected(false)
    }
  }, [symbol, apiBase])

  return { connected, streamError }
}
