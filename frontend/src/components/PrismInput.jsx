/**
 * PrismInput.jsx — Main input form for PRISM analysis.
 *
 * Every field is labeled for accessibility. Loading and error states
 * provide clear feedback. Example query chips help new users get started.
 *
 * Libraries: framer-motion (MIT), lucide-react (ISC).
 */

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, MapPin, IndianRupee, Loader2, AlertCircle, Sparkles } from 'lucide-react'
import { EXAMPLE_QUERIES } from '../utils/constants'

export default function PrismInput({ onSubmit, isLoading, error }) {
  const [userInput, setUserInput] = useState('')
  const [pincode, setPincode] = useState('')
  const [budget, setBudget] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!userInput.trim() || isLoading) return
    onSubmit({
      user_input: userInput.trim(),
      user_pincode: pincode || '600001',
      budget: budget ? parseInt(budget, 10) : null,
    })
  }

  const fillExample = (example) => {
    setUserInput(example.text)
    setPincode(String(example.pincode))
    setBudget(String(example.budget))
  }

  const canSubmit = userInput.trim().length >= 5 && !isLoading

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3, duration: 0.6 }}
      className="w-full max-w-2xl mx-auto"
    >
      <form onSubmit={handleSubmit} id="prism-analysis-form" noValidate>
        <div className="rounded-2xl border border-surface-border bg-surface-card/80 backdrop-blur-sm p-6 shadow-card">

          {/* Main input */}
          <div className="mb-4">
            <label htmlFor="user-input" className="block text-sm font-medium text-gray-300 mb-2">
              What's happening in your life? <span className="text-prism-400">*</span>
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-3.5 w-5 h-5 text-gray-500 pointer-events-none" />
              <textarea
                id="user-input"
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                placeholder="e.g. My daughter just got into NIT Trichy, need hostel essentials under Rs 15000..."
                rows={3}
                maxLength={500}
                required
                disabled={isLoading}
                className="w-full pl-10 pr-4 py-3 bg-surface-elevated border border-surface-border rounded-xl
                  text-white placeholder-gray-500 resize-none focus:outline-none focus:ring-2
                  focus:ring-prism-500 focus:border-transparent transition-all text-sm leading-relaxed
                  disabled:opacity-50"
              />
              <span className="absolute bottom-2 right-3 text-xs text-gray-600">
                {userInput.length}/500
              </span>
            </div>
          </div>

          {/* Pincode + Budget row */}
          <div className="grid grid-cols-2 gap-3 mb-5">
            <div>
              <label htmlFor="pincode-input" className="block text-sm font-medium text-gray-300 mb-2">
                Delivery Pincode
              </label>
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                <input
                  id="pincode-input"
                  type="text"
                  value={pincode}
                  onChange={(e) => setPincode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="600001"
                  maxLength={6}
                  pattern="\d{6}"
                  disabled={isLoading}
                  className="w-full pl-9 pr-3 py-2.5 bg-surface-elevated border border-surface-border rounded-xl
                    text-white placeholder-gray-500 focus:outline-none focus:ring-2
                    focus:ring-prism-500 focus:border-transparent transition-all text-sm
                    disabled:opacity-50"
                />
              </div>
              <p className="text-xs text-gray-600 mt-1">Defaults to 600001</p>
            </div>

            <div>
              <label htmlFor="budget-input" className="block text-sm font-medium text-gray-300 mb-2">
                Budget (optional)
              </label>
              <div className="relative">
                <IndianRupee className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                <input
                  id="budget-input"
                  type="number"
                  value={budget}
                  onChange={(e) => setBudget(e.target.value)}
                  placeholder="50000"
                  min={0}
                  max={10000000}
                  disabled={isLoading}
                  className="w-full pl-9 pr-3 py-2.5 bg-surface-elevated border border-surface-border rounded-xl
                    text-white placeholder-gray-500 focus:outline-none focus:ring-2
                    focus:ring-prism-500 focus:border-transparent transition-all text-sm
                    disabled:opacity-50"
                />
              </div>
              <p className="text-xs text-gray-600 mt-1">In Indian Rupees</p>
            </div>
          </div>

          {/* Submit button */}
          <button
            type="submit"
            id="analyze-btn"
            disabled={!canSubmit}
            className="w-full py-3 px-6 rounded-xl font-display font-semibold text-white text-base
              bg-prism-gradient hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed
              transition-all active:scale-[0.98] shadow-prism hover:shadow-prism-lg
              flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                PRISM is thinking...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                Analyse with PRISM
              </>
            )}
          </button>
        </div>
      </form>

      {/* Error display */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mt-3 p-4 rounded-xl bg-red-500/10 border border-red-500/30 flex items-start gap-3"
            role="alert"
          >
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-red-300">Analysis failed</p>
              <p className="text-xs text-red-400 mt-0.5">{error}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Example queries */}
      <div className="mt-5">
        <p className="text-xs text-gray-500 mb-2 text-center">Try an example:</p>
        <div className="flex flex-wrap gap-2 justify-center">
          {EXAMPLE_QUERIES.map((ex, i) => (
            <button
              key={i}
              onClick={() => fillExample(ex)}
              disabled={isLoading}
              className="text-xs px-3 py-1.5 rounded-full border border-surface-border text-gray-400
                hover:border-prism-500/50 hover:text-prism-300 hover:bg-prism-500/5
                transition-all disabled:opacity-40"
            >
              {ex.text.slice(0, 40)}…
            </button>
          ))}
        </div>
      </div>
    </motion.div>
  )
}
