/**
 * Demo.jsx — Full results page showing all 6 PRISM pillars.
 *
 * Displays: EmotionalMessage, ProductCatalog (two-row), AgentDebateChamber,
 * ConfidenceGenome, TemporalSimulator, LifeEventResult, BharatContextBadge.
 * All 6 PRISM pillars are visible and interactive.
 *
 * Product display uses the new two-row layout:
 *   Row 1 — PRISM Top Picks: best product per subcategory (4-agent selected)
 *   Row 2 — More to Explore: budget variants and alternatives
 *
 * If no result in context (e.g. direct navigation), redirects to Home.
 */

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { usePrism } from '../context/PrismContext'
import LoadingOrchestrator from '../components/LoadingOrchestrator'
import EmotionalMessage from '../components/EmotionalMessage'
import ProductCatalog from '../components/ProductCatalog'
import AgentDebateChamber from '../components/AgentDebateChamber'
import ConfidenceGenome from '../components/ConfidenceGenome'
import TemporalSimulator from '../components/TemporalSimulator'
import StrategyConfirmation from '../components/StrategyConfirmation'
import LifeEventResult from '../components/LifeEventResult'
import BharatContextBadge from '../components/BharatContextBadge'

export default function Demo() {
  const navigate = useNavigate()
  const { result, query } = usePrism()
  const [selectedStrategy, setSelectedStrategy] = useState(null)

  useEffect(() => {
    if (!result) {
      navigate('/', { replace: true })
    }
  }, [result, navigate])

  if (!result) {
    return <LoadingOrchestrator />
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#0f0a1e' }}>
      <div className="fixed inset-0 pointer-events-none" style={{ background: 'radial-gradient(ellipse at top, rgba(108,43,217,0.3) 0%, transparent 70%)', opacity: 0.5 }} />

      <div className="relative pt-24 pb-20 px-4 max-w-7xl mx-auto">

        {/* Session header */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 flex items-center justify-between"
        >
          <div>
            <p className="text-xs text-gray-600 uppercase tracking-wider mb-1">
              Analysis complete · Session {result.session_id?.slice(0, 8)}
            </p>
            <h1 className="font-display font-bold text-2xl text-white">
              {result.detected_event}
            </h1>
          </div>
          {query && (
            <div className="hidden sm:block text-right">
              <p className="text-xs text-gray-600 mb-1">Your query</p>
              <p className="text-sm text-gray-400 max-w-xs truncate">
                &ldquo;{query.user_input}&rdquo;
              </p>
            </div>
          )}
        </motion.div>

        {/* ── Product Catalog: two-row layout (full width, above the fold) ── */}
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-5"
        >
          <ProductCatalog
            topPicks={result.top_picks || []}
            otherProducts={result.all_products || []}
            isSpecificAsk={result.is_specific_product_ask || false}
            primaryItemLabel={result.primary_item_label || null}
          />
        </motion.div>

        {/* Main grid: 3 cols on desktop */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

          {/* LEFT COLUMN — Confidence + Temporal */}
          <div className="lg:col-span-1 space-y-5">
            <ConfidenceGenome confidence={result.confidence} />
            <TemporalSimulator 
              strategies={result.temporal_strategies} 
              selectedStrategy={selectedStrategy}
              onSelectStrategy={setSelectedStrategy}
            />
            {selectedStrategy && (
              <StrategyConfirmation 
                selectedStrategy={selectedStrategy}
                strategies={result.temporal_strategies}
                onClear={() => setSelectedStrategy(null)}
              />
            )}
          </div>

          {/* RIGHT COLUMN — Emotional + Agents + Timeline + Bharat */}
          <div className="lg:col-span-2 space-y-5">
            <EmotionalMessage
              message={result.emotional_message}
              emotionLevel={result.emotion_level}
              detectedEvent={result.detected_event}
              llmRoadmap={result.llm_roadmap}
            />
            <AgentDebateChamber agents={result.agent_debate} />
            <LifeEventResult
              detectedEvent={result.detected_event}
              eventKey={result.event_key}
              purchaseTimeline={result.purchase_timeline}
              familySignificance={result.family_significance}
            />
            <BharatContextBadge
              context={result.bharat_context}
              stateDetected={result.state_detected}
              institutionDetected={result.institution_detected}
              detectedIntent={result.detected_intent}
            />
          </div>
        </div>

        {/* Footer note */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.5 }}
          className="text-center text-xs text-gray-700 mt-10"
        >
          Session ID: {result.session_id} · Powered by PRISM AI · v1.0.0
        </motion.p>
      </div>
    </div>
  )
}
