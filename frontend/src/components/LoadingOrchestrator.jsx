/**
 * LoadingOrchestrator.jsx — Sequential agent thinking display during analysis.
 *
 * Shows animated steps while the backend is processing, so users understand
 * what PRISM is doing rather than seeing a blank spinner.
 *
 * Library: framer-motion (MIT).
 */

import { motion, AnimatePresence } from 'framer-motion'
import { useEffect, useState } from 'react'

const STEPS = [
  { icon: '🔍', label: 'Reading your life context...', duration: 2500 },
  { icon: '🗺', label: 'Detecting location and institution...', duration: 2000 },
  { icon: '❤️', label: 'Understanding the emotion of this moment...', duration: 2500 },
  { icon: '🛍', label: 'Matching relevant products...', duration: 2000 },
  { icon: '🛡', label: 'Kismat checking seller trust...', duration: 2000 },
  { icon: '💰', label: 'Paisa evaluating budget fit...', duration: 2000 },
  { icon: '⏱', label: 'Samay checking delivery windows...', duration: 2000 },
  { icon: '🧠', label: 'Soch deliberating the final verdict...', duration: 3000 },
  { icon: '📊', label: 'Building your Confidence Genome...', duration: 2000 },
]

export default function LoadingOrchestrator() {
  const [currentStep, setCurrentStep] = useState(0)
  const [completedSteps, setCompletedSteps] = useState([])

  useEffect(() => {
    let accumulated = 0
    const timers = STEPS.map((step, i) => {
      const timer = setTimeout(() => {
        setCurrentStep(i)
        if (i > 0) {
          setCompletedSteps((prev) => [...prev, i - 1])
        }
      }, accumulated)
      accumulated += step.duration
      return timer
    })

    return () => timers.forEach(clearTimeout)
  }, [])

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] py-12">
      {/* Pulsing PRISM logo */}
      <motion.div
        animate={{ scale: [1, 1.08, 1], opacity: [0.7, 1, 0.7] }}
        transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
        className="w-20 h-20 rounded-2xl bg-prism-gradient flex items-center justify-center mb-8 shadow-prism-lg"
        aria-label="PRISM is analysing"
      >
        <span className="text-3xl">✦</span>
      </motion.div>

      <h3 className="font-display font-bold text-white text-xl mb-2">PRISM is thinking</h3>
      <p className="text-gray-500 text-sm mb-10">Running a 4-agent debate for your specific context</p>

      {/* Steps */}
      <div className="w-full max-w-sm space-y-3">
        {STEPS.map((step, i) => {
          const isActive = i === currentStep
          const isComplete = completedSteps.includes(i)
          const isFuture = i > currentStep && !isComplete

          return (
            <motion.div
              key={i}
              initial={{ opacity: 0.3 }}
              animate={{ opacity: isFuture ? 0.3 : 1 }}
              className={`flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all
                ${isActive ? 'bg-prism-500/15 border border-prism-500/30' : ''}
                ${isComplete ? 'opacity-60' : ''}
              `}
            >
              <span className="text-xl w-8 text-center">{step.icon}</span>
              <span className={`text-sm flex-1 ${isActive ? 'text-white font-medium' : isComplete ? 'text-gray-500 line-through' : 'text-gray-600'}`}>
                {step.label}
              </span>
              {isComplete && <span className="text-emerald-400 text-xs">✓</span>}
              {isActive && (
                <motion.span
                  animate={{ opacity: [1, 0.3, 1] }}
                  transition={{ duration: 0.8, repeat: Infinity }}
                  className="text-prism-400 text-xs"
                >
                  ●
                </motion.span>
              )}
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
