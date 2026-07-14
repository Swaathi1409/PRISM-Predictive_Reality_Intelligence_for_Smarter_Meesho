/**
 * EmotionalMessage.jsx — Displays the warm AI-generated opening message.
 *
 * The emotional message is the first thing users see after analysis.
 * It acknowledges the life moment before presenting products.
 *
 * Library: framer-motion (MIT) for entrance animation.
 */

import { motion } from 'framer-motion'
import { Heart } from 'lucide-react'
import { EMOTION_LABELS } from '../utils/constants'

export default function EmotionalMessage({ message, emotionLevel, detectedEvent, llmRoadmap }) {
  if (!message) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: 'easeOut' }}
      id="emotional-message-section"
      className="rounded-2xl border border-prism-500/30 bg-gradient-to-br from-prism-500/10 to-meesho-pink/5 p-6"
    >
      {/* Header row */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Heart className="w-5 h-5 text-prism-400" />
          <span className="text-sm font-medium text-prism-300">PRISM understands your moment</span>
        </div>
        {emotionLevel && (
          <span className="text-xs px-2 py-1 rounded-full bg-prism-500/20 border border-prism-500/30 text-prism-300">
            {EMOTION_LABELS[emotionLevel] || emotionLevel}
          </span>
        )}
      </div>

      {/* Detected event label */}
      {detectedEvent && (
        <div className="mb-3">
          <span className="text-xs text-gray-500 uppercase tracking-wider">Life event detected: </span>
          <span className="text-xs font-semibold text-prism-300">{detectedEvent}</span>
        </div>
      )}

      {/* Main message */}
      <blockquote className="text-base text-gray-200 leading-relaxed font-medium italic border-l-2 border-prism-500 pl-4">
        {message}
      </blockquote>

      {/* LLM roadmap intro (optional) */}
      {llmRoadmap && (
        <div className="mt-4 pt-4 border-t border-prism-500/20">
          <p className="text-sm text-gray-400 leading-relaxed">{llmRoadmap}</p>
        </div>
      )}
    </motion.div>
  )
}
