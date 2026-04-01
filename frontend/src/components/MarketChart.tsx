import { useMemo } from 'react'
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { OhlcvBar } from '../types'

type Row = {
  x: string
  close: number
  volume: number
  high: number
  low: number
  time_close: string
}

function barsToRows(bars: OhlcvBar[]): Row[] {
  const sorted = [...bars].sort((a, b) => a.time_open.localeCompare(b.time_open))
  return sorted.map((b) => ({
    x: new Date(b.time_close).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }),
    close: b.close,
    volume: b.volume,
    high: b.high,
    low: b.low,
    time_close: b.time_close,
  }))
}

export function MarketChart({ bars, symbol }: { bars: OhlcvBar[]; symbol: string }) {
  const data = useMemo(() => barsToRows(bars), [bars])

  if (data.length === 0) {
    return (
      <div className="chart-empty">
        <p>
          No bars yet for {symbol}. Start the backend with mock market data, or wait for the next 5m
          bar.
        </p>
      </div>
    )
  }

  return (
    <div className="chart-wrap">
      <ResponsiveContainer width="100%" height={380}>
        <ComposedChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="x" tick={{ fill: 'var(--text)', fontSize: 11 }} minTickGap={24} />
          <YAxis
            yAxisId="price"
            domain={['auto', 'auto']}
            tick={{ fill: 'var(--text)', fontSize: 11 }}
            width={56}
          />
          <YAxis
            yAxisId="vol"
            orientation="right"
            tick={{ fill: 'var(--text)', fontSize: 11 }}
            width={48}
          />
          <Tooltip
            contentStyle={{
              background: 'var(--bg)',
              border: '1px solid var(--border)',
              borderRadius: 8,
            }}
            formatter={(value, name) => {
              const v = typeof value === 'number' ? value : Number(value)
              if (name === 'volume') {
                return [v.toLocaleString(), 'Volume']
              }
              return [v.toFixed(2), 'Close']
            }}
            labelFormatter={(_, payload) => {
              const row = payload?.[0]?.payload as Row | undefined
              return row ? `${row.time_close}` : ''
            }}
          />
          <Legend />
          <Bar
            yAxisId="vol"
            dataKey="volume"
            name="Volume"
            fill="var(--accent)"
            fillOpacity={0.25}
            radius={[2, 2, 0, 0]}
          />
          <Line
            yAxisId="price"
            type="monotone"
            dataKey="close"
            name="Close"
            stroke="var(--accent)"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
