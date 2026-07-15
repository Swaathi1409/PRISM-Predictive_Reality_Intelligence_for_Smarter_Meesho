/**
 * AgentCard.jsx — Single agent card with animated reveal.
 *
 * Displays one agent's verdict, message, score contribution, and data signals.
 * Framer Motion (MIT) handles the staggered entrance animation.
 */

import { motion } from 'framer-motion'
import { AGENT_CONFIG, VERDICT_CONFIG } from '../utils/constants'

export default function AgentCard({ agent, index }) {
  const agentConfig = AGENT_CONFIG[agent.agent_name] || {
    emoji: '🤖',
    color: 'from-gray-600 to-gray-400',
    accent: 'border-gray-500/40',
  }
  const verdictConfig = VERDICT_CONFIG[agent.verdict] || VERDICT_CONFIG.caution

  const scoreSign = agent.score_contribution > 0 ? '+' : ''
  const scoreColor =
    agent.score_contribution > 0 ? 'text-emerald-400' : agent.score_contribution < 0 ? 'text-red-400' : 'text-gray-400'

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay: index * 0.12, duration: 0.4, ease: 'easeOut' }}
      className={`min-w-0 rounded-xl border ${agentConfig.accent} bg-surface-card p-4 hover:bg-surface-elevated transition-colors`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${agentConfig.color} flex items-center justify-center text-xl shadow-lg`}>
            {agentConfig.emoji}
          </div>
          <div>
            <p className="font-display font-semibold text-white text-sm">{agent.agent_name}</p>
            <p className="text-xs text-gray-500">{agent.agent_role}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Score contribution */}
          {agent.agent_name !== 'Soch' && (
            <span className={`text-sm font-bold font-display ${scoreColor}`}>
              {scoreSign}{agent.score_contribution.toFixed(0)}
            </span>
          )}
          {/* Verdict badge */}
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${verdictConfig.bg} ${verdictConfig.color}`}>
            {verdictConfig.icon} {verdictConfig.label}
          </span>
        </div>
      </div>

      {/* Message */}
      <p className="text-sm text-gray-300 leading-relaxed">{agent.message}</p>

      {/* Data signals — shown for specialist agents only */}
      {agent.data && Object.keys(agent.data).length > 0 && agent.agent_name !== 'Soch' && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {Object.entries(agent.data)
            .filter(([k]) => k !== 'flags')
            .slice(0, 4)
            .map(([key, val]) => (
              <span
                key={key}
                className="text-xs px-2 py-0.5 rounded-md bg-surface-elevated border border-surface-border text-gray-400"
              >
                {key.replace(/_/g, ' ')}: <span className="text-gray-300">{String(val)}</span>
              </span>
            ))}
        </div>
      )}

      {/* Flags — if any */}
      {agent.data?.flags?.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {agent.data.flags.map((flag, i) => (
            <span key={i} className="text-xs px-2 py-0.5 rounded-md bg-red-500/10 border border-red-500/20 text-red-400">
              ⚠ {flag}
            </span>
          ))}
        </div>
      )}
    </motion.div>
  )
}
