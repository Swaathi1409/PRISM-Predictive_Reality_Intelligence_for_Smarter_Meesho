import { useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, Mic, Activity, CheckCircle, Code, Brain, Send, MicOff, Calendar, ShoppingCart, Check, X, Trash2, CreditCard, ShieldCheck, Loader2 } from 'lucide-react'
import { usePrismAnalysis } from '../hooks/usePrismAnalysis'
import LoadingOrchestrator from '../components/LoadingOrchestrator'
import AgentDebateChamber from '../components/AgentDebateChamber'
import ConfidenceGenome from '../components/ConfidenceGenome'
import BharatContextBadge from '../components/BharatContextBadge'

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
  const [result, setResult] = useState(null)
  const [selectedProduct, setSelectedProduct] = useState(null)
  const [isListening, setIsListening] = useState(false)
  const [cartItems, setCartItems] = useState([])
  const [isCartOpen, setIsCartOpen] = useState(false)
  const [checkoutState, setCheckoutState] = useState('idle') // 'idle' | 'processing' | 'success'
  const [toast, setToast] = useState(null)
  const [orderId, setOrderId] = useState(null)
  const brainRef = useRef(null)

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
    
    analyze(payload, {
      onSuccess: (data) => {
        setResult(data)
        setIsXRayOpen(true) // auto-reveal the AI brain on first result so judges see the agent debate
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
                  <h3 className="font-bold text-gray-900 flex items-center gap-2 text-lg">
                    <CheckCircle className="w-5 h-5 text-emerald-500" />
                    Your Purchase Plan
                  </h3>
                  
                  <div className="space-y-6">
                    {(() => {
                      const seenProductIds = new Set();
                      const oosProducts = result.all_products?.filter(p => p.stock_status === 'out_of_stock') || [];
                      const inStockProducts = result.all_products?.filter(p => p.stock_status !== 'out_of_stock') || [];

                      // ── Original phased timeline — exactly as before ──────────
                      let phasesToRender = result.purchase_timeline.map(phase => {
                         const phaseProducts = inStockProducts.filter(p => {
                            if (seenProductIds.has(p.id)) return false;
                            const matches = phase.categories.some(cat => p.category?.toLowerCase().includes(cat.toLowerCase()));
                            if (matches) {
                               seenProductIds.add(p.id);
                               return true;
                            }
                            return false;
                         }) || [];
                         return { ...phase, displayProducts: phaseProducts };
                      }).filter(phase => phase.displayProducts.length > 0 || phase.phase_name === "Waiting for Inventory");

                      const phasesToShow = phasesToRender.length > 0 ? phasesToRender : [{
                         phase_name: "Recommended Products",
                         note: "Top selections for your upcoming event.",
                         displayProducts: inStockProducts.length > 0 ? inStockProducts : [result.top_recommendation].filter(Boolean)
                      }];

                      const renderProductCard = (prod, j) => (
                        <div key={j} className={`shrink-0 ${!isXRayOpen ? 'w-48' : 'w-36'} bg-white border border-gray-100 rounded-2xl shadow-sm hover:shadow-md transition-shadow snap-center overflow-hidden cursor-pointer group`} onClick={() => setSelectedProduct(prod)}>
                           <div className="relative w-full aspect-square bg-gray-50 overflow-hidden">
                              <img
                                src={prod.image_placeholder ? `/images/${prod.image_placeholder}.jpg` : `https://ui-avatars.com/api/?name=${encodeURIComponent(prod.name.split(' ').slice(0,2).join('+'))}&background=random&color=fff&size=256&font-size=0.33`}
                                onError={(e) => { e.target.onerror = null; e.target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(prod.name.split(' ').slice(0,2).join('+'))}&background=random&color=fff&size=256&font-size=0.33`; }}
                                alt={prod.name}
                                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                              />
                              <div className="absolute bottom-2 right-2 w-6 h-6 bg-white/80 backdrop-blur-sm rounded-full flex items-center justify-center shadow-sm">
                                <span className="text-[8px] font-bold text-[#F43397]">M</span>
                              </div>
                           </div>
                           <div className="p-3">
                             <p className={`font-medium text-gray-800 leading-tight ${!isXRayOpen ? 'text-sm line-clamp-2' : 'text-xs truncate'}`}>{prod.name}</p>
                             <div className="flex items-end gap-2 mt-2">
                               <span className="text-base font-bold text-gray-900">₹{prod.price}</span>
                               <span className="text-xs text-gray-400 line-through mb-0.5">₹{prod.price + Math.floor(prod.price * 0.4)}</span>
                             </div>
                             <button className="w-full mt-3 py-2 bg-pink-50 text-[#F43397] rounded-xl text-xs font-bold hover:bg-[#F43397] hover:text-white transition-colors">
                               View Product
                             </button>
                           </div>
                        </div>
                      );

                      return (
                        <>
                          {/* Original phase timeline — untouched */}
                          {phasesToShow.map((phase, i) => (
                            <div key={i} className="relative pl-5 border-l-2 border-gray-200 ml-2">
                              <div className="absolute -left-[9px] top-0.5 w-4 h-4 rounded-full bg-white border-2 border-[#F43397]"></div>
                              <h4 className="font-bold text-sm text-gray-900 mb-1">{phase.phase_name}</h4>
                              <p className="text-xs text-gray-500 mb-3 leading-relaxed">{phase.note}</p>
                              <div className={`flex gap-4 overflow-x-auto pb-5 snap-x scrollbar-product`}>
                                {phase.displayProducts?.map((prod, j) => renderProductCard(prod, j))}
                              </div>
                            </div>
                          ))}

                          {/* OOS section — only if unavailable items exist, shown at the very bottom */}
                          {oosProducts.length > 0 && (
                            <div className="relative pl-5 border-l-2 border-amber-200 ml-2 mt-2">
                              <div className="absolute -left-[9px] top-0.5 w-4 h-4 rounded-full bg-white border-2 border-amber-400"></div>
                              <h4 className="font-bold text-sm text-amber-700 mb-1">⚠ Currently Unavailable on Meesho</h4>
                              <p className="text-xs text-gray-500 mb-3 leading-relaxed">These specific items you may need aren't available right now. Set an alert and we'll notify you!</p>
                              <div className={`flex gap-4 overflow-x-auto pb-5 snap-x scrollbar-product`}>
                                {oosProducts.map((prod, j) => (
                                  <div key={j} className={`shrink-0 ${!isXRayOpen ? 'w-48' : 'w-36'} bg-white border border-amber-100 rounded-2xl shadow-sm snap-center overflow-hidden`}>
                                     <div className="relative w-full aspect-square bg-amber-50 overflow-hidden flex items-center justify-center">
                                        <span className="text-3xl">📦</span>
                                        <div className="absolute top-2 left-2 bg-amber-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full shadow-sm">
                                            Out of Stock
                                        </div>
                                     </div>
                                     <div className="p-3">
                                       <p className={`font-medium text-gray-700 leading-tight ${!isXRayOpen ? 'text-sm line-clamp-2' : 'text-xs truncate'}`}>{prod.name}</p>
                                       <p className="text-xs text-amber-600 font-semibold mt-2">Not available currently</p>
                                       <button 
                                         onClick={(e) => { e.stopPropagation(); showToast(`Alert set for ${prod.name}`); }}
                                         className="w-full mt-3 py-2 bg-amber-50 text-amber-600 rounded-xl text-xs font-bold hover:bg-amber-500 hover:text-white transition-colors border border-amber-200">
                                         🔔 Notify Me
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

      {/* JUDGE MODE MODAL */}
      <AnimatePresence>
        {showJudgeMode && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              className="w-full max-w-2xl bg-white rounded-2xl shadow-2xl overflow-hidden border border-gray-100"
            >
              <div className="px-6 py-5 border-b border-gray-100 flex items-center justify-between bg-gray-50">
                <h2 className="text-xl font-black text-gray-900 flex items-center gap-2 font-display">
                  <Sparkles className="w-5 h-5 text-prism-600" /> Hackathon Evaluation Map
                </h2>
                <button onClick={() => setShowJudgeMode(false)} className="text-gray-400 hover:text-gray-900 font-bold text-2xl transition-colors">&times;</button>
              </div>
              <div className="p-6 space-y-5">
                <p className="text-sm font-medium text-gray-600 mb-2">How PRISM fulfills the grading rubrics:</p>
                <div className="space-y-4">
                  <div className="p-4 rounded-xl border border-gray-100 bg-white shadow-sm flex gap-4 items-start">
                    <div className="w-8 h-8 rounded-full bg-prism-100 flex items-center justify-center shrink-0 mt-0.5">
                       <span className="font-bold text-prism-600 text-xs">1</span>
                    </div>
                    <div>
                       <span className="font-bold text-gray-900 text-sm block mb-1">Innovation</span> 
                       <p className="text-sm text-gray-600 leading-relaxed">First Commerce Brain for Bharat. Dynamic life-event detection instead of keyword search. (Toggle the X-Ray view to see the 4 named agents debating internally).</p>
                    </div>
                  </div>
                  <div className="p-4 rounded-xl border border-gray-100 bg-white shadow-sm flex gap-4 items-start">
                    <div className="w-8 h-8 rounded-full bg-prism-100 flex items-center justify-center shrink-0 mt-0.5">
                       <span className="font-bold text-prism-600 text-xs">2</span>
                    </div>
                    <div>
                       <span className="font-bold text-gray-900 text-sm block mb-1">Technical Excellence</span> 
                       <p className="text-sm text-gray-600 leading-relaxed">Multi-agent architecture using LLMs and deterministic rules (Confidence Genome). Verified via the <b>Raw API Response</b> block at the bottom of the X-Ray view.</p>
                    </div>
                  </div>
                  <div className="p-4 rounded-xl border border-gray-100 bg-white shadow-sm flex gap-4 items-start">
                    <div className="w-8 h-8 rounded-full bg-prism-100 flex items-center justify-center shrink-0 mt-0.5">
                       <span className="font-bold text-prism-600 text-xs">3</span>
                    </div>
                    <div>
                       <span className="font-bold text-gray-900 text-sm block mb-1">Impact</span> 
                       <p className="text-sm text-gray-600 leading-relaxed">Predicts purchases for India's next 500M users before they even search. See the dynamically generated 3-phase timeline in the App Shell that organizes their life event.</p>
                    </div>
                  </div>
                </div>
                <div className="mt-8 pt-4 border-t border-gray-100 flex justify-end">
                  <a href="https://github.com/Swaathi1409/PRISM-Predictive_Reality_Intelligence_for_Smarter_Meesho" target="_blank" rel="noreferrer" className="text-sm font-bold text-white bg-gray-900 hover:bg-black px-6 py-2.5 rounded-full shadow-md transition-all active:scale-95">
                    View GitHub Repo →
                  </a>
                </div>
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
                  src={`/images/${selectedProduct.image_placeholder}.jpg`}
                  onError={(e) => {
                    e.target.onerror = null; 
                    e.target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(selectedProduct.name.split(' ').slice(0,2).join('+'))}&background=random&color=fff&size=512&font-size=0.33`;
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
                          selectedProduct.temporal_strategies.map((ts, idx) => (
                            <div key={idx} className={`p-3 rounded-xl border ${ts.recommended ? 'border-emerald-500 bg-emerald-50 shadow-sm' : 'border-gray-100 bg-white opacity-70'}`}>
                              <div className="flex justify-between items-center mb-1">
                                <span className={`text-xs font-bold ${ts.recommended ? 'text-emerald-700' : 'text-gray-700'}`}>
                                  {ts.strategy_name} {ts.recommended && '✓ Recommended'}
                                </span>
                                {ts.price > 0 && <span className="text-xs font-bold text-gray-900">₹{ts.price}</span>}
                              </div>
                              <p className="text-[10px] text-gray-600 mb-1">{ts.action_date}</p>
                              <p className="text-[10px] text-gray-500 leading-snug">{ts.note}</p>
                            </div>
                          ))
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
                    <button onClick={handleAddToCart} className="py-3.5 rounded-xl text-sm font-bold text-[#F43397] border border-[#F43397] bg-pink-50 hover:bg-pink-100 transition-colors">
                      Add to Cart
                    </button>
                    <button onClick={handleBuyNow} className="py-3.5 rounded-xl text-sm font-bold text-white bg-[#F43397] hover:bg-[#e02b88] shadow-md transition-colors">
                      Buy Now
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
                          src={`/images/${item.image_placeholder}.jpg`}
                          onError={(e) => {
                            e.target.onerror = null;
                            e.target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(item.name.split(' ').slice(0,2).join('+'))}&background=random&color=fff&size=256&font-size=0.33`;
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
