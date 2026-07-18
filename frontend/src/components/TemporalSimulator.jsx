/**
 * TemporalSimulator.jsx — Displays three purchase timing strategy cards.
 *
 * Shows Buy Now / Wait for Sale / Split Purchase strategies with prices,
 * savings, and PRISM's recommended strategy highlighted.
 *
 * Library: framer-motion (MIT), lucide-react (ISC).
 */

import { motion } from 'framer-motion'
import { Clock, CheckCircle2 } from 'lucide-react'
import { STRATEGY_CONFIG } from '../utils/constants'

export default function TemporalSimulator({ strategies, selectedStrategy, onSelectStrategy }) {
  if (!strategies || strategies.length === 0) return null

  return (
    <section id="temporal-simulator-section" aria-label="Temporal Simulator — Purchase Timing Strategies">
      <div className="rounded-2xl border border-surface-border bg-surface-card p-5">
        {/* Header */}
        <div className="flex items-center gap-3 mb-5">
          <div className="w-8 h-8 rounded-lg bg-prism-500/20 border border-prism-500/30 flex items-center justify-center">
            <Clock className="w-4 h-4 text-prism-400" />
          </div>
          <div>
            <h2 className="font-display font-bold text-white text-lg">Temporal Simulator</h2>
            <p className="text-xs text-gray-500">When should you actually buy?</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {strategies.map((strategy, i) => {
            const cfg = STRATEGY_CONFIG[strategy.strategy_key] || { icon: '📦', color: 'from-gray-600 to-gray-500' }
            const isSelected = selectedStrategy?.strategy_key === strategy.strategy_key;
            
            // Button label logic
            let btnLabel = "I choose this";
            if (strategy.strategy_key === "buy_now") btnLabel = "Proceed with this";
            else if (strategy.strategy_key === "wait") btnLabel = "Set a reminder";
            else if (strategy.strategy_key === "split") btnLabel = "Split my payment";

            return (
              <motion.div
                key={strategy.strategy_key}
                onClick={() => onSelectStrategy && onSelectStrategy(strategy)}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1, duration: 0.4 }}
                id={`strategy-${strategy.strategy_key}`}
                className={`group relative flex flex-col rounded-xl border p-4 transition-all cursor-pointer
                  ${isSelected ? 'border-prism-400 bg-prism-500/20 shadow-prism ring-1 ring-prism-400' 
                    : strategy.recommended
                      ? 'border-prism-500/60 bg-prism-500/10 shadow-prism hover:border-prism-500/80'
                      : 'border-surface-border bg-surface-elevated hover:border-gray-500'
                  }`}
              >
                {/* Recommended badge */}
                {strategy.recommended && (
                  <div className="absolute -top-2.5 left-1/2 -translate-x-1/2">
                    <span className="flex items-center gap-1 text-xs font-semibold px-3 py-0.5 rounded-full bg-prism-600 text-white shadow-prism">
                      <CheckCircle2 className="w-3 h-3" />
                      PRISM Recommends
                    </span>
                  </div>
                )}

                {/* Icon + name */}
                <div className="flex items-center gap-2 mb-3 mt-1">
                  <span className={`text-2xl w-10 h-10 rounded-xl bg-gradient-to-br ${cfg.color} flex items-center justify-center`}>
                    {cfg.icon}
                  </span>
                  <span className="font-display font-semibold text-white text-sm leading-tight">{strategy.strategy_name}</span>
                </div>

                {/* Price */}
                <div className="mb-2">
                  <span className="font-display font-bold text-2xl text-white">
                    ₹{strategy.price.toLocaleString('en-IN')}
                  </span>
                  {strategy.savings_vs_now > 0 && (
                    <span className="ml-2 text-xs font-medium text-emerald-400">
                      Save ₹{strategy.savings_vs_now.toLocaleString('en-IN')}
                    </span>
                  )}
                </div>

                {/* Action date */}
                <p className="text-xs text-prism-300 mb-2 font-medium">{strategy.action_date}</p>

                {/* Note */}
                <p className="text-xs text-gray-400 leading-relaxed flex-grow">{strategy.note}</p>

                {/* Action button */}
                <button
                  className={`mt-4 w-full py-2 rounded-lg text-xs font-semibold transition-colors pointer-events-none ${
                    isSelected 
                      ? 'bg-prism-500 text-white'
                      : strategy.recommended
                        ? 'bg-prism-500/20 text-prism-300 group-hover:bg-prism-500 group-hover:text-white'
                        : 'bg-surface-border text-gray-300 group-hover:bg-gray-700 group-hover:text-white'
                  }`}
                >
                  {isSelected ? 'Selected' : btnLabel}
                </button>
              </motion.div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
