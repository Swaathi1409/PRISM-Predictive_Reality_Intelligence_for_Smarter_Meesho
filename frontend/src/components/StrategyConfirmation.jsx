import { motion, AnimatePresence } from 'framer-motion'
import { ExternalLink, X } from 'lucide-react'

export default function StrategyConfirmation({ selectedStrategy, strategies, onClear }) {
  if (!selectedStrategy) return null;

  // Find the recommended strategy
  const recommendedStrategy = strategies.find(s => s.recommended);
  const pickedAgainstRecommendation = recommendedStrategy && recommendedStrategy.strategy_key !== selectedStrategy.strategy_key;

  // Render Soch's note
  let sochNote = "";
  if (pickedAgainstRecommendation) {
    if (selectedStrategy.strategy_key === 'buy_now') {
      sochNote = `Noted. You're prioritising certainty over savings — completely valid if your deadline is firm. Proceeding with Buy Now at Rs ${selectedStrategy.price.toLocaleString('en-IN')}.`;
    } else if (selectedStrategy.strategy_key === 'wait') {
      sochNote = `Noted. You're prioritising savings over immediate delivery. We will remind you when the sale window opens.`;
    } else if (selectedStrategy.strategy_key === 'split') {
      sochNote = `Noted. You're splitting the payment. PRISM will add the upcoming installment to your financial calendar.`;
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      className="mt-5 rounded-2xl border border-prism-400/50 bg-prism-900/20 p-5 relative overflow-hidden"
    >
      <button 
        onClick={onClear}
        className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
      >
        <X className="w-5 h-5" />
      </button>

      <h3 className="font-display font-bold text-white text-lg mb-4">
        {selectedStrategy.strategy_key === 'buy_now' && "You chose to Buy Now"}
        {selectedStrategy.strategy_key === 'wait' && "You chose to Wait for Sale"}
        {selectedStrategy.strategy_key === 'split' && "You chose to Split Payment"}
      </h3>

      {/* Confirmation content based on selected strategy */}
      {selectedStrategy.strategy_key === 'buy_now' && (
        <div className="space-y-4">
          <p className="text-sm text-gray-300">
            You chose to buy now at Rs {selectedStrategy.price.toLocaleString('en-IN')}. 
            {pickedAgainstRecommendation ? "" : " This eliminates all waiting risk, ensuring you have the item before your event."}
          </p>
          {pickedAgainstRecommendation && (
            <div className="bg-prism-800/40 border border-prism-500/30 rounded-lg p-3">
              <p className="text-sm text-prism-200"><span className="font-semibold text-prism-400">Soch noted:</span> {sochNote}</p>
            </div>
          )}
          <button disabled className="flex items-center justify-center gap-2 w-full py-3 rounded-xl bg-gray-700 text-gray-400 font-semibold cursor-not-allowed group relative">
            <ExternalLink className="w-4 h-4" />
            View on Meesho
            <span className="absolute -top-8 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity bg-gray-800 text-xs px-2 py-1 rounded border border-gray-700 pointer-events-none whitespace-nowrap">
              Live integration coming soon
            </span>
          </button>
        </div>
      )}

      {selectedStrategy.strategy_key === 'wait' && (
        <div className="space-y-4">
          <p className="text-sm text-gray-300">
            Great. {selectedStrategy.action_date}. You save Rs {selectedStrategy.savings_vs_now?.toLocaleString('en-IN') || 0}. Soch will remind you — set your reminder below.
          </p>
          {pickedAgainstRecommendation && (
            <div className="bg-prism-800/40 border border-prism-500/30 rounded-lg p-3">
              <p className="text-sm text-prism-200"><span className="font-semibold text-prism-400">Soch noted:</span> {sochNote}</p>
            </div>
          )}
          <div className="flex flex-col sm:flex-row gap-2 mt-4">
            <input 
              type="date" 
              className="bg-surface-elevated border border-surface-border rounded-lg px-3 py-2 text-sm text-white flex-1 focus:outline-none focus:border-prism-400"
              defaultValue={new Date(Date.now() + 86400000 * 6).toISOString().split('T')[0]} 
            />
            <button className="bg-prism-600 hover:bg-prism-500 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors">
              Set Reminder
            </button>
          </div>
        </div>
      )}

      {selectedStrategy.strategy_key === 'split' && (
        <div className="space-y-4">
          <p className="text-sm text-gray-300">
            {selectedStrategy.action_date}. PRISM will track this for you in your financial calendar.
          </p>
          {pickedAgainstRecommendation && (
            <div className="bg-prism-800/40 border border-prism-500/30 rounded-lg p-3">
              <p className="text-sm text-prism-200"><span className="font-semibold text-prism-400">Soch noted:</span> {sochNote}</p>
            </div>
          )}
          <div className="bg-surface-elevated border border-surface-border rounded-lg p-4 mt-2">
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs text-gray-400">Due Today</span>
              <span className="font-semibold text-white">Rs {Math.floor(selectedStrategy.price * 0.55).toLocaleString('en-IN')}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-gray-400">Due Next Month</span>
              <span className="font-semibold text-white">Rs {Math.ceil(selectedStrategy.price * 0.45).toLocaleString('en-IN')}</span>
            </div>
          </div>
          <button disabled className="flex items-center justify-center gap-2 w-full py-3 mt-2 rounded-xl bg-gray-700 text-gray-400 font-semibold cursor-not-allowed group relative">
            <ExternalLink className="w-4 h-4" />
            Continue to Meesho
            <span className="absolute -top-8 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity bg-gray-800 text-xs px-2 py-1 rounded border border-gray-700 pointer-events-none whitespace-nowrap">
              Live integration coming soon
            </span>
          </button>
        </div>
      )}

      <div className="mt-4 text-center">
        <button onClick={onClear} className="text-xs text-gray-500 hover:text-prism-400 underline decoration-gray-500 hover:decoration-prism-400 underline-offset-2 transition-colors">
          Change my mind
        </button>
      </div>
    </motion.div>
  )
}
