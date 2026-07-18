import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, Mic, Activity, CheckCircle, Code, Brain, Send, MicOff, Calendar, ShoppingCart, Check, X, Trash2, CreditCard, ShieldCheck, Loader2, Copy, ChevronRight, FlaskConical, Rocket, AlertCircle } from 'lucide-react'
import { usePrismAnalysis } from '../hooks/usePrismAnalysis'
import { useUserMemory } from '../hooks/useUserMemory'
import LoadingOrchestrator from '../components/LoadingOrchestrator'
import AgentDebateChamber from '../components/AgentDebateChamber'
import ConfidenceGenome from '../components/ConfidenceGenome'
import BharatContextBadge from '../components/BharatContextBadge'

import TopPickHero from '../components/TopPickHero'

// 3 Pre-loaded Scenarios
const SCENARIOS = [
  { label: "🎓 NIT Trichy hostel move", query: "My daughter got into NIT Trichy starting August.", pincode: "620015", budget: 15000 },
  { label: "💒 Daughter's wedding, Jaipur", query: "My daughter's wedding is next month in Jaipur.", pincode: "302001", budget: 50000 },
  { label: "🪔 Diwali prep, budget ₹3000", query: "Need to prepare for Diwali next week.", pincode: "110001", budget: 3000 },
  { label: "💼 Corporate job joining", query: "Starting my first corporate job in Bangalore next week.", pincode: "560001", budget: 10000 },
]

export default function Home() {
  const [userInput, setUserInput] = useState('')
  const [isXRayOpen, setIsXRayOpen] = useState(false)
  const [showJudgeMode, setShowJudgeMode] = useState(false)
  const [judgeTab, setJudgeTab] = useState('howto') // 'howto' | 'scope' | 'vision'
  const [result, setResult] = useState(null)
  const [selectedProduct, setSelectedProduct] = useState(null)
  const [isListening, setIsListening] = useState(false)
  const [cartItems, setCartItems] = useState([])
  const [isCartOpen, setIsCartOpen] = useState(false)
  
  useEffect(() => {
    setSelectedTemporalStrategy(null)
  }, [selectedProduct])
  const [checkoutState, setCheckoutState] = useState('idle') // 'idle' | 'processing' | 'success'
  const [toast, setToast] = useState(null)
  const [orderId, setOrderId] = useState(null)
  const [copiedQuery, setCopiedQuery] = useState(null)
  const [selectedTemporalStrategy, setSelectedTemporalStrategy] = useState(null)
  const brainRef = useRef(null)

  // ── Memory Mining hook ───────────────────────────────────────────────
  const {
    hasMemory, memoryTags, skippingCategories,
    getAvoidCategories, getContextString, getAccessoryHints, addSessionResult, clearMemory
  } = useUserMemory()

  const showToast = (msg) => {
    setToast(msg)
    setTimeout(() => setToast(null), 3000)
  }

  const handleAddToCart = () => {
    setCartItems([...cartItems, selectedProduct])
    showToast(`Added to Cart!`)
  }

  const handleBuyNow = () => {
    setIsCartOpen(false)
    setOrderId(Math.floor(100000 + Math.random() * 900000)) // generate once, not inline in JSX
    setCheckoutState('processing')
    setTimeout(() => {
        setCheckoutState('success')
        setCartItems([])
        setTimeout(() => {
            setCheckoutState('idle')
            setSelectedProduct(null)
        }, 3000)
    }, 2500)
  }

  const removeFromCart = (idx) => {
    const newCart = [...cartItems]
    newCart.splice(idx, 1)
    setCartItems(newCart)
  }

  const handleNotifyMe = () => {
    showToast(`We'll notify you when this is available!`)
  }

  const handleToggleBrain = () => {
    const newState = !isXRayOpen
    setIsXRayOpen(newState)
    if (newState && typeof window !== 'undefined' && window.innerWidth < 1024) {
      setTimeout(() => {
        if (brainRef.current) {
          brainRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }
      }, 150)
    }
  }
  const [targetDate, setTargetDate] = useState('')
  const [pincode, setPincode] = useState('600001')
  const [budget, setBudget] = useState('10000')
  
  const { mutate: analyze, isPending, error } = usePrismAnalysis()

  const handleListen = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert("Speech recognition is not supported in this browser. Please use Chrome or Edge.")
      return
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SpeechRecognition()
    recognition.lang = 'en-IN' // English India
    recognition.interimResults = false
    recognition.maxAlternatives = 1

    recognition.onstart = () => {
      setIsListening(true)
      setUserInput('') // clear input on new voice start
    }

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript
      setUserInput(transcript)
      // Auto submit — pass current form state, not hardcoded defaults
      setTimeout(() => {
         handleAnalyze(transcript, pincode || "600001", budget ? parseInt(budget) : null, null)
      }, 500)
    }

    recognition.onerror = (event) => {
      console.error("Speech error:", event.error)
      setIsListening(false)
    }

    recognition.onend = () => {
      setIsListening(false)
    }

    recognition.start()
  }

  const handleScenarioClick = (scenario) => {
    setUserInput(scenario.query)
    setPincode(scenario.pincode)
    setBudget(scenario.budget.toString())
    setTargetDate('')
    handleAnalyze(scenario.query, scenario.pincode, scenario.budget, null)
  }

  const handleManualSubmit = (e) => {
    if (e) e.preventDefault()
    if (!userInput.trim()) return
    handleAnalyze(userInput.trim(), (pincode || "600001").trim(), budget ? parseInt(budget) : null, targetDate)
  }

  const handleAnalyze = (query, pincode, budget, date) => {
    setResult(null) // reset
    const payload = { user_input: query, user_pincode: pincode, budget }
    if (date) payload.target_date = date

    // ── Memory Mining: inject context into payload ────────────────────────
    const contextStr = getContextString()
    if (contextStr) payload.user_context = contextStr
    const avoidCats = getAvoidCategories()
    if (avoidCats.length > 0) payload.avoid_categories = avoidCats

    analyze(payload, {
      onSuccess: (data) => {
        setResult(data)
        setIsXRayOpen(true) // auto-reveal the AI brain on first result so judges see the agent debate
        // Mine the result to update behavioral profile for next session
        addSessionResult(query, budget, data)
      }
    })
  }

  return (
    <div className="min-h-[100dvh] bg-[#fafafa] flex flex-col items-center justify-center p-2 sm:p-4 lg:p-8 font-sans overflow-x-hidden relative">
      
      {/* Premium AI x Meesho Themed Background */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden bg-slate-50">
        <div className="absolute -top-[20%] -left-[10%] w-[70%] h-[70%] rounded-full bg-[#F43397]/25 blur-[120px] mix-blend-multiply animate-[pulse_6s_ease-in-out_infinite]" />
        <div className="absolute -bottom-[20%] -right-[10%] w-[70%] h-[70%] rounded-full bg-prism-600/25 blur-[120px] mix-blend-multiply animate-[pulse_8s_ease-in-out_infinite_reverse]" />
        <div className="absolute top-[20%] left-[40%] w-[50%] h-[50%] rounded-full bg-indigo-500/15 blur-[120px] mix-blend-multiply animate-[pulse_7s_ease-in-out_infinite]" />
        <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg width=\'24\' height=\'24\' viewBox=\'0 0 24 24\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Ccircle cx=\'2\' cy=\'2\' r=\'1.5\' fill=\'rgba(0,0,0,0.08)\'/%3E%3C/svg%3E')] [mask-image:linear-gradient(to_bottom,white_40%,transparent)]" />
      </div>

      <div className={`relative z-10 flex flex-col lg:flex-row w-full max-w-[1400px] transition-all duration-500 ease-in-out gap-4 lg:gap-8 justify-center items-stretch ${isXRayOpen ? 'min-h-[150vh] lg:min-h-0 lg:h-[90vh]' : 'h-[95vh] lg:h-[90vh]'}`}>
        
        {/* LEFT: MEESHO APP SHELL */}
        <div className={`relative w-full max-w-full transition-all duration-500 ease-in-out shrink-0 overflow-hidden flex flex-col bg-white
          ${isXRayOpen 
            ? 'sm:max-w-[480px] h-[85vh] lg:h-full rounded-3xl lg:rounded-[40px] shadow-2xl border-4 lg:border-[8px] border-gray-900 mx-auto lg:mx-0' 
            : 'lg:max-w-5xl h-[100vh] lg:h-full rounded-none lg:rounded-3xl shadow-none lg:shadow-xl border-0 lg:border border-gray-200 mx-auto'}
        `}>
          
          {/* Mobile Status Bar Fake */}
          <div className={`w-full h-7 bg-white flex items-center justify-between px-6 pt-2 shrink-0 ${!isXRayOpen ? 'lg:hidden' : ''}`}>
            <span className="text-[10px] font-medium">9:41</span>
            <div className="flex gap-1">
              <div className="w-4 h-2.5 bg-black rounded-sm"></div>
            </div>
          </div>

          {/* App Header */}
          <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between bg-white z-10 shadow-sm shrink-0">
            <h1 className="text-2xl font-bold text-[#F43397]">meesho</h1>
            <div className="flex items-center gap-4">
              <button 
                onClick={() => setShowJudgeMode(true)}
                className="bg-prism-600 hover:bg-prism-700 text-white px-3 py-1.5 rounded-full text-xs font-semibold shadow-sm transition-all flex items-center gap-1.5"
              >
                <Sparkles className="w-3 h-3" /> Judge Mode
              </button>
              <div className="relative cursor-pointer transition-transform hover:scale-105 active:scale-95" onClick={() => setIsCartOpen(true)}>
                <ShoppingCart className="w-5 h-5 text-gray-700" />
                {cartItems.length > 0 && (
                  <span className="absolute -top-1.5 -right-1.5 bg-[#F43397] text-white text-[10px] font-bold w-4 h-4 flex items-center justify-center rounded-full">
                    {cartItems.length}
                  </span>
                )}
              </div>
              <div className="relative">
                <button 
                  onClick={handleToggleBrain}
                  className={`p-1.5 rounded-full transition-colors relative z-10 ${isXRayOpen ? 'bg-prism-100 text-prism-600' : 'bg-gray-100 text-gray-400 hover:bg-gray-200 hover:text-gray-600'}`}
                  title="Toggle PRISM Brain X-Ray"
                >
                  <Brain className="w-5 h-5" />
                </button>
                {!isXRayOpen && result && (
                  <div className="absolute top-full right-0 mt-2 flex flex-col items-center animate-bounce z-20 pointer-events-none">
                    <div className="w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-b-[6px] border-b-prism-600"></div>
                    <div className="bg-prism-600 text-white text-[10px] font-bold px-2.5 py-1 rounded shadow-lg whitespace-nowrap tracking-wide">
                      See AI Brain
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* App Content Area */}
          <div className="flex-1 overflow-y-auto bg-[#F9F9F9] relative flex flex-col scrollbar-hide">
            {!isPending && !result && (
              <div className="p-5 flex-1 flex flex-col">
                <div className="mb-8 mt-10 text-center">
                  <div className="w-16 h-16 bg-pink-50 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-pink-100">
                     <Brain className="w-8 h-8 text-[#F43397]" />
                  </div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">PRISM Brain</h2>
                  <p className="text-sm text-gray-500 max-w-[250px] mx-auto">Tap the mic and tell me what's happening in your life.</p>
                </div>

                <div className="relative mb-8">
                  {/* Memory Mining chip hidden from frontend per user request */}
                  <form onSubmit={handleManualSubmit} className="flex flex-col gap-3">
                    <div className="flex gap-2 relative">
                      <div className="relative flex-1 group">
                        <span className="absolute -top-6 left-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                          What's happening? <span className="text-red-500">*</span>
                        </span>
                        <input
                          value={userInput}
                          onChange={(e) => setUserInput(e.target.value)}
                          placeholder={isListening ? "Listening..." : "E.g. Moving to hostel next week..."}
                          className={`w-full text-gray-900 bg-white border ${isListening ? 'border-[#F43397] ring-2 ring-pink-100' : 'border-gray-200'} rounded-full py-4 pl-5 pr-14 shadow-sm focus:outline-none focus:border-[#F43397] focus:ring-1 focus:ring-[#F43397] transition-all mt-4`}
                          required
                        />
                        <button 
                          type="button" 
                          onClick={isListening ? () => {} : handleListen}
                          className={`absolute right-2 top-6 p-2 rounded-full transition-all shadow-sm ${isListening ? 'bg-red-500 text-white animate-pulse' : 'bg-gray-100 text-gray-500 hover:bg-[#F43397] hover:text-white'}`}
                          title="Voice Input"
                        >
                          {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                        </button>
                      </div>
                      {userInput.trim() && !isListening && (
                        <button type="submit" className="p-4 mt-4 bg-[#F43397] text-white rounded-full hover:bg-pink-600 transition-transform active:scale-95 shadow-md flex-shrink-0 flex items-center justify-center">
                          <Send className="w-5 h-5" />
                        </button>
                      )}
                    </div>
                    
                    {error && (
                      <div className="text-red-500 text-xs font-semibold px-2 py-1 bg-red-50 rounded-lg border border-red-100">
                        Error: {error.message || "Failed to process request. Please check inputs."}
                      </div>
                    )}

                    {/* Optional Target Date */}
                    <div className="flex items-center gap-2 px-1">
                      <Calendar className="w-4 h-4 text-gray-400" />
                      <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">When is the event? (Optional)</span>
                      <input 
                        type="date" 
                        value={targetDate} 
                        onChange={(e) => setTargetDate(e.target.value)}
                        className="ml-auto text-xs bg-white border border-gray-200 rounded-lg px-2 py-1 text-gray-700 outline-none focus:border-[#F43397]"
                      />
                    </div>
                    
                    {/* Additional Context Inputs */}
                    <div className="flex gap-2">
                      <div className="flex-1">
                         <label className="block text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1 px-1">Pincode (Optional)</label>
                         <input 
                           type="text" 
                           value={pincode} 
                           onChange={(e) => setPincode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                           placeholder="600001" 
                           className="w-full text-sm bg-white border border-gray-200 rounded-xl px-3 py-2 text-gray-700 outline-none focus:border-[#F43397]"
                         />
                      </div>
                      <div className="flex-1">
                         <label className="block text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1 px-1">Budget (Optional)</label>
                         <input 
                           type="number" 
                           value={budget} 
                           onChange={(e) => setBudget(e.target.value)}
                           placeholder="Any" 
                           className="w-full text-sm bg-white border border-gray-200 rounded-xl px-3 py-2 text-gray-700 outline-none focus:border-[#F43397]"
                         />
                      </div>
                    </div>
                  </form>
                </div>

                <div className="space-y-3">
                  <p className="text-xs font-bold text-gray-400 uppercase tracking-wider px-2">Try a scenario</p>
                  {SCENARIOS.map((sc, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleScenarioClick(sc)}
                      className="w-full text-left px-4 py-3.5 bg-white rounded-xl border border-gray-100 shadow-sm text-sm text-gray-700 font-medium hover:border-[#F43397] hover:text-[#F43397] transition-all flex items-center gap-3"
                    >
                      {sc.label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {isPending && (
              <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-white h-full">
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ repeat: Infinity, duration: 1.5 }}
                  className="w-20 h-20 bg-pink-50 rounded-full flex items-center justify-center mb-6 shadow-sm border border-pink-100"
                >
                  <Sparkles className="w-10 h-10 text-[#F43397]" />
                </motion.div>
                <h3 className="font-bold text-gray-900 text-xl">Thinking...</h3>
                <p className="text-sm text-gray-500 mt-2 max-w-[200px]">PRISM is analyzing your life event and predicting needs.</p>
              </div>
            )}

            {result && !isPending && (
              <div className="flex-1 flex flex-col bg-gray-50">
                {/* Chat Bubble for emotional message */}
                <div className="p-5 bg-white shadow-sm border-b border-gray-100">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-[#F43397] flex flex-shrink-0 items-center justify-center shadow-sm">
                      <Sparkles className="w-4 h-4 text-white" />
                    </div>
                    <div className="bg-gray-50 p-4 rounded-2xl rounded-tl-sm border border-gray-100 shadow-sm">
                      <p className="text-sm text-gray-800 leading-relaxed font-medium">
                        {result.emotional_message}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Timeline and Products */}
                <div className="p-5 space-y-6 flex-1 overflow-y-auto pb-8">
                  {/* ⭐ Top Pick Hero — shown first, prominently */}
                  {result.top_recommendation?.id !== 'NONE' && (
                    <div>
                      <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-2 px-1">⭐ Top Pick</p>
                      <TopPickHero
                        product={result.top_recommendation}
                        isXRayOpen={isXRayOpen}
                        onView={setSelectedProduct}
                      />
                    </div>
                  )}

                  <h3 className="font-bold text-gray-900 flex items-center gap-2 text-lg">
                    <CheckCircle className="w-5 h-5 text-emerald-500" />
                    {result.is_specific_product_ask && result.primary_item_label
                      ? `Find Your ${result.primary_item_label.charAt(0).toUpperCase() + result.primary_item_label.slice(1)}`
                      : 'Full Purchase Plan'}
                  </h3>
                  
                  <div className="space-y-6">
                    {result.is_specific_product_ask && result.primary_item_label ? (() => {
                      // ── Specific-ask mode: two clean phases ──────────────────
                      const itemLabel = result.primary_item_label;
                      const ItemDisplay = itemLabel.charAt(0).toUpperCase() + itemLabel.slice(1);
                      const allTopPicks = result.top_picks || [];
                      const allOthers   = result.all_products || [];
                      const oosItems    = allTopPicks.filter(p => p.stock_status === 'out_of_stock');
                      const inStockPrimary = allTopPicks.filter(p => p.stock_status !== 'out_of_stock');
                      const accessories    = allOthers.filter(p => p.stock_status !== 'out_of_stock');

                      const renderProductCard = (prod, j) => {
                        const isTopPick   = allTopPicks.some(t => t.id === prod.id);
                        const namePart    = (prod.name || '').split(' ').slice(0, 2).join('+');
                        const imgFallback = `https://picsum.photos/seed/${encodeURIComponent(namePart)}/400/400`;
                        const imgSrc      = prod.image_url
                          || (prod.image_placeholder ? `/images/${prod.image_placeholder}.jpg` : imgFallback);
                        return (
                          <div
                            key={prod.id || j}
                            className={`shrink-0 ${!isXRayOpen ? 'w-48' : 'w-36'} bg-white border ${
                              isTopPick ? 'border-[#F43397]/40 ring-1 ring-[#F43397]/20' : 'border-gray-100'
                            } rounded-2xl shadow-sm hover:shadow-md transition-shadow snap-center overflow-hidden cursor-pointer group`}
                            onClick={() => setSelectedProduct(prod)}
                          >
                            <div className="relative w-full aspect-square bg-gray-50 overflow-hidden">
                              <img
                                src={imgSrc}
                                onError={(e) => { e.target.onerror = null; e.target.src = imgFallback; }}
                                alt={prod.name}
                                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                              />
                              {isTopPick && (
                                <div className="absolute top-2 left-2 bg-[#F43397] text-white text-[9px] font-bold px-2 py-0.5 rounded-full shadow-sm">
                                  Top Pick
                                </div>
                              )}
                              <div className="absolute bottom-2 right-2 w-6 h-6 bg-white/80 backdrop-blur-sm rounded-full flex items-center justify-center shadow-sm">
                                <span className="text-[8px] font-bold text-[#F43397]">M</span>
                              </div>
                            </div>
                            <div className="p-3">
                              <p className={`font-medium text-gray-800 leading-tight ${!isXRayOpen ? 'text-sm line-clamp-2' : 'text-xs truncate'}`}>
                                {prod.name}
                              </p>
                              <div className="flex items-end gap-2 mt-2">
                                <span className="text-base font-bold text-gray-900">&#8377;{prod.price}</span>
                                <span className="text-xs text-gray-400 line-through mb-0.5">
                                  &#8377;{prod.price + Math.floor(prod.price * 0.4)}
                                </span>
                              </div>
                              <button className="w-full mt-3 py-2 bg-pink-50 text-[#F43397] rounded-xl text-xs font-bold hover:bg-[#F43397] hover:text-white transition-colors">
                                View Product
                              </button>
                            </div>
                          </div>
                        );
                      };

                      return (
                        <>
                          {/* Phase 1: The primary item */}
                          <div className="relative pl-5 border-l-2 border-gray-200 ml-2">
                            <div className="absolute -left-[9px] top-0.5 w-4 h-4 rounded-full bg-white border-2 border-[#F43397]"></div>
                            <div className="flex items-center gap-2 mb-1">
                              <span className="w-2 h-2 rounded-full flex-shrink-0 bg-red-400"></span>
                              <h4 className="font-bold text-sm text-gray-900">
                                {ItemDisplay}s Available Now
                              </h4>
                            </div>
                            <p className="text-xs text-gray-500 mb-3 leading-relaxed">
                              Best {itemLabel} options ranked by PRISM's 4-agent system — price, trust &amp; timing verified.
                            </p>
                            {inStockPrimary.length > 0 ? (
                              <div className="flex gap-4 overflow-x-auto pb-5 snap-x scrollbar-product">
                                {inStockPrimary.map((prod, j) => renderProductCard(prod, j))}
                              </div>
                            ) : (
                              <div className="flex items-center gap-3 bg-amber-50 border border-dashed border-amber-200 rounded-xl px-4 py-3 mb-3">
                                <span className="text-xl">📦</span>
                                <div>
                                  <p className="text-xs font-semibold text-amber-700">No {itemLabel}s in catalog right now</p>
                                  <p className="text-xs text-gray-400">We'll notify you when they're available.</p>
                                </div>
                              </div>
                            )}
                            {/* OOS stubs */}
                            {oosItems.length > 0 && (
                              <div className="flex gap-4 overflow-x-auto pb-3 snap-x">
                                {oosItems.map((prod, j) => (
                                  <div key={j} className={`shrink-0 ${!isXRayOpen ? 'w-48' : 'w-36'} bg-white border border-amber-100 rounded-2xl shadow-sm snap-center overflow-hidden`}>
                                    <div className="relative w-full aspect-square bg-amber-50 overflow-hidden flex items-center justify-center">
                                      <span className="text-3xl">📦</span>
                                      <div className="absolute top-2 left-2 bg-amber-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full shadow-sm">Out of Stock</div>
                                    </div>
                                    <div className="p-3">
                                      <p className="text-sm font-medium text-gray-700 leading-tight line-clamp-2">{prod.name}</p>
                                      <p className="text-xs text-amber-600 font-semibold mt-2">Not available currently</p>
                                      <button
                                        onClick={(e) => { e.stopPropagation(); showToast(`Alert set for ${prod.name}`); }}
                                        className="w-full mt-3 py-2 bg-amber-50 text-amber-600 rounded-xl text-xs font-bold hover:bg-amber-500 hover:text-white transition-colors border border-amber-200"
                                      >
                                        🔔 Notify Me
                                      </button>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>

                          {/* Phase 2: Accessories */}
                          {accessories.length > 0 && (
                            <div className="relative pl-5 border-l-2 border-gray-200 ml-2">
                              <div className="absolute -left-[9px] top-0.5 w-4 h-4 rounded-full bg-white border-2 border-emerald-400"></div>
                              <div className="flex items-center gap-2 mb-1">
                                <span className="w-2 h-2 rounded-full flex-shrink-0 bg-emerald-400"></span>
                                <h4 className="font-bold text-sm text-gray-900">
                                  After buying your {itemLabel}, you may also need
                                </h4>
                              </div>
                              <p className="text-xs text-gray-500 mb-3 leading-relaxed">
                                These accessories go perfectly with your {itemLabel}. Optional but highly recommended.
                              </p>
                              <div className="flex gap-4 overflow-x-auto pb-5 snap-x scrollbar-product">
                                {accessories.map((prod, j) => renderProductCard(prod, j))}
                              </div>
                            </div>
                          )}
                        </>
                      );
                    })() : (() => {

                      const seenProductIds = new Set();

                      const allTopPicks     = result.top_picks || [];
                      const allOthers       = result.all_products || [];
                      const combinedProducts = [...allTopPicks, ...allOthers];

                      const oosProducts    = combinedProducts.filter(p => p.stock_status === 'out_of_stock');
                      const inStockProducts = combinedProducts.filter(p => p.stock_status !== 'out_of_stock');

                      // ALWAYS show ALL phases. Use STRICT category match (no fuzzy word overlap).
                      const phasesToRender = result.purchase_timeline.map(phase => {
                        const phaseProducts = inStockProducts.filter(p => {
                          if (seenProductIds.has(p.id)) return false;
                          const matches = phase.categories.some(cat => {
                            const pCat     = (p.category || '').toLowerCase().replace(/_/g, ' ').trim();
                            const phaseCat = (cat || '').toLowerCase().replace(/_/g, ' ').trim();
                            if (!phaseCat) return false;
                            // Strict exact match only — prevents kitchen_appliances bleeding into kitchen_essentials
                            if (pCat === phaseCat) return true;
                            // Allow prefix match for subcategory namespacing (e.g. bags_luggage_travel → bags_luggage)
                            if (pCat.startsWith(phaseCat + ' ') || phaseCat.startsWith(pCat + ' ')) return true;
                            return false;
                          });
                          if (matches) { seenProductIds.add(p.id); return true; }
                          return false;
                        });
                        phaseProducts.sort((a, b) => {
                          const aTop = allTopPicks.some(t => t.id === a.id);
                          const bTop = allTopPicks.some(t => t.id === b.id);
                          if (aTop && !bTop) return -1;
                          if (!aTop && bTop) return  1;
                          return 0;
                        });
                        return { ...phase, displayProducts: phaseProducts };
                      });

                      // Filter to only phases that have products
                      let phasesToShow = phasesToRender.filter(ph => ph.displayProducts.length > 0);

                      // Step 2: Fallback Category Rows — ONLY for categories that are
                      // part of the original purchase_timeline. This prevents "bleed-through"
                      // of unrelated products from broad DB matches (e.g. showing
                      // study_accessories for a temple visit query).
                      const allowedFallbackCats = new Set(
                        result.purchase_timeline.flatMap(ph => ph.categories || [])
                      );
                      const unassignedProducts = inStockProducts.filter(p =>
                        !seenProductIds.has(p.id) && allowedFallbackCats.has(p.category)
                      );
                      const categoryGroups = {};
                      unassignedProducts.forEach(p => {
                        const cat = p.category || 'Other';
                        if (!categoryGroups[cat]) categoryGroups[cat] = [];
                        categoryGroups[cat].push(p);
                      });

                      Object.keys(categoryGroups).forEach(cat => {
                        const prodList = categoryGroups[cat];
                        prodList.sort((a, b) => {
                          const aTop = allTopPicks.some(t => t.id === a.id);
                          const bTop = allTopPicks.some(t => t.id === b.id);
                          if (aTop && !bTop) return -1;
                          if (!aTop && bTop) return 1;
                          return 0;
                        });
                        
                        phasesToShow.push({
                          phase_name: cat.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
                          note: `Additional items highly relevant to your context.`,
                          displayProducts: prodList,
                          priority: 'nice_to_have',
                          is_fallback_category: true,
                          categories: [cat]
                        });
                      });

                      // Extreme fallback if everything failed (e.g. no phases and no categories)
                      if (phasesToShow.length === 0) {
                        phasesToShow = [{
                          phase_name: 'Recommended Products',
                          note: 'Top selections for your upcoming event.',
                          displayProducts: inStockProducts.length > 0 ? inStockProducts : [result.top_recommendation].filter(Boolean),
                          priority: 'must_have',
                        }];
                      }

                      const priorityDot = {
                        must_have:    'bg-red-400',
                        should_have:  'bg-amber-400',
                        nice_to_have: 'bg-emerald-400',
                      };

                      const renderProductCard = (prod, j) => {
                        const isTopPick   = allTopPicks.some(t => t.id === prod.id);
                        const namePart    = (prod.name || '').split(' ').slice(0, 2).join('+');
                        const imgFallback = `https://picsum.photos/seed/${encodeURIComponent(namePart)}/400/400`;
                        const imgSrc      = prod.image_url
                          || (prod.image_placeholder ? `/images/${prod.image_placeholder}.jpg` : imgFallback);
                        return (
                          <div
                            key={prod.id || j}
                            className={`shrink-0 ${!isXRayOpen ? 'w-48' : 'w-36'} bg-white border ${
                              isTopPick ? 'border-[#F43397]/40 ring-1 ring-[#F43397]/20' : 'border-gray-100'
                            } rounded-2xl shadow-sm hover:shadow-md transition-shadow snap-center overflow-hidden cursor-pointer group`}
                            onClick={() => setSelectedProduct(prod)}
                          >
                            <div className="relative w-full aspect-square bg-gray-50 overflow-hidden">
                              <img
                                src={imgSrc}
                                onError={(e) => { e.target.onerror = null; e.target.src = imgFallback; }}
                                alt={prod.name}
                                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                              />
                              {isTopPick && (
                                <div className="absolute top-2 left-2 bg-[#F43397] text-white text-[9px] font-bold px-2 py-0.5 rounded-full shadow-sm">
                                  Top Pick
                                </div>
                              )}
                              <div className="absolute bottom-2 right-2 w-6 h-6 bg-white/80 backdrop-blur-sm rounded-full flex items-center justify-center shadow-sm">
                                <span className="text-[8px] font-bold text-[#F43397]">M</span>
                              </div>
                            </div>
                            <div className="p-3">
                              <p className={`font-medium text-gray-800 leading-tight ${!isXRayOpen ? 'text-sm line-clamp-2' : 'text-xs truncate'}`}>
                                {prod.name}
                              </p>
                              <div className="flex items-end gap-2 mt-2">
                                <span className="text-base font-bold text-gray-900">&#8377;{prod.price}</span>
                                <span className="text-xs text-gray-400 line-through mb-0.5">
                                  &#8377;{prod.price + Math.floor(prod.price * 0.4)}
                                </span>
                              </div>
                              <button className="w-full mt-3 py-2 bg-pink-50 text-[#F43397] rounded-xl text-xs font-bold hover:bg-[#F43397] hover:text-white transition-colors">
                                View Product
                              </button>
                            </div>
                          </div>
                        );
                      };

                      return (
                        <>
                          {phasesToShow.map((phase, i) => (
                            <div key={i} className="relative pl-5 border-l-2 border-gray-200 ml-2">
                              <div className="absolute -left-[9px] top-0.5 w-4 h-4 rounded-full bg-white border-2 border-[#F43397]"></div>
                              <div className="flex items-center gap-2 mb-1">
                                <span className={`w-2 h-2 rounded-full flex-shrink-0 ${priorityDot[phase.priority] || 'bg-gray-300'}`}></span>
                                <h4 className="font-bold text-sm text-gray-900">{phase.phase_name}</h4>
                              </div>
                              <p className="text-xs text-gray-500 mb-3 leading-relaxed">{phase.note}</p>
                              {phase.displayProducts?.length > 0 ? (
                                <div className="flex gap-4 overflow-x-auto pb-5 snap-x scrollbar-product">
                                  {phase.displayProducts.map((prod, j) => renderProductCard(prod, j))}
                                </div>
                              ) : (
                                <div className="flex items-center gap-3 bg-gray-50 border border-dashed border-gray-200 rounded-xl px-4 py-3 mb-5">
                                  <span className="text-xl">&#x1F6CD;</span>
                                  <div>
                                    <p className="text-xs font-semibold text-gray-600">Products being curated for this phase</p>
                                    <p className="text-xs text-gray-400">
                                      Categories: {(phase.categories || []).map(c => (c || '').replace(/_/g, ' ')).join(', ')}
                                    </p>
                                  </div>
                                </div>
                              )}
                            </div>
                          ))}

                          {oosProducts.length > 0 && (
                            <div className="relative pl-5 border-l-2 border-amber-200 ml-2 mt-2">
                              <div className="absolute -left-[9px] top-0.5 w-4 h-4 rounded-full bg-white border-2 border-amber-400"></div>
                              <h4 className="font-bold text-sm text-amber-700 mb-1">&#9888; Currently Unavailable on Meesho</h4>
                              <p className="text-xs text-gray-500 mb-3 leading-relaxed">
                                These items aren&apos;t available right now. Set an alert and we&apos;ll notify you!
                              </p>
                              <div className="flex gap-4 overflow-x-auto pb-5 snap-x scrollbar-product">
                                {oosProducts.map((prod, j) => (
                                  <div
                                    key={j}
                                    className={`shrink-0 ${!isXRayOpen ? 'w-48' : 'w-36'} bg-white border border-amber-100 rounded-2xl shadow-sm snap-center overflow-hidden`}
                                  >
                                    <div className="relative w-full aspect-square bg-amber-50 overflow-hidden flex items-center justify-center">
                                      <span className="text-3xl">&#x1F4E6;</span>
                                      <div className="absolute top-2 left-2 bg-amber-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full shadow-sm">
                                        Out of Stock
                                      </div>
                                    </div>
                                    <div className="p-3">
                                      <p className={`font-medium text-gray-700 leading-tight ${!isXRayOpen ? 'text-sm line-clamp-2' : 'text-xs truncate'}`}>
                                        {prod.name}
                                      </p>
                                      <p className="text-xs text-amber-600 font-semibold mt-2">Not available currently</p>
                                      <button
                                        onClick={(e) => { e.stopPropagation(); showToast(`Alert set for ${prod.name}`); }}
                                        className="w-full mt-3 py-2 bg-amber-50 text-amber-600 rounded-xl text-xs font-bold hover:bg-amber-500 hover:text-white transition-colors border border-amber-200"
                                      >
                                        &#x1F514; Notify Me
                                      </button>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </>
                      );
                    })()}
                  </div>
                </div>
                
                <div className="p-4 bg-white border-t border-gray-100 text-center shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] z-10">
                   <button onClick={() => setResult(null)} className="text-sm font-bold text-[#F43397] py-2 px-6 rounded-full hover:bg-pink-50 transition-colors">Start Over</button>
                </div>
              </div>
            )}
            
            {/* Toast Notification for App Shell */}
            <AnimatePresence>
              {toast && (
                <motion.div
                  initial={{ opacity: 0, y: 50 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 50 }}
                  className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-gray-900 text-white px-5 py-3 rounded-full shadow-2xl flex items-center gap-2 z-50 text-sm font-medium whitespace-nowrap"
                >
                  <Check className="w-4 h-4 text-emerald-400" />
                  {toast}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* RIGHT: X-RAY DASHBOARD */}
        <AnimatePresence>
          {isXRayOpen && (
            <motion.div 
              ref={brainRef}
              initial={{ opacity: 0, scale: 0.95, height: 0 }}
              animate={{ opacity: 1, scale: 1, height: 'auto', width: '100%', maxWidth: '800px' }}
              exit={{ opacity: 0, scale: 0.95, height: 0 }}
              className="w-full h-[85vh] lg:h-full bg-[#0f0a1e] rounded-3xl shadow-2xl border border-white/10 overflow-hidden flex flex-col relative shrink-0"
            >
              {/* Background Glow */}
              <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(circle at 50% 0%, rgba(108,43,217,0.15) 0%, transparent 60%)' }} />

              <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between bg-white/5 backdrop-blur-xl relative z-10">
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <Activity className="w-5 h-5 text-prism-400" />
                  PRISM Brain X-Ray
                </h2>
                <div className="flex items-center gap-3">
                  <span className="text-xs font-semibold px-2.5 py-1 bg-prism-500/20 text-prism-300 rounded-lg border border-prism-500/30 hidden sm:inline-block">Developer Mode</span>
                  <button onClick={() => setIsXRayOpen(false)} className="p-1.5 text-gray-400 hover:text-white bg-white/5 hover:bg-white/10 rounded-full transition-all flex items-center justify-center group" title="Close X-Ray">
                    <X className="w-5 h-5 group-hover:rotate-90 transition-transform duration-300" />
                  </button>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-6 space-y-6 relative z-10 scrollbar-hide">
                {!result && !isPending && (
                  <div className="h-full flex flex-col items-center justify-center text-gray-500">
                    <Brain className="w-16 h-16 opacity-20 mb-4 text-prism-400" />
                    <p className="text-sm">Awaiting query to reveal internal agent debate.</p>
                  </div>
                )}
                
                {isPending && (
                   <div className="flex flex-col items-center justify-center h-full">
                      <LoadingOrchestrator />
                   </div>
                )}

                {result && !isPending && (
                  <>
                    <div className="flex flex-col gap-6">
                      {/* Debate chamber takes full width above so cards have room */}
                      <AgentDebateChamber agents={result.agent_debate} />
                      
                      {/* Genome and Bharat context split half/half */}
                      {result.top_recommendation?.id !== 'NONE' && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <ConfidenceGenome confidence={result.confidence} />
                          <BharatContextBadge 
                            context={result.bharat_context} 
                            stateDetected={result.state_detected} 
                            institutionDetected={result.institution_detected}
                            detectedIntent={result.detected_intent}
                          />
                        </div>
                      )}
                    </div>

                    {/* API Response Block */}
                    <div className="mt-8 bg-black/60 rounded-xl border border-white/10 overflow-hidden backdrop-blur-md shadow-lg">
                      <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between bg-white/5">
                        <div className="flex items-center gap-2">
                           <Code className="w-4 h-4 text-prism-400" />
                           <span className="text-xs text-gray-300 font-mono font-medium">Raw API Response (Key Insights)</span>
                        </div>
                        <span className="text-[10px] font-mono text-gray-500 px-2 py-0.5 bg-white/10 rounded">POST /api/prism/analyze</span>
                      </div>
                      <div className="p-5 max-h-[350px] overflow-y-auto scrollbar-hide">
                        <pre className="text-[11px] sm:text-xs font-mono text-emerald-400/90 leading-relaxed whitespace-pre-wrap">
                          {JSON.stringify({
                             session_id: result.session_id,
                             detected_event: result.detected_event,
                             emotion_level: result.emotion_level,
                             top_recommendation: {
                               id: result.top_recommendation?.id,
                               name: result.top_recommendation?.name,
                               price: result.top_recommendation?.price,
                             },
                             confidence_score: result.confidence?.total_score,
                             temporal_strategies: result.temporal_strategies?.map(s => s.strategy_name)
                          }, null, 2)}
                        </pre>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* JUDGE MODE MODAL — 3-Tab Guide */}
      <AnimatePresence>
        {showJudgeMode && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" onClick={() => setShowJudgeMode(false)}>
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              onClick={e => e.stopPropagation()}
              className="w-full max-w-2xl bg-white rounded-2xl shadow-2xl overflow-hidden border border-gray-100 max-h-[90vh] flex flex-col"
            >
              {/* Header */}
              <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-gradient-to-r from-[#F43397]/10 to-purple-50 shrink-0">
                <h2 className="text-lg font-black text-gray-900 flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-[#F43397]" /> PRISM Judge Guide
                </h2>
                <button onClick={() => setShowJudgeMode(false)} className="text-gray-400 hover:text-gray-900 font-bold text-xl transition-colors">&times;</button>
              </div>

              {/* Tab bar */}
              <div className="flex border-b border-gray-100 shrink-0 bg-gray-50">
                {[
                  { key: 'howto', icon: <FlaskConical className="w-3.5 h-3.5" />, label: 'How to Test' },
                  { key: 'scope', icon: <AlertCircle className="w-3.5 h-3.5" />, label: 'Scope & Constraints' },
                  { key: 'vision', icon: <Rocket className="w-3.5 h-3.5" />, label: 'Production Vision' },
                ].map(tab => (
                  <button
                    key={tab.key}
                    onClick={() => setJudgeTab(tab.key)}
                    className={`flex-1 flex items-center justify-center gap-1.5 py-3 text-xs font-bold transition-all border-b-2 ${
                      judgeTab === tab.key
                        ? 'border-[#F43397] text-[#F43397] bg-white'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    {tab.icon} {tab.label}
                  </button>
                ))}
              </div>

              {/* Tab content */}
              <div className="flex-1 overflow-y-auto p-6">

                {/* ── Tab 1: How to Test ──────────────────────────────── */}
                {judgeTab === 'howto' && (
                  <div className="space-y-4">
                    <p className="text-sm text-gray-600 leading-relaxed">
                      PRISM understands <strong>natural language life events</strong> — no keywords needed. Just speak naturally, like you'd tell a friend. Here's how to evaluate it:
                    </p>

                    <div className="space-y-2">
                      <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-1">Step-by-step evaluation</p>
                      {[
                        { step: '1', text: 'Type a life-event query (or use the pre-loaded scenarios)', detail: 'Click any scenario chip to auto-fill and run instantly' },
                        { step: '2', text: 'Watch the 3-phase purchase timeline generate', detail: 'Phases are dynamically built by the LLM, not hardcoded' },
                        { step: '3', text: 'Toggle the 🧠 Brain X-Ray button (top right)', detail: 'See the 4 named agents debating internally in real-time' },
                        { step: '4', text: 'Click any product card to see PRISM Smart Timing', detail: 'Buy Now / Wait / Split strategies with real pricing' },
                        { step: '5', text: 'Run a second query — watch PRISM remember you', detail: 'The 🧠 memory chip will appear showing your profile' },
                      ].map(item => (
                        <div key={item.step} className="flex gap-3 p-3 bg-gray-50 rounded-xl border border-gray-100">
                          <div className="w-6 h-6 rounded-full bg-[#F43397] text-white text-xs font-black flex items-center justify-center shrink-0 mt-0.5">{item.step}</div>
                          <div>
                            <p className="text-sm font-semibold text-gray-800">{item.text}</p>
                            <p className="text-xs text-gray-500 mt-0.5">{item.detail}</p>
                          </div>
                        </div>
                      ))}
                    </div>

                    <div>
                      <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">📋 Copy-paste test queries</p>
                      <div className="space-y-2">
                        {[
                          { q: 'My daughter got into NIT Trichy starting August.', tag: 'Hostel Move + Institution constraints' },
                          { q: 'Going trekking to Kashmir next month. Need gear.', tag: 'Travel + Cultural + Climate context' },
                          { q: 'Starting my first corporate job in Bangalore next week at Infosys.', tag: 'First Job + Memory Mining' },
                          { q: 'My daughter\'s wedding is next month in Jaipur.', tag: 'Wedding + Rajasthan cultural context' },
                          { q: 'I want to buy a car.', tag: 'Graceful rejection (non-retail)' },
                        ].map((item, i) => (
                          <div key={i} className="flex items-start gap-2 p-3 bg-white border border-gray-200 rounded-xl group hover:border-[#F43397]/40 transition-all">
                            <div className="flex-1 min-w-0">
                              <p className="text-xs font-semibold text-gray-800 leading-relaxed">"{item.q}"</p>
                              <span className="text-[10px] text-purple-600 font-bold bg-purple-50 px-1.5 py-0.5 rounded-full mt-1 inline-block">{item.tag}</span>
                            </div>
                            <button
                              onClick={() => { navigator.clipboard.writeText(item.q); setCopiedQuery(i); setTimeout(() => setCopiedQuery(null), 2000) }}
                              className="shrink-0 p-1.5 rounded-lg text-gray-400 hover:text-[#F43397] hover:bg-pink-50 transition-all"
                              title="Copy query"
                            >
                              {copiedQuery === i ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* ── Tab 2: Scope & Constraints ──────────────────────── */}
                {judgeTab === 'scope' && (
                  <div className="space-y-5">
                    <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl flex gap-3">
                      <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                      <div>
                        <p className="text-sm font-bold text-amber-800 mb-1">Limited Demo Dataset</p>
                        <p className="text-xs text-amber-700 leading-relaxed">
                          This demo uses a curated mock product catalog (~80 products) to simulate Meesho's catalog. Some queries may show placeholder images or "Out of Stock" cards — this is expected and demonstrates PRISM's product gap detection, not a bug.
                        </p>
                      </div>
                    </div>

                    <div>
                      <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">✅ Covered Product Categories</p>
                      <div className="flex flex-wrap gap-1.5">
                        {['Bedding', 'Formal Wear', 'Bags & Luggage', 'Study Accessories', 'Kitchen Essentials', 'Personal Care', 'Festival Decor', 'Baby Products', 'Electronics', 'Home Decor', 'Wedding Apparel', 'Stationery', 'Security', 'Home Improvement'].map(cat => (
                          <span key={cat} className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-1 rounded-full">{cat}</span>
                        ))}
                      </div>
                    </div>

                    <div>
                      <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">🤖 The 4 PRISM Agents</p>
                      <div className="space-y-2">
                        {[
                          { name: 'Kismat', role: 'Trust Agent', desc: 'Evaluates seller ratings, return rates, and review credibility. Adds trust confidence to the score.', color: 'purple' },
                          { name: 'Paisa', role: 'Budget Agent', desc: 'Checks if the product fits the user\'s budget. Flags overpriced items, rewards good value.', color: 'emerald' },
                          { name: 'Samay', role: 'Time Agent', desc: 'Checks delivery feasibility vs. event date. Validates timing strategy.', color: 'blue' },
                          { name: 'Soch', role: 'Synthesis Agent (LLM)', desc: 'Weighs all 3 agents\' verdicts with cultural + Bharat context to produce the final recommendation.', color: 'pink' },
                        ].map(agent => (
                          <div key={agent.name} className="flex gap-3 p-3 bg-gray-50 rounded-xl border border-gray-100">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-xs font-black ${
                              agent.color === 'purple' ? 'bg-purple-100 text-purple-700' :
                              agent.color === 'emerald' ? 'bg-emerald-100 text-emerald-700' :
                              agent.color === 'blue' ? 'bg-blue-100 text-blue-700' :
                              'bg-pink-100 text-pink-700'
                            }`}>{agent.name[0]}</div>
                            <div>
                              <p className="text-xs font-bold text-gray-800">{agent.name} <span className="text-gray-500 font-normal">— {agent.role}</span></p>
                              <p className="text-[11px] text-gray-600 mt-0.5 leading-relaxed">{agent.desc}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="p-3 bg-gray-50 border border-gray-200 rounded-xl">
                      <p className="text-xs font-bold text-gray-700 mb-1">💡 For best demo results, give context like:</p>
                      <ul className="text-xs text-gray-600 space-y-1 list-disc pl-4">
                        <li>Mention a city or institution name (NIT, IIT, Bangalore, Kashmir…)</li>
                        <li>Include an event (wedding, hostel move, first job, Diwali…)</li>
                        <li>Optionally set a budget and date in the input fields</li>
                      </ul>
                    </div>
                  </div>
                )}

                {/* ── Tab 3: Production Vision ────────────────────────── */}
                {judgeTab === 'vision' && (
                  <div className="space-y-5">
                    <div className="p-4 bg-gradient-to-br from-[#F43397]/10 to-purple-50 border border-pink-200 rounded-xl">
                      <p className="text-sm font-bold text-gray-900 mb-1 flex items-center gap-2">
                        <Rocket className="w-4 h-4 text-[#F43397]" /> What PRISM becomes with real Meesho data
                      </p>
                      <p className="text-xs text-gray-600 leading-relaxed">
                        Every component of PRISM is production-ready and API-first. The moment it connects to Meesho's live catalog, it transforms from a powerful demo into India's most intelligent shopping brain.
                      </p>
                    </div>

                    <div className="space-y-3">
                      {[
                        { icon: '🛒', title: 'Live Inventory Intelligence', desc: 'Real-time product availability, actual pricing, and live seller ratings from Meesho\'s 15M+ product catalog. PRISM\'s confidence scores become genuinely actionable.' },
                        { icon: '🧠', title: 'Deep Personalisation at Scale', desc: 'The Memory Mining system (active in this demo) scales to millions of users. PRISM learns purchase patterns, owned categories, and life stage — becoming smarter with every interaction.' },
                        { icon: '🌍', title: 'Hyperlocal Bharat Intelligence', desc: 'Pincode-level delivery routing, regional language queries (Hindi, Tamil, Telugu), and festival calendars for every state — making PRISM the first truly Bharat-first commerce brain.' },
                        { icon: '📱', title: 'WhatsApp & Voice Integration', desc: 'PRISM\'s API-first design plugs directly into WhatsApp Business — India\'s primary communication channel for tier-2/3 users — enabling voice-first shopping assistance.' },
                        { icon: '⚡', title: 'Predictive Pre-Purchase', desc: 'With historical data, PRISM predicts purchase intent days before users search. Proactive notifications: "Your son\'s semester starts in 3 weeks — shall we prepare his hostel list?"' },
                        { icon: '🤝', title: 'Seller Empowerment', desc: 'PRISM\'s demand signals feed back to Meesho sellers — telling them which products will spike demand for upcoming life events in their region. Supply meets demand before it happens.' },
                      ].map((item, i) => (
                        <div key={i} className="flex gap-3 p-3.5 bg-white border border-gray-100 rounded-xl shadow-sm hover:border-pink-200 transition-all">
                          <span className="text-xl shrink-0">{item.icon}</span>
                          <div>
                            <p className="text-sm font-bold text-gray-900 mb-0.5">{item.title}</p>
                            <p className="text-xs text-gray-600 leading-relaxed">{item.desc}</p>
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="p-4 bg-gray-900 rounded-xl text-center">
                      <p className="text-sm font-black text-white mb-1">Built for India's next 500 million users</p>
                      <p className="text-xs text-gray-400">PRISM doesn't just predict what people buy — it understands <em>why</em> they buy, <em>when</em> they need it, and <em>what they'll need next</em>.</p>
                    </div>
                  </div>
                )}

              </div>

              {/* Footer */}
              <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-between bg-gray-50 shrink-0">
                <span className="text-xs text-gray-400 font-medium">PRISM v1.0 · ScriptedBy&#123;Her&#125; 2.0</span>
                <a href="https://github.com/Swaathi1409/PRISM-Predictive_Reality_Intelligence_for_Smarter_Meesho" target="_blank" rel="noreferrer" className="text-xs font-bold text-white bg-gray-900 hover:bg-black px-4 py-2 rounded-full shadow-sm transition-all active:scale-95 flex items-center gap-1.5">
                  <ChevronRight className="w-3.5 h-3.5" /> View GitHub
                </a>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      
      {/* PRODUCT DETAILS MODAL FOR DEMO */}
      <AnimatePresence>
        {selectedProduct && (
          <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 sm:p-6 bg-black/60 backdrop-blur-sm" onClick={() => setSelectedProduct(null)}>
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              onClick={e => e.stopPropagation()}
              className="w-full max-w-sm sm:max-w-md bg-white rounded-[24px] shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
            >
              {/* Product Image Header */}
              <div className="relative w-full h-48 sm:h-56 bg-gray-50 shrink-0">
                <img 
                  src={selectedProduct.image_url || (selectedProduct.image_placeholder ? `/images/${selectedProduct.image_placeholder}.jpg` : `https://picsum.photos/seed/${encodeURIComponent(selectedProduct.id || selectedProduct.name)}/400/400`)}
                  onError={(e) => {
                    e.target.onerror = null; 
                    e.target.src = `https://picsum.photos/seed/${encodeURIComponent(selectedProduct.id || selectedProduct.name)}/400/400`;
                  }}
                  alt={selectedProduct.name} 
                  className="w-full h-full object-cover"
                />
                <button 
                  onClick={() => setSelectedProduct(null)} 
                  className="absolute top-4 right-4 w-8 h-8 bg-black/40 hover:bg-black/60 text-white rounded-full flex items-center justify-center backdrop-blur-md transition-colors"
                >
                  &times;
                </button>
              </div>

              {/* Product Info */}
              <div className="p-6 flex-1 overflow-y-auto">
                <div className="flex items-center gap-2 mb-2">
                  <span className={`px-2 py-1 text-[10px] font-bold rounded uppercase tracking-wide ${
                    selectedProduct.stock_status === 'in_stock' ? 'bg-green-100 text-green-700' : 
                    selectedProduct.stock_status === 'low_stock' ? 'bg-amber-100 text-amber-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {selectedProduct.stock_status === 'in_stock' ? 'In Stock' : 
                     selectedProduct.stock_status === 'low_stock' ? 'Low Stock' : 'Out of Stock'}
                  </span>
                  {selectedProduct.seller_rating > 0 && (
                    <span className="flex items-center text-xs text-yellow-600 font-bold bg-yellow-50 px-2 py-1 rounded">
                      ★ {selectedProduct.seller_rating}
                    </span>
                  )}
                  {selectedProduct.confidence_score > 0 && (
                    <span className="flex items-center text-[10px] text-prism-600 font-bold bg-prism-50 border border-prism-200 px-2 py-1 rounded uppercase tracking-wide">
                      PRISM Score {selectedProduct.confidence_score}/98
                    </span>
                  )}
                </div>
                
                <h2 className="text-xl font-bold text-gray-900 mb-2 leading-tight">{selectedProduct.name}</h2>
                
                {selectedProduct.price > 0 && (() => {
                  const d = ((selectedProduct.price % 40) + 20) / 100;
                  const mrp = Math.floor(selectedProduct.price / (1 - d));
                  const percentOff = Math.round(((mrp - selectedProduct.price) / mrp) * 100);
                  return (
                    <div className="flex items-end gap-3 mb-4">
                      <span className="text-3xl font-black text-gray-900">₹{selectedProduct.price}</span>
                      <span className="text-sm text-gray-400 line-through mb-1">₹{mrp}</span>
                      <span className="text-sm font-bold text-green-500 mb-1">{percentOff}% off</span>
                    </div>
                  )
                })()}

                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-bold text-gray-900 mb-1">Product Details</h3>
                    <p className="text-sm text-gray-600 leading-relaxed">
                      {selectedProduct.description || 'High quality product delivered directly from the best sellers on Meesho.'}
                    </p>
                  </div>

                  {selectedProduct.id !== 'NONE' && (
                    <div className="grid grid-cols-2 gap-3 pt-4 border-t border-gray-100">
                      <div>
                        <p className="text-xs text-gray-500">Sold By</p>
                        <p className="text-sm font-semibold text-gray-900 truncate">{selectedProduct.seller_name || 'Verified Seller'}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">Delivery</p>
                        <p className="text-sm font-semibold text-gray-900">~{selectedProduct.delivery_days || 4} Days</p>
                      </div>
                    </div>
                  )}
                  
                  {/* PRISM Temporal Intelligence */}
                  {selectedProduct.stock_status !== 'out_of_stock' && selectedProduct.id !== 'NONE' && (
                    <div className="p-4 bg-gray-50 border-t border-gray-100">
                      <h3 className="text-xs font-bold text-gray-900 mb-3 flex items-center gap-1.5 uppercase tracking-wider">
                        <Activity className="w-4 h-4 text-emerald-500" /> 
                        PRISM Smart Timing Strategy
                      </h3>
                      <div className="space-y-2">
                        {selectedProduct.temporal_strategies ? (
                          selectedProduct.temporal_strategies.map((ts, idx) => {
                            const isSelected = selectedTemporalStrategy 
                              ? selectedTemporalStrategy.strategy_key === ts.strategy_key
                              : false; // No auto-selection!

                            return (
                              <div 
                                key={idx} 
                                onClick={() => setSelectedTemporalStrategy(ts)}
                                className={`p-3 rounded-xl border cursor-pointer transition-all ${
                                  isSelected 
                                    ? 'border-emerald-500 bg-emerald-50 shadow-sm ring-1 ring-emerald-500' 
                                    : ts.recommended 
                                      ? 'border-emerald-200 bg-emerald-50/30 hover:border-emerald-300'
                                      : 'border-gray-200 bg-white hover:border-gray-300'
                                }`}
                              >
                                <div className="flex justify-between items-center mb-1">
                                  <span className={`text-xs font-bold ${isSelected ? 'text-emerald-700' : ts.recommended ? 'text-emerald-600' : 'text-gray-700'}`}>
                                    {ts.strategy_name} {ts.recommended && '✓ Recommended'}
                                  </span>
                                  {ts.price > 0 && <span className="text-xs font-bold text-gray-900">₹{ts.price}</span>}
                                </div>
                                <p className="text-[10px] text-gray-600 mb-1">{ts.action_date}</p>
                                <p className="text-[10px] text-gray-500 leading-snug">{ts.note}</p>
                              </div>
                            )
                          })
                        ) : (
                          <div className="p-3 rounded-xl border border-emerald-500 bg-emerald-50 shadow-sm">
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-xs font-bold text-emerald-700">Buy Now ✓ Recommended</span>
                              <span className="text-xs font-bold text-gray-900">₹{selectedProduct.price}</span>
                            </div>
                            <p className="text-[10px] text-gray-600 mb-1">Act Today</p>
                            <p className="text-[10px] text-gray-500 leading-snug">No rate difference expected. You can buy this immediately to secure delivery.</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Action Bar */}
              <div className="p-4 border-t border-gray-100 bg-white grid grid-cols-2 gap-3">
                {selectedProduct.id === 'NONE' ? (
                  <button onClick={handleNotifyMe} className="col-span-2 py-3.5 rounded-xl text-sm font-bold text-white bg-indigo-500 hover:bg-indigo-600 shadow-md transition-colors">
                    Notify Me
                  </button>
                ) : selectedProduct.stock_status === 'out_of_stock' ? (
                  <div className="col-span-2 flex flex-col gap-2">
                     <p className="text-xs text-center text-amber-600 font-medium">This item is currently out of stock. We will notify you once it's available.</p>
                     <button onClick={handleNotifyMe} className="w-full py-3.5 rounded-xl text-sm font-bold text-white bg-amber-500 hover:bg-amber-600 shadow-md transition-colors">
                       Notify Me When Restocked
                     </button>
                  </div>
                ) : (
                  <>
                    <button 
                      onClick={handleAddToCart} 
                      className="py-3.5 rounded-xl text-sm font-bold text-[#F43397] border border-[#F43397] bg-pink-50 hover:bg-pink-100 transition-colors"
                    >
                      Add to Cart
                    </button>
                    <button 
                      onClick={() => {
                        if (selectedTemporalStrategy?.strategy_key === 'wait') {
                          handleNotifyMe();
                          setSelectedProduct(null);
                        } else {
                          handleBuyNow();
                        }
                      }} 
                      className={`py-3.5 rounded-xl text-sm font-bold text-white shadow-md transition-colors ${
                        selectedTemporalStrategy?.strategy_key === 'wait' 
                          ? 'bg-emerald-500 hover:bg-emerald-600' 
                          : selectedTemporalStrategy?.strategy_key === 'split'
                            ? 'bg-purple-500 hover:bg-purple-600'
                            : 'bg-[#F43397] hover:bg-[#e02b88]'
                      }`}
                    >
                      {selectedTemporalStrategy?.strategy_key === 'wait' 
                        ? 'Set Reminder' 
                        : selectedTemporalStrategy?.strategy_key === 'split'
                          ? 'Pay Deposit'
                          : 'Buy Now'}
                    </button>
                  </>
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Cart Modal Overlay */}
      <AnimatePresence>
        {isCartOpen && (
          <div className="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-blur-sm overflow-hidden">
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="w-full max-w-sm h-full bg-white shadow-2xl flex flex-col relative"
            >
              <div className="p-4 border-b border-gray-100 flex items-center justify-between bg-white">
                <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                  <ShoppingCart className="w-5 h-5 text-[#F43397]" /> 
                  Your Cart {cartItems.length > 0 && `(${cartItems.length})`}
                </h2>
                <button onClick={() => setIsCartOpen(false)} className="p-2 bg-gray-50 hover:bg-gray-100 rounded-full transition-colors">
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
                {cartItems.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-gray-400">
                    <ShoppingCart className="w-16 h-16 mb-4 opacity-20" />
                    <p className="font-medium text-sm">Your cart is empty.</p>
                  </div>
                ) : (
                  cartItems.map((item, idx) => (
                    <motion.div key={idx} layout initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex gap-4 p-3 bg-white rounded-2xl border border-gray-100 shadow-sm relative group">
                      <div className="w-20 h-20 bg-gray-50 rounded-xl overflow-hidden shrink-0 border border-gray-100">
                        <img
                          src={item.image_url || (item.image_placeholder ? `/images/${item.image_placeholder}.jpg` : `https://picsum.photos/seed/${encodeURIComponent(item.id || item.name)}/400/400`)}
                          onError={(e) => {
                            e.target.onerror = null;
                            e.target.src = `https://picsum.photos/seed/${encodeURIComponent(item.id || item.name)}/400/400`;
                          }}
                          alt={item.name}
                          className="w-full h-full object-cover"
                        />
                      </div>
                      <div className="flex-1 flex flex-col justify-center pr-6">
                        <p className="text-sm font-semibold text-gray-800 line-clamp-2 leading-tight mb-1">{item.name}</p>
                        <p className="text-sm font-bold text-gray-900">₹{item.price}</p>
                      </div>
                      <button onClick={() => removeFromCart(idx)} className="absolute right-3 top-1/2 -translate-y-1/2 p-2 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </motion.div>
                  ))
                )}
              </div>

              {cartItems.length > 0 && (
                <div className="p-5 bg-white border-t border-gray-100 shadow-[0_-10px_20px_-10px_rgba(0,0,0,0.05)]">
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-sm font-medium text-gray-600">Total Price</span>
                    <span className="text-xl font-bold text-gray-900">₹{cartItems.reduce((acc, curr) => acc + curr.price, 0)}</span>
                  </div>
                  <button onClick={handleBuyNow} className="w-full py-4 rounded-xl text-sm font-bold text-white bg-[#F43397] hover:bg-[#e02b88] shadow-md transition-transform active:scale-95 flex items-center justify-center gap-2">
                    <ShieldCheck className="w-5 h-5" /> Proceed to Checkout
                  </button>
                </div>
              )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Checkout Processing/Success Modal */}
      <AnimatePresence>
        {checkoutState !== 'idle' && (
          <div className="absolute inset-0 z-[60] flex items-center justify-center bg-black/60 backdrop-blur-md p-6">
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              className="w-full max-w-sm bg-white rounded-3xl p-8 shadow-2xl flex flex-col items-center text-center relative overflow-hidden"
            >
              {checkoutState === 'processing' ? (
                <>
                  <div className="w-20 h-20 rounded-full bg-blue-50 text-blue-500 flex items-center justify-center mb-6 shadow-inner">
                    <CreditCard className="w-10 h-10 animate-pulse" />
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Processing Payment</h3>
                  <p className="text-sm text-gray-500 mb-8">Securely contacting your bank...</p>
                  <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
                </>
              ) : (
                <>
                  <div className="absolute -top-10 -left-10 w-40 h-40 bg-emerald-400 rounded-full mix-blend-multiply filter blur-2xl opacity-20 animate-pulse"></div>
                  <div className="absolute -bottom-10 -right-10 w-40 h-40 bg-teal-400 rounded-full mix-blend-multiply filter blur-2xl opacity-20 animate-pulse"></div>
                  <div className="w-24 h-24 rounded-full bg-emerald-100 text-emerald-500 flex items-center justify-center mb-6 shadow-[0_0_40px_rgba(16,185,129,0.2)]">
                    <CheckCircle className="w-12 h-12" />
                  </div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">Order Confirmed!</h3>
                  <p className="text-sm text-gray-500 mb-6">Your payment was successful. We've started processing your order.</p>
                  <div className="w-full bg-gray-50 rounded-xl p-4 text-left border border-gray-100">
                    <div className="flex justify-between items-center text-xs mb-2">
                      <span className="text-gray-500 font-medium">Order ID</span>
                      <span className="text-gray-900 font-bold">#MSH-{orderId}</span>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-gray-500 font-medium">Expected Delivery</span>
                      <span className="text-gray-900 font-bold">Within 4-5 Days</span>
                    </div>
                  </div>
                </>
              )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Global Toast UI */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: 50, x: '-50%' }}
            animate={{ opacity: 1, y: 0, x: '-50%' }}
            exit={{ opacity: 0, y: 50, x: '-50%' }}
            className="fixed bottom-6 left-1/2 z-[70] bg-gray-900 text-white px-6 py-3 rounded-full shadow-2xl flex items-center gap-2 text-sm font-medium"
          >
            <CheckCircle className="w-4 h-4 text-green-400" />
            {toast}
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  )
}
