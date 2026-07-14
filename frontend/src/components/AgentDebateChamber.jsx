/**
 * AgentDebateChamber.jsx — Container for all four agent debate cards.
 *
 * Renders all 4 agents (Kismat, Paisa, Samay, Soch) with section header
 * and animated stagger through AgentCard children.
 */

import { motion } from 'framer-motion'
import { Brain } from 'lucide-react'
import AgentCard from './AgentCard'

export default function AgentDebateChamber({ agents }) {
  if (!agents || agents.length === 0) return null

  return (
    <section id="agent-debate-section" aria-label="Agent Debate Chamber">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4 }}
      >
        {/* Section header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 rounded-lg bg-prism-500/20 border border-prism-500/30 flex items-center justify-center">
            <Brain className="w-4 h-4 text-prism-400" />
          </div>
          <div>
            <h2 className="font-display font-bold text-white text-lg">Agent Debate Chamber</h2>
            <p className="text-xs text-gray-500">4 specialist AI agents evaluated this product for your context</p>
          </div>
        </div>

        {/* Agent cards — staggered via individual card delays */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {agents.map((agent, i) => (
            <AgentCard key={agent.agent_name} agent={agent} index={i} />
          ))}
        </div>
      </motion.div>
    </section>
  )
}
