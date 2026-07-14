/**
 * Home.jsx — Landing page with the PRISM input form.
 *
 * Shows the hero section, input form, and session history chips.
 * On successful analysis, navigates to /demo with results in context.
 */

import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Sparkles, Shield, Clock, Brain, Dna, Heart, MapPin } from 'lucide-react'
import PrismInput from '../components/PrismInput'
import SessionHistory from '../components/SessionHistory'
import { usePrismAnalysis } from '../hooks/usePrismAnalysis'
import { useSessionHistory } from '../hooks/useSessionHistory'
import { usePrism } from '../context/PrismContext'

const PILLARS = [
  { icon: <Brain className="w-5 h-5" />, label: 'Life Event Detection', desc: 'Understands the human moment behind every purchase' },
  { icon: <Shield className="w-5 h-5" />, label: 'Multi-Agent Debate', desc: 'Kismat, Paisa, Samay & Soch evaluate every product' },
  { icon: <Dna className="w-5 h-5" />, label: 'Confidence Genome', desc: 'Decomposes every score into auditable factors' },
  { icon: <Clock className="w-5 h-5" />, label: 'Temporal Simulator', desc: 'Buy Now, Wait, or Split — with real pricing' },
  { icon: <Heart className="w-5 h-5" />, label: 'Emotional Layer', desc: 'Register-switched warm, culturally-aware messages' },
  { icon: <MapPin className="w-5 h-5" />, label: 'Bharat Context', desc: 'Institution rules, state climate, government schemes' },
]

export default function Home() {
  const navigate = useNavigate()
  const { setResult, setQuery } = usePrism()
  const { mutate: analyze, isPending, error } = usePrismAnalysis()
  const { history, addToHistory, clearHistory } = useSessionHistory()

  const handleSubmit = (formData) => {
    analyze(formData, {
      onSuccess: (data) => {
        setResult(data)
        setQuery(formData)
        addToHistory(formData)
        navigate('/demo')
      },
    })
  }

  return (
    <div className="min-h-screen bg-surface-DEFAULT">
      {/* Background glow */}
      <div className="fixed inset-0 bg-glow-gradient pointer-events-none" />

      <div className="relative pt-24 pb-16 px-4 max-w-7xl mx-auto">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
          className="text-center mb-12"
        >
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-prism-500/30 bg-prism-500/10 text-prism-300 text-sm font-medium mb-6"
          >
            <Sparkles className="w-4 h-4" />
            ScriptedBy&#123;Her&#125; 2.0 · Meesho Hackathon 2026
          </motion.div>

          <h1 className="font-display font-black text-5xl sm:text-6xl lg:text-7xl text-white mb-4 leading-tight">
            <span className="bg-prism-gradient bg-clip-text text-transparent">PRISM</span>
          </h1>

          <p className="font-display text-xl sm:text-2xl text-gray-300 font-semibold mb-2">
            Predictive Reality Intelligence for Smarter Meesho
          </p>

          <p className="text-gray-500 text-base max-w-xl mx-auto leading-relaxed">
            The first agentic AI that understands <em>why</em> you're buying, not just <em>what</em> you want.
            Built for India's next 500 million shoppers.
          </p>
        </motion.div>

        {/* Input form */}
        <PrismInput onSubmit={handleSubmit} isLoading={isPending} error={error?.message} />

        {/* Session history */}
        <SessionHistory
          history={history}
          onSelect={(item) => handleSubmit(item)}
          onClear={clearHistory}
        />

        {/* 6 Pillars */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.6 }}
          className="mt-16"
        >
          <p className="text-center text-sm text-gray-600 mb-6 uppercase tracking-widest font-medium">The 6 PRISM Pillars</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {PILLARS.map((pillar, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.7 + i * 0.07 }}
                className="rounded-xl border border-surface-border bg-surface-card p-4 text-center hover:border-prism-500/40 hover:bg-surface-elevated transition-all group"
              >
                <div className="w-10 h-10 rounded-xl bg-prism-500/10 border border-prism-500/20 flex items-center justify-center mx-auto mb-2 text-prism-400 group-hover:bg-prism-500/20 transition-all">
                  {pillar.icon}
                </div>
                <p className="text-xs font-semibold text-white mb-1">{pillar.label}</p>
                <p className="text-xs text-gray-600 leading-tight">{pillar.desc}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  )
}
