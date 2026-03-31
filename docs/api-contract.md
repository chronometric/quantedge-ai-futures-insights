# QuantEdge AI — API Contract Draft (V1)

Base URL placeholder: `https://api.example.com` / `http://localhost:8000` (dev).

All timestamps are **RFC 3339** strings in UTC unless noted. API version prefix: `/v1`.

## REST

### Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/health` | Liveness: process up. |
| `GET` | `/v1/health/ready` | Readiness: DB, Redis, optional vector store reachable. |

**Response `200` example:**

```json
{
  "status": "ok",
  "version": "0.1.0",
  "environment": "dev"
}
```

### Market history

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/symbols` | List tradable symbols for V1. |
| `GET` | `/v1/market/{symbol}/bars` | OHLCV bars for charting. |

**Query parameters (`/bars`):**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `interval` | string | yes | e.g. `5m` |
| `start` | datetime | no | Inclusive start (UTC) |
| `end` | datetime | no | Exclusive or inclusive end (document per implementation) |
| `limit` | integer | no | Max bars (default cap e.g. 500) |

**Response:** JSON array of objects validating `contracts/ohlcv-bar.schema.json` (or wrapped in `{ "bars": [...] }`).

### Insights (on-demand)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/insights` | Generate insight for a symbol from latest snapshot + RAG + LLM. |

**Request body:**

```json
{
  "symbol": "ES",
  "interval": "5m",
  "include_narrative": true
}
```

**Response:** Object validating `contracts/insight-payload.schema.json`.

**Errors:** `400` validation; `429` rate limit; `503` LLM or upstream unavailable.

## WebSocket

### Connection

- **URL:** `GET /v1/ws` (or `/v1/stream`) — exact path TBD; upgrade to WebSocket.
- **Subprotocol / auth:** Bearer token in query `?token=` or first message handshake (TBD).

### Client → server messages (draft)

| Type | Payload | Description |
|------|---------|-------------|
| `subscribe` | `{ "type": "subscribe", "channels": ["market:ES:5m", "insights:ES"] }` | Subscribe to symbol channels. |
| `unsubscribe` | `{ "type": "unsubscribe", "channels": [...] }` | Stop receiving channels. |
| `ping` | `{ "type": "ping" }` | Keep-alive; server responds `pong`. |

### Server → client messages (draft)

| Type | Payload | Description |
|------|---------|-------------|
| `bar` | `{ "type": "bar", "data": <OhlcvBar> }` | New or updated 5m bar. |
| `insight` | `{ "type": "insight", "data": <InsightPayload> }` | New AI insight for subscribed symbol. |
| `error` | `{ "type": "error", "code": "...", "message": "..." }` | Recoverable or fatal error notice. |
| `pong` | `{ "type": "pong" }` | Response to `ping`. |

Envelope convention:

```json
{
  "type": "bar",
  "schema_version": "1.0.0",
  "data": { }
}
```

## OpenAPI

Machine-readable draft: [`openapi/openapi.yaml`](../openapi/openapi.yaml).

## Versioning

- **URL path:** `/v1/...` for breaking changes reserve `/v2/`.
- **Payloads:** `schema_version` inside contracts (see JSON Schemas) for backward-compatible field additions.
