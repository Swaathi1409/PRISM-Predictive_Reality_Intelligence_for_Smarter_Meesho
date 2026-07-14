/**
 * constants.js — Frontend display constants for PRISM UI.
 *
 * All UI strings that vary by data value live here.
 * No raw data strings should appear in components directly.
 */

// Verdict → display config
export const VERDICT_CONFIG = {
  strong_approve: {
    label: 'Strong Approve',
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10 border-emerald-500/30',
    icon: '✦',
  },
  approve: {
    label: 'Approve',
    color: 'text-green-400',
    bg: 'bg-green-500/10 border-green-500/30',
    icon: '✓',
  },
  caution: {
    label: 'Caution',
    color: 'text-amber-400',
    bg: 'bg-amber-500/10 border-amber-500/30',
    icon: '⚠',
  },
  flag: {
    label: 'Flag',
    color: 'text-orange-400',
    bg: 'bg-orange-500/10 border-orange-500/30',
    icon: '⚑',
  },
  reject: {
    label: 'Reject',
    color: 'text-red-400',
    bg: 'bg-red-500/10 border-red-500/30',
    icon: '✕',
  },
  RECOMMEND: {
    label: 'Recommend',
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10 border-emerald-500/30',
    icon: '✦',
  },
  REJECT: {
    label: 'Reject',
    color: 'text-red-400',
    bg: 'bg-red-500/10 border-red-500/30',
    icon: '✕',
  },
}

// Agent → display config
export const AGENT_CONFIG = {
  Kismat: {
    emoji: '🛡',
    color: 'from-blue-600 to-blue-400',
    accent: 'border-blue-500/40',
    description: 'Trust Agent — verifies seller reliability',
  },
  Paisa: {
    emoji: '💰',
    color: 'from-emerald-600 to-emerald-400',
    accent: 'border-emerald-500/40',
    description: 'Budget Agent — checks price and trends',
  },
  Samay: {
    emoji: '⏱',
    color: 'from-amber-600 to-amber-400',
    accent: 'border-amber-500/40',
    description: 'Time Agent — evaluates delivery feasibility',
  },
  Soch: {
    emoji: '🧠',
    color: 'from-prism-600 to-prism-400',
    accent: 'border-prism-500/40',
    description: 'Orchestrator — final synthesis and verdict',
  },
}

// Strategy key → display config
export const STRATEGY_CONFIG = {
  buy_now: {
    label: 'Buy Now',
    icon: '⚡',
    color: 'from-emerald-600 to-teal-500',
  },
  wait: {
    label: 'Wait for Sale',
    icon: '⏳',
    color: 'from-amber-600 to-orange-500',
  },
  split: {
    label: 'Split Purchase',
    icon: '⚖',
    color: 'from-blue-600 to-indigo-500',
  },
}

// Confidence score → interpretation + color
export function getConfidenceDisplay(score) {
  if (score >= 80) return { label: 'High Confidence', color: 'text-emerald-400', ring: '#10b981' }
  if (score >= 65) return { label: 'Good Confidence', color: 'text-green-400', ring: '#4ade80' }
  if (score >= 50) return { label: 'Moderate', color: 'text-amber-400', ring: '#fbbf24' }
  if (score >= 35) return { label: 'Low Confidence', color: 'text-orange-400', ring: '#f97316' }
  return { label: 'Very Low', color: 'text-red-400', ring: '#f87171' }
}

// Priority → badge
export const PRIORITY_CONFIG = {
  must_have: { label: 'Must Have', color: 'bg-red-500/20 text-red-300 border-red-500/30' },
  should_have: { label: 'Should Have', color: 'bg-amber-500/20 text-amber-300 border-amber-500/30' },
  nice_to_have: { label: 'Nice to Have', color: 'bg-blue-500/20 text-blue-300 border-blue-500/30' },
}

// Emotion level → label
export const EMOTION_LABELS = {
  very_high: 'Very High Emotion',
  high: 'High Emotion',
  moderate: 'Moderate',
  low: 'Low',
}

export const EXAMPLE_QUERIES = [
  { text: 'My son just got into IIT Bombay, need hostel essentials', pincode: '400076', budget: 50000 },
  { text: 'Preparing for Diwali — need decor and gifts for the family', pincode: '226001', budget: 8000 },
  { text: 'Starting my first corporate job next Monday, need to look professional', pincode: '110016', budget: 15000 },
  { text: 'We are expecting our first baby in 2 months', pincode: '560001', budget: 25000 },
  { text: 'Getting married in 3 months, need wedding essentials', pincode: '600001', budget: 100000 },
]
