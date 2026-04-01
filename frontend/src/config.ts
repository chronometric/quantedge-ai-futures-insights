/** API origin without trailing slash, or empty string for same-origin (Vite dev proxy). */
export function getApiBase(): string {
  const v = import.meta.env.VITE_API_BASE_URL
  if (v !== undefined && v !== '') {
    return v.replace(/\/$/, '')
  }
  return ''
}

/** WebSocket URL for the streaming endpoint. */
export function getWsUrl(apiBase: string): string {
  if (apiBase) {
    return `${apiBase.replace(/^http/, 'ws')}/v1/ws`
  }
  const { protocol, host } = window.location
  const wsProto = protocol === 'https:' ? 'wss:' : 'ws:'
  return `${wsProto}//${host}/v1/ws`
}
