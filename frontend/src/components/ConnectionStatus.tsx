export function ConnectionStatus({
  apiOk,
  wsConnected,
  streamError,
}: {
  apiOk: boolean | null
  wsConnected: boolean
  streamError: string | null
}) {
  return (
    <div className="status-row" role="status">
      <span className={`pill ${apiOk ? 'ok' : apiOk === false ? 'bad' : ''}`}>
        API {apiOk === null ? '…' : apiOk ? 'live' : 'down'}
      </span>
      <span className={`pill ${wsConnected ? 'ok' : 'bad'}`}>
        Stream {wsConnected ? 'connected' : 'reconnecting…'}
      </span>
      {streamError ? <span className="pill bad">{streamError}</span> : null}
    </div>
  )
}
