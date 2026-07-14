/**
 * LifeEventResult.jsx — Shows detected event and phased purchase timeline.
 *
 * Displays the life event label, emotion level, and the purchase phases
 * as a vertical timeline with priority badges.
 *
 * Library: framer-motion (MIT), lucide-react (ISC).
 */

import { motion } from 'framer-motion'
import { Calendar, Clock, Tag } from 'lucide-react'
import { PRIORITY_CONFIG } from '../utils/constants'

export default function LifeEventResult({ detectedEvent, eventKey, purchaseTimeline, familySignificance }) {
  if (!purchaseTimeline || purchaseTimeline.length === 0) return null

  return (
    <section id="life-event-section" aria-label="Life Event and Purchase Timeline">
      <div className="rounded-2xl border border-surface-border bg-surface-card p-5">
        {/* Header */}
        <div className="flex items-center gap-3 mb-5">
          <div className="w-8 h-8 rounded-lg bg-prism-500/20 border border-prism-500/30 flex items-center justify-center">
            <Calendar className="w-4 h-4 text-prism-400" />
          </div>
          <div>
            <h2 className="font-display font-bold text-white text-lg">Purchase Timeline</h2>
            <p className="text-xs text-gray-500">
              {detectedEvent} · {familySignificance?.replace('_', ' ')} significance
            </p>
          </div>
        </div>

        {/* Timeline */}
        <div className="relative">
          {/* Vertical line */}
          <div className="absolute left-4 top-2 bottom-2 w-0.5 bg-surface-elevated" />

          <div className="space-y-4">
            {purchaseTimeline.map((phase, i) => {
              const priorityCfg = PRIORITY_CONFIG[phase.priority] || PRIORITY_CONFIG.nice_to_have
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -15 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1, duration: 0.4 }}
                  className="flex gap-4 pl-10 relative"
                >
                  {/* Timeline dot */}
                  <div className={`absolute left-2.5 top-1 w-3 h-3 rounded-full border-2 border-prism-500 bg-surface-DEFAULT ring-2 ring-surface-DEFAULT z-10`} />

                  {/* Phase card */}
                  <div className="flex-1 rounded-xl border border-surface-border bg-surface-elevated p-3">
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <h3 className="text-sm font-semibold text-white">{phase.phase_name}</h3>
                      <span className={`text-xs px-2 py-0.5 rounded-full border flex-shrink-0 ${priorityCfg.color}`}>
                        {priorityCfg.label}
                      </span>
                    </div>

                    <div className="flex items-center gap-1 mb-2">
                      <Clock className="w-3 h-3 text-gray-600" />
                      <span className="text-xs text-gray-500">
                        {phase.days_from_now === 0 ? 'Immediately' : `In ${phase.days_from_now} days`}
                      </span>
                    </div>

                    {/* Categories */}
                    <div className="flex flex-wrap gap-1 mb-2">
                      {phase.categories?.map((cat) => (
                        <span key={cat} className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-md bg-surface-DEFAULT border border-surface-border text-gray-400">
                          <Tag className="w-2.5 h-2.5" />
                          {cat.replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>

                    <p className="text-xs text-gray-400 leading-relaxed">{phase.note}</p>
                  </div>
                </motion.div>
              )
            })}
          </div>
        </div>
      </div>
    </section>
  )
}
