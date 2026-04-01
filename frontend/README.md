# QuantEdge AI — Frontend

React 19 + TypeScript (strict) + Vite.

## Setup

```bash
cd frontend
npm install
```

## Commands

| Task             | Command                |
| ---------------- | ---------------------- |
| Dev server       | `npm run dev`          |
| Production build | `npm run build`        |
| ESLint           | `npm run lint`         |
| Prettier (write) | `npm run format`       |
| Prettier (check) | `npm run format:check` |

Default dev URL: `http://localhost:5173`. Leave `VITE_API_BASE_URL` unset (or empty) to use the Vite proxy to the backend on port 8000 (`/v1`, `/docs`, `/metrics`, etc.). Set `VITE_API_BASE_URL` explicitly if the UI should call the API on another origin (e.g. Docker Compose with the nginx gateway on port 8080).
