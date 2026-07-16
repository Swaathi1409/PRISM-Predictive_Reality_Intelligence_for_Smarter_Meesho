/**
 * BharatContextBadge.jsx — State/institution/cultural context card.
 *
 * Now shows:
 * - Institution, wattage limits
 * - State / travel destination + climate
 * - Cultural context (LLM-detected) — e.g. "Islamic majority, modest dress expected"
 * - Relevant festivals, govt scheme notes, contextual notes
 *
 * Library: framer-motion (MIT), lucide-react (ISC).
 */

import { motion } from 'framer-motion'
import { MapPin, Zap, Star, AlertTriangle, Thermometer, Globe, Heart } from 'lucide-react'

export default function BharatContextBadge({ context, stateDetected, institutionDetected, detectedIntent }) {
  if (!context) return null

  const hasContent =
    context.institution_name ||
    context.state_name ||
    context.wattage_limit ||
    (context.relevant_festivals?.length > 0) ||
    context.government_scheme_note ||
    (context.contextual_notes?.length > 0) ||
    context.cultural_context

  if (!hasContent) {
    return (
      <motion.section
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        id="bharat-context-section"
        aria-label="Bharat Cultural Context"
      >
        <div className="rounded-2xl border border-gray-500/30 bg-gray-500/5 p-5 h-full min-h-[250px] flex flex-col items-center justify-center text-center">
          <div className="w-12 h-12 rounded-2xl bg-gray-500/10 border border-gray-500/20 flex items-center justify-center mb-4 shadow-sm">
             <MapPin className="w-5 h-5 text-gray-400" />
          </div>
          <h2 className="font-display font-bold text-gray-300 text-lg mb-2">Pan-India Context Applied</h2>
          <p className="text-sm text-gray-500 max-w-[240px] leading-relaxed">No specific regional or institutional constraints detected. PRISM is applying baseline Bharat shopping patterns.</p>
        </div>
      </motion.section>
    )
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      id="bharat-context-section"
      aria-label="Bharat Cultural Context"
    >
      <div className="rounded-2xl border border-amber-500/30 bg-amber-500/5 p-5 h-full flex flex-col gap-3">
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-amber-500/20 border border-amber-500/30 flex items-center justify-center">
            <MapPin className="w-4 h-4 text-amber-400" />
          </div>
          <div>
            <h2 className="font-display font-bold text-white text-lg">Bharat Context</h2>
            <p className="text-xs text-gray-500">PRISM detected your cultural and regional context</p>
          </div>
        </div>

        {/* Detected Intent — if available */}
        {detectedIntent && (
          <div className="p-3 rounded-xl bg-violet-500/10 border border-violet-500/20">
            <div className="flex items-start gap-2">
              <Heart className="w-4 h-4 text-violet-400 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-xs text-violet-400 uppercase tracking-wider mb-0.5">Detected Intent</p>
                <p className="text-sm text-violet-200 leading-relaxed">{detectedIntent}</p>
              </div>
            </div>
          </div>
        )}

        {/* Cultural Context — prominently shown */}
        {context.cultural_context && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20">
            <div className="flex items-start gap-2">
              <Globe className="w-4 h-4 text-rose-400 mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-xs text-rose-400 uppercase tracking-wider mb-0.5">Cultural Context</p>
                <p className="text-sm text-rose-200 leading-relaxed">{context.cultural_context}</p>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {/* Institution */}
          {context.institution_name && (
            <ContextItem
              icon={<Star className="w-3.5 h-3.5 text-amber-400" />}
              label="Institution"
              value={context.institution_name}
              sub={context.institution_type?.replace('_', ' ').toUpperCase()}
            />
          )}

          {/* State / Destination */}
          {context.state_name && (
            <ContextItem
              icon={<MapPin className="w-3.5 h-3.5 text-blue-400" />}
              label={institutionDetected ? "State" : "Location / Destination"}
              value={context.state_name}
              sub={context.climate_note}
            />
          )}

          {/* Wattage limit */}
          {context.wattage_limit && (
            <ContextItem
              icon={<Zap className="w-3.5 h-3.5 text-yellow-400" />}
              label="Appliance Limit"
              value={`Max ${context.wattage_limit}W`}
              sub="Applied to product filtering"
              highlight
            />
          )}

          {/* Festivals */}
          {context.relevant_festivals?.length > 0 && (
            <ContextItem
              icon={<Star className="w-3.5 h-3.5 text-orange-400" />}
              label="Local Festivals"
              value={context.relevant_festivals.join(', ')}
            />
          )}
        </div>

        {/* Government scheme note */}
        {context.government_scheme_note && (
          <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-emerald-300 break-words min-w-0">{context.government_scheme_note}</p>
            </div>
          </div>
        )}

        {/* Contextual notes */}
        {context.contextual_notes?.length > 0 && (
          <div className="space-y-2 mt-auto">
            {context.contextual_notes.slice(0, 4).map((note, i) => (
              <div key={i} className="flex items-start gap-2">
                <Thermometer className="w-3.5 h-3.5 text-amber-400 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-gray-400 break-words min-w-0 leading-relaxed">{note}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </motion.section>
  )
}

function ContextItem({ icon, label, value, sub, highlight }) {
  return (
    <div className={`rounded-xl border p-3 ${highlight
      ? 'border-yellow-500/30 bg-yellow-500/5'
      : 'border-surface-border bg-surface-elevated'
    }`}>
      <div className="flex items-center gap-1.5 mb-1">
        {icon}
        <span className="text-xs text-gray-500 uppercase tracking-wider">{label}</span>
      </div>
      <p className="text-sm font-semibold text-white">{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-0.5">{sub}</p>}
    </div>
  )
}
