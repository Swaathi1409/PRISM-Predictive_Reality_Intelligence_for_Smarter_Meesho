/**
 * SessionHistory.jsx — Last 5 queries as clickable chips for quick re-run.
 *
 * Reads from localStorage via useSessionHistory hook.
 * Each chip shows the first 40 chars of the query and can be clicked to re-fill the form.
 */

import { motion } from 'framer-motion'
import { History, X } from 'lucide-react'

export default function SessionHistory({ history, onSelect, onClear }) {
  if (!history || history.length === 0) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-2xl mx-auto mt-4"
      id="session-history-section"
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5">
          <History className="w-3.5 h-3.5 text-gray-600" />
          <span className="text-xs text-gray-600">Recent queries</span>
        </div>
        <button
          onClick={onClear}
          className="text-xs text-gray-700 hover:text-gray-500 transition-colors flex items-center gap-1"
        >
          <X className="w-3 h-3" /> Clear
        </button>
      </div>
      <div className="flex flex-wrap gap-2">
        {history.map((item, i) => (
          <button
            key={i}
            onClick={() => onSelect(item)}
            className="text-xs px-3 py-1.5 rounded-full border border-surface-border text-gray-500
              hover:border-prism-500/50 hover:text-prism-300 hover:bg-prism-500/5 transition-all max-w-[240px] truncate"
            title={item.user_input}
          >
            {item.user_input.slice(0, 45)}{item.user_input.length > 45 ? '…' : ''}
          </button>
        ))}
      </div>
    </motion.div>
  )
}
