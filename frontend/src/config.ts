/** API origin without trailing slash, or empty string for same-origin (Vite dev proxy). */
export function getApiBase(): string {
  const v = import.meta.env.VITE_API_BASE_URL
  if (v !== undefined && v !== '') {
    return v.replace(/\/$/, '')
  }
  return ''
}

/** Optional shared secret when the API enforces ``API_KEY`` (demo only; prefer gateway auth in prod). */
export function getApiKey(): string | undefined {
  const v = import.meta.env.VITE_API_KEY
  if (v !== undefined && v !== '') {
    return v
  }
  return undefined
}

/** Headers for authenticated REST calls (e.g. POST /v1/insights). */
export function apiKeyHeaders(): Record<string, string> {
  const k = getApiKey()
  return k ? { 'X-API-Key': k } : {}
}

/** WebSocket URL for the streaming endpoint (adds ``?token=`` when ``VITE_API_KEY`` is set). */
export function getWsUrl(apiBase: string): string {
  let url: string
  if (apiBase) {
    url = `${apiBase.replace(/^http/, 'ws')}/v1/ws`
  } else {
    const { protocol, host } = window.location
    const wsProto = protocol === 'https:' ? 'wss:' : 'ws:'
    url = `${wsProto}//${host}/v1/ws`
  }
  const k = getApiKey()
  if (k) {
    const sep = url.includes('?') ? '&' : '?'
    url = `${url}${sep}token=${encodeURIComponent(k)}`
  }
  return url
}
