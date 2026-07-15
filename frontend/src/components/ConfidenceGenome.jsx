/**
 * ConfidenceGenome.jsx — Animated confidence ring + labelled factor breakdown.
 *
 * Shows the total confidence score as an animated SVG ring with each
 * contributing factor listed with direction arrows and magnitude bars.
 *
 * Library: framer-motion (MIT) for ring animation, lucide-react (ISC) for icons.
 */

import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Dna } from 'lucide-react'
import { getConfidenceDisplay } from '../utils/constants'

const RING_RADIUS = 52
const RING_CIRCUMFERENCE = 2 * Math.PI * RING_RADIUS

export default function ConfidenceGenome({ confidence }) {
  if (!confidence) return null

  const { total_score, base_score, factors, interpretation } = confidence
  const display = getConfidenceDisplay(total_score)
  const dashOffset = RING_CIRCUMFERENCE * (1 - total_score / 100)

  return (
    <section id="confidence-genome-section" aria-label="Confidence Genome" className="h-full">
      <div className="rounded-2xl border border-surface-border bg-surface-card p-5 h-full flex flex-col">
        {/* Header */}
        <div className="flex items-center gap-3 mb-5">
          <div className="w-8 h-8 rounded-lg bg-prism-500/20 border border-prism-500/30 flex items-center justify-center">
            <Dna className="w-4 h-4 text-prism-400" />
          </div>
          <div>
            <h2 className="font-display font-bold text-white text-lg">Confidence Genome</h2>
            <p className="text-xs text-gray-500">Every factor that shaped this score</p>
          </div>
        </div>

        <div className="flex flex-col gap-6 items-center flex-1">
          {/* Animated SVG ring */}
          <div className="flex-shrink-0 flex flex-col items-center gap-2">
            <div className="relative">
              <svg width="140" height="140" viewBox="0 0 140 140" aria-label={`Confidence score: ${total_score}%`}>
                {/* Background ring */}
                <circle cx="70" cy="70" r={RING_RADIUS} fill="none" stroke="#2d2050" strokeWidth="12" />
                {/* Animated score ring */}
                <motion.circle
                  cx="70" cy="70" r={RING_RADIUS}
                  fill="none"
                  stroke={display.ring}
                  strokeWidth="12"
                  strokeLinecap="round"
                  strokeDasharray={RING_CIRCUMFERENCE}
                  initial={{ strokeDashoffset: RING_CIRCUMFERENCE }}
                  animate={{ strokeDashoffset: dashOffset }}
                  transition={{ duration: 1.4, ease: 'easeOut', delay: 0.2 }}
                  style={{ transform: 'rotate(-90deg)', transformOrigin: '70px 70px' }}
                />
                {/* Score text */}
                <text x="70" y="64" textAnchor="middle" fill="white" fontSize="28" fontWeight="800" fontFamily="Outfit, sans-serif">
                  {total_score.toFixed(0)}
                </text>
                <text x="70" y="80" textAnchor="middle" fill={display.ring} fontSize="10" fontWeight="600" fontFamily="Inter, sans-serif">
                  {display.label}
                </text>
              </svg>
            </div>
            <p className="text-xs text-gray-500 text-center max-w-[140px]">Base: {base_score}</p>
          </div>

          {/* Factor list */}
          <div className="flex-1 space-y-3 w-full min-w-0 max-w-full flex flex-col justify-center">
            <p className="text-sm text-gray-400 italic mb-4 text-center break-words">"{interpretation}"</p>
            <div className="space-y-2 w-full max-w-[300px] mx-auto">
              {factors.map((factor, i) => (
                <FactorRow key={i} factor={factor} index={i} maxContribution={Math.abs(factors[0]?.contribution || 1)} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

function FactorRow({ factor, index, maxContribution }) {
  const isPositive = factor.direction === 'up'
  const barWidth = Math.min(100, (Math.abs(factor.contribution) / maxContribution) * 100)

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.3 + index * 0.06, duration: 0.3 }}
      className="flex items-center gap-2"
    >
      {/* Direction icon */}
      {isPositive
        ? <TrendingUp className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
        : <TrendingDown className="w-3.5 h-3.5 text-red-400 flex-shrink-0" />
      }

      {/* Factor label */}
      <span className="text-xs text-gray-400 w-24 sm:w-36 flex-shrink-0 truncate" title={factor.factor_label}>{factor.factor_label}</span>

      {/* Bar */}
      <div className="flex-1 h-1.5 rounded-full bg-surface-elevated overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${barWidth}%` }}
          transition={{ delay: 0.4 + index * 0.06, duration: 0.6, ease: 'easeOut' }}
          className={`h-full rounded-full ${isPositive ? 'bg-emerald-500' : 'bg-red-500'}`}
        />
      </div>

      {/* Contribution value */}
      <span className={`text-xs font-medium w-8 text-right ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
        {isPositive ? '+' : ''}{factor.contribution.toFixed(1)}
      </span>
    </motion.div>
  )
}
