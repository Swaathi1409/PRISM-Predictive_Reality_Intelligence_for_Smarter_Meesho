/**
 * UserMemoryChip.jsx — PRISM Memory Intelligence UI
 *
 * Shows a glowing animated chip above the input when PRISM has a
 * memory profile for the user. Expands into a panel showing:
 *   - Your Profile (city, company, lifestyle)
 *   - Skipping (likely-owned categories + their accessories)
 *   - Prioritising (fresh accessory picks)
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Brain, ChevronDown, X, RotateCcw, Zap, Package, Sparkles } from 'lucide-react'

export default function UserMemoryChip({ memoryTags, skippingCategories, getAccessoryHints, onClear }) {
  const [isOpen, setIsOpen] = useState(false)
  const [confirmClear, setConfirmClear] = useState(false)

  if (!memoryTags || memoryTags.length === 0) return null

  // Build unique accessory suggestions from all skipped categories
  const allOwned = skippingCategories.map(s => s.category)
  const accessories = getAccessoryHints(allOwned).slice(0, 6)

  const handleClear = () => {
    if (confirmClear) {
      onClear()
      setIsOpen(false)
      setConfirmClear(false)
    } else {
      setConfirmClear(true)
      setTimeout(() => setConfirmClear(false), 3000)
    }
  }

  return (
    <div className="w-full mb-3">
      {/* ── Chip trigger ──────────────────────────────────────────── */}
      <button
        onClick={() => setIsOpen(o => !o)}
        className="group flex items-center gap-2 px-3 py-1.5 rounded-full border border-pink-200/60 bg-gradient-to-r from-pink-50 to-purple-50 hover:from-pink-100 hover:to-purple-100 transition-all shadow-sm w-full sm:w-auto"
      >
        {/* Pulsing brain dot */}
        <span className="relative flex h-2 w-2 shrink-0">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#F43397] opacity-60" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-[#F43397]" />
        </span>

        <Brain className="w-3.5 h-3.5 text-[#F43397] shrink-0" />
        <span className="text-xs font-bold text-gray-700 whitespace-nowrap">PRISM Remembers You</span>

        {/* Tag pills */}
        <div className="flex items-center gap-1.5 overflow-hidden">
          {memoryTags.slice(0, 3).map((tag, i) => (
            <span
              key={i}
              className="hidden sm:inline-flex items-center gap-1 text-[10px] font-semibold text-gray-600 bg-white/70 px-2 py-0.5 rounded-full border border-gray-200/60 whitespace-nowrap"
            >
              {tag.icon} {tag.label}
            </span>
          ))}
        </div>

        <ChevronDown className={`w-3.5 h-3.5 text-gray-400 ml-auto transition-transform duration-200 shrink-0 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* ── Expanded Memory Panel ─────────────────────────────────── */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -6, height: 0 }}
            animate={{ opacity: 1, y: 0, height: 'auto' }}
            exit={{ opacity: 0, y: -6, height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden mt-1.5"
          >
            <div className="bg-white border border-pink-100 rounded-2xl shadow-lg overflow-hidden">
              {/* Header */}
              <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-pink-50 to-purple-50 border-b border-pink-100">
                <div className="flex items-center gap-2">
                  <Brain className="w-4 h-4 text-[#F43397]" />
                  <span className="text-xs font-bold text-gray-800">PRISM Memory Panel</span>
                </div>
                <button
                  onClick={handleClear}
                  className={`flex items-center gap-1 text-[10px] font-semibold px-2 py-1 rounded-full transition-all ${
                    confirmClear
                      ? 'bg-red-500 text-white'
                      : 'text-gray-400 hover:text-red-500 hover:bg-red-50'
                  }`}
                >
                  <RotateCcw className="w-3 h-3" />
                  {confirmClear ? 'Confirm reset' : 'Reset memory'}
                </button>
              </div>

              <div className="p-4 grid grid-cols-1 sm:grid-cols-3 gap-4">
                {/* ── Column 1: Your Profile ─────────────────────── */}
                <div>
                  <div className="flex items-center gap-1.5 mb-2">
                    <Sparkles className="w-3.5 h-3.5 text-purple-500" />
                    <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Your Profile</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {memoryTags.map((tag, i) => (
                      <span
                        key={i}
                        className="flex items-center gap-1 text-[10px] font-semibold text-purple-700 bg-purple-50 border border-purple-200/60 px-2 py-1 rounded-full"
                      >
                        {tag.icon} {tag.label}
                      </span>
                    ))}
                  </div>
                </div>

                {/* ── Column 2: Skipping ─────────────────────────── */}
                <div>
                  <div className="flex items-center gap-1.5 mb-2">
                    <Package className="w-3.5 h-3.5 text-amber-500" />
                    <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Skipping (likely own)</span>
                  </div>
                  {skippingCategories.length === 0 ? (
                    <p className="text-[10px] text-gray-400">No items tracked yet</p>
                  ) : (
                    <div className="flex flex-wrap gap-1.5">
                      {skippingCategories.slice(0, 5).map((item, i) => (
                        <span
                          key={i}
                          title={`Accessories: ${item.accessories.join(', ')}`}
                          className="flex items-center gap-1 text-[10px] font-semibold text-amber-700 bg-amber-50 border border-amber-200/60 px-2 py-1 rounded-full"
                        >
                          📦 {item.category.replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* ── Column 3: Prioritising ─────────────────────── */}
                <div>
                  <div className="flex items-center gap-1.5 mb-2">
                    <Zap className="w-3.5 h-3.5 text-emerald-500" />
                    <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">Prioritising for you</span>
                  </div>
                  {accessories.length === 0 ? (
                    <p className="text-[10px] text-gray-400">Submit a query to start</p>
                  ) : (
                    <div className="flex flex-wrap gap-1.5">
                      {accessories.map((acc, i) => (
                        <span
                          key={i}
                          className="flex items-center gap-1 text-[10px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200/60 px-2 py-1 rounded-full"
                        >
                          ✨ {acc}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
