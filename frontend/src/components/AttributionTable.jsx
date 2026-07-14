/**
 * AttributionTable.jsx — Open source library attribution table.
 *
 * Required by submission: every library used is listed with name,
 * license, version, and why it was chosen.
 */

import { motion } from 'framer-motion'

const ATTRIBUTIONS = [
  { name: 'FastAPI', license: 'MIT', side: 'Backend', reason: 'Native async, auto OpenAPI docs at /docs' },
  { name: 'Anthropic SDK', license: 'Anthropic Terms', side: 'Backend', reason: 'Claude LLM calls for Soch and EmotionalLayer' },
  { name: 'LangChain', license: 'MIT', side: 'Backend', reason: 'Agent orchestration interface and prompt chaining' },
  { name: 'SQLAlchemy', license: 'MIT', side: 'Backend', reason: 'Database-agnostic ORM (SQLite dev / PostgreSQL prod)' },
  { name: 'Alembic', license: 'MIT', side: 'Backend', reason: 'Versioned schema migrations for reproducible DB setup' },
  { name: 'Pydantic v2', license: 'MIT', side: 'Backend', reason: 'Strict type validation at API boundary, powers OpenAPI docs' },
  { name: 'Redis-py', license: 'BSD', side: 'Backend', reason: 'Result caching to avoid redundant LLM calls during demo' },
  { name: 'Uvicorn', license: 'BSD', side: 'Backend', reason: 'ASGI server for FastAPI' },
  { name: 'python-dotenv', license: 'BSD', side: 'Backend', reason: 'Load .env for local dev' },
  { name: 'React 18', license: 'MIT', side: 'Frontend', reason: 'Component-based UI, concurrent rendering' },
  { name: 'Vite', license: 'MIT', side: 'Frontend', reason: 'Sub-second HMR and tree-shaken production builds' },
  { name: 'Tailwind CSS', license: 'MIT', side: 'Frontend', reason: 'Utility classes co-located with components' },
  { name: 'Framer Motion', license: 'MIT', side: 'Frontend', reason: 'Staggered agent reveal, confidence ring animation' },
  { name: 'TanStack React Query', license: 'MIT', side: 'Frontend', reason: 'Loading/error/success states for API calls' },
  { name: 'Axios', license: 'MIT', side: 'Frontend', reason: 'HTTP client with interceptors and timeout' },
  { name: 'Lucide React', license: 'ISC', side: 'Frontend', reason: 'Consistent icon set throughout UI' },
  { name: 'React Router v6', license: 'MIT', side: 'Frontend', reason: 'Client-side routing (Home / Demo / About)' },
  { name: 'Docker', license: 'Apache 2.0', side: 'Infra', reason: 'Reproducible builds across all judge machines' },
  { name: 'Nginx', license: 'BSD-2', side: 'Infra', reason: 'Reverse proxy, static file serving, CORS elimination' },
]

const SIDE_COLORS = {
  Backend: 'bg-blue-500/15 text-blue-300 border-blue-500/30',
  Frontend: 'bg-prism-500/15 text-prism-300 border-prism-500/30',
  Infra: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
}

export default function AttributionTable() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="overflow-x-auto rounded-2xl border border-surface-border"
    >
      <table className="w-full text-sm" aria-label="Open source library attributions">
        <thead>
          <tr className="border-b border-surface-border bg-surface-elevated">
            <th className="text-left px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Library</th>
            <th className="text-left px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">License</th>
            <th className="text-left px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Layer</th>
            <th className="text-left px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Why Chosen</th>
          </tr>
        </thead>
        <tbody>
          {ATTRIBUTIONS.map((row, i) => (
            <tr key={i} className="border-b border-surface-border/50 hover:bg-surface-elevated/50 transition-colors">
              <td className="px-4 py-3 font-medium text-white">{row.name}</td>
              <td className="px-4 py-3 text-gray-400 font-mono text-xs">{row.license}</td>
              <td className="px-4 py-3">
                <span className={`text-xs px-2 py-0.5 rounded-full border ${SIDE_COLORS[row.side]}`}>
                  {row.side}
                </span>
              </td>
              <td className="px-4 py-3 text-gray-400 text-xs">{row.reason}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </motion.div>
  )
}
