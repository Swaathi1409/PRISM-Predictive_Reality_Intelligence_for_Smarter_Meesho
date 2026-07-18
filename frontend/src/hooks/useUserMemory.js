/**
 * useUserMemory.js — PRISM Deep Behavioral Memory Mining
 *
 * Builds a living user profile from every session:
 * - Extracts city, employer, lifestyle signals from query text
 * - Infers likely-owned categories from products recommended
 * - Maps owned categories → accessory suggestions
 * - Learns budget range across sessions
 * - Builds a context string that the LLM uses to personalise next session
 *
 * All data lives in localStorage under 'prism_user_profile'.
 * Users can wipe it at any time via clearMemory().
 */

import { useState, useCallback } from 'react'

const STORAGE_KEY = 'prism_user_profile'
const MAX_OWNED_CATEGORIES = 20
const FRESHNESS_DAYS = 30

// ── Accessory Mapping Table ────────────────────────────────────────────────
// Maps a category the user likely owns → what to recommend next
const ACCESSORY_MAP = {
  'electronics': ['laptop stand', 'mouse', 'keyboard', 'cooling pad', 'usb hub', 'screen cleaner'],
  'laptop': ['laptop bag', 'mouse', 'keyboard', 'cooling pad', 'laptop stand', 'screen protector'],
  'bags_luggage': ['travel pillow', 'combination lock', 'packing cubes', 'neck pouch', 'luggage tag'],
  'bedding': ['pillow cover', 'bed organizer', 'laundry bag', 'mosquito net', 'mattress protector'],
  'formal_wear': ['belt', 'formal shoes', 'tie', 'watch', 'cufflinks', 'blazer', 'wallet'],
  'kitchen_essentials': ['cookware', 'storage containers', 'cleaning supplies', 'dish rack', 'kitchen towels'],
  'kitchen_appliances': ['cleaning brush', 'storage boxes', 'trivets', 'oven mitts', 'silicone mats'],
  'personal_care': ['cosmetic bag', 'mirror', 'grooming kit', 'bath caddy', 'fragrance'],
  'study_accessories': ['desk lamp', 'pencil holder', 'sticky notes', 'book stand', 'timer'],
  'stationery': ['file organizer', 'pen holder', 'notebook set', 'sticky pads', 'highlighters'],
  'festival_decor': ['candles', 'garlands', 'puja thali', 'storage box', 'incense'],
  'baby_products': ['baby wipes dispenser', 'baby monitor', 'diaper bag', 'feeding set'],
  'home_decor': ['wall clock', 'photo frames', 'vase', 'cushion covers', 'bookshelf'],
  'wedding_apparel': ['jewellery box', 'dupatta pins', 'shoe bag', 'bridal pouch'],
  'home_improvement': ['tool organizer', 'safety gloves', 'measuring tape', 'storage hooks'],
}

// ── City keyword list ──────────────────────────────────────────────────────
const CITY_KEYWORDS = [
  'bangalore', 'bengaluru', 'mumbai', 'delhi', 'chennai', 'hyderabad',
  'pune', 'kolkata', 'ahmedabad', 'jaipur', 'lucknow', 'kochi',
  'indore', 'bhopal', 'nagpur', 'surat', 'vadodara', 'coimbatore',
  'vizag', 'chandigarh', 'patna', 'guwahati', 'bhubaneswar',
]

// ── Employer/Institution keyword list ─────────────────────────────────────
const EMPLOYER_KEYWORDS = [
  'infosys', 'tcs', 'wipro', 'accenture', 'cognizant', 'hcl', 'tech mahindra',
  'iit', 'nit', 'iim', 'aiims', 'bits', 'srm', 'vit',
  'amazon', 'flipkart', 'google', 'microsoft', 'zoho', 'razorpay',
]

// ── Lifestyle tag extractors ───────────────────────────────────────────────
const LIFESTYLE_KEYWORDS = {
  tech: ['laptop', 'coding', 'software', 'developer', 'engineer', 'programmer', 'tech'],
  student: ['hostel', 'college', 'university', 'exam', 'semester', 'degree', 'campus'],
  professional: ['office', 'corporate', 'job', 'career', 'joining', 'salary', 'work'],
  traveller: ['trek', 'travel', 'trip', 'vacation', 'tour', 'adventure', 'pilgrimage'],
  homemaker: ['kitchen', 'home', 'house', 'flat', 'apartment', 'moving', 'decor'],
  festive: ['diwali', 'navratri', 'wedding', 'puja', 'eid', 'christmas', 'holi'],
}

function _loadProfile() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function _saveProfile(profile) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(profile))
  } catch {
    // quota exceeded — ignore
  }
}

function _defaultProfile() {
  return {
    likely_owned_categories: [],     // [{ category, addedAt }]
    recently_recommended_categories: {}, // { category: ISO date string }
    recommended_product_ids: [],
    city: null,
    company: null,
    lifestyle_tags: [],
    event_history: [],
    budget_history: [],   // last 5 budget values
    session_count: 0,
    last_query_date: null,
  }
}

/**
 * Extract signals from a plain-text query string.
 * Returns { city, company, lifestyleTags }
 */
function extractSignals(queryText) {
  const lower = queryText.toLowerCase()
  const signals = { city: null, company: null, lifestyleTags: [] }

  for (const city of CITY_KEYWORDS) {
    if (lower.includes(city)) { signals.city = city; break }
  }
  for (const employer of EMPLOYER_KEYWORDS) {
    if (lower.includes(employer)) { signals.company = employer; break }
  }
  for (const [tag, keywords] of Object.entries(LIFESTYLE_KEYWORDS)) {
    if (keywords.some(kw => lower.includes(kw))) {
      signals.lifestyleTags.push(tag)
    }
  }
  return signals
}

/**
 * Given a list of owned category names, return accessory suggestions.
 */
function getAccessoryHints(ownedCategories) {
  const hints = new Set()
  for (const cat of ownedCategories) {
    const catLower = cat.toLowerCase()
    for (const [key, accessories] of Object.entries(ACCESSORY_MAP)) {
      if (catLower.includes(key) || key.includes(catLower)) {
        accessories.forEach(a => hints.add(a))
      }
    }
  }
  return [...hints].slice(0, 8)
}

/**
 * Get categories that were recommended recently (within FRESHNESS_DAYS).
 * These should be avoided to ensure the user sees fresh recommendations.
 */
function getStaleCategories(profile) {
  const cutoff = Date.now() - FRESHNESS_DAYS * 24 * 60 * 60 * 1000
  return Object.entries(profile.recently_recommended_categories || {})
    .filter(([, date]) => new Date(date).getTime() > cutoff)
    .map(([cat]) => cat)
}

/**
 * Build the full LLM context string from the user's profile.
 * This gets injected at the top of the PRISM LLM prompt.
 */
function buildContextString(profile) {
  if (!profile || profile.session_count < 1) return null

  const lines = [`[PRISM Memory Intelligence — Session ${profile.session_count + 1}]`]

  // Identity signals
  const identity = []
  if (profile.city) identity.push(`City=${profile.city.charAt(0).toUpperCase() + profile.city.slice(1)}`)
  if (profile.company) identity.push(`Employer=${profile.company.toUpperCase()}`)
  if (profile.lifestyle_tags.length > 0) identity.push(`Lifestyle=${profile.lifestyle_tags.map(t => t.charAt(0).toUpperCase() + t.slice(1)).join(', ')}`)
  if (identity.length > 0) lines.push(`User Profile: ${identity.join(' | ')}`)

  // Owned categories
  const ownedCats = profile.likely_owned_categories.map(o => o.category)
  if (ownedCats.length > 0) {
    lines.push(`Likely already owns: ${ownedCats.slice(0, 6).join(', ')}`)
    lines.push(`→ DO NOT recommend these as primary picks: ${ownedCats.slice(0, 4).join(', ')}`)
    const accessories = getAccessoryHints(ownedCats)
    if (accessories.length > 0) {
      lines.push(`→ PRIORITISE accessories/complements: ${accessories.slice(0, 5).join(', ')}`)
    }
  }

  // Recently seen (freshness)
  const stale = getStaleCategories(profile)
  if (stale.length > 0) {
    lines.push(`Recently recommended (avoid repeating): ${stale.join(', ')}`)
  }

  // Budget affinity
  if (profile.budget_history.length >= 2) {
    const validBudgets = profile.budget_history.filter(b => b > 0)
    if (validBudgets.length >= 2) {
      const avg = Math.round(validBudgets.reduce((a, b) => a + b, 0) / validBudgets.length)
      const min = Math.min(...validBudgets)
      const max = Math.max(...validBudgets)
      lines.push(`Budget affinity: ₹${min.toLocaleString('en-IN')}–₹${max.toLocaleString('en-IN')} (avg ₹${avg.toLocaleString('en-IN')} across ${validBudgets.length} sessions)`)
    }
  }

  // Event history
  if (profile.event_history.length > 0) {
    lines.push(`Event history: ${profile.event_history.slice(-3).join(', ')}`)
    const lastEvent = profile.event_history[profile.event_history.length - 1]
    if (lastEvent === 'hostel_move' || lastEvent === 'first_job') {
      lines.push(`→ User is recently settled in a new environment. Focus on productivity, comfort, and lifestyle upgrades.`)
    }
  }

  return lines.join('\n')
}

// ── The hook ───────────────────────────────────────────────────────────────
export function useUserMemory() {
  const [profile, setProfile] = useState(() => _loadProfile())

  /**
   * Called after a successful PRISM analysis.
   * Mines the result to update the behavioral profile.
   */
  const addSessionResult = useCallback((queryText, budget, result) => {
    setProfile(prev => {
      const p = prev ? { ...prev } : _defaultProfile()

      // Extract text signals
      const signals = extractSignals(queryText)
      if (signals.city && !p.city) p.city = signals.city
      if (signals.company && !p.company) p.company = signals.company
      // Merge lifestyle tags (no duplicates)
      p.lifestyle_tags = [...new Set([...(p.lifestyle_tags || []), ...signals.lifestyleTags])].slice(0, 8)

      // Track event history
      if (result?.event_key && result.event_key !== 'generic' && result.event_key !== 'unsupported') {
        p.event_history = [...new Set([...(p.event_history || []), result.event_key])].slice(-5)
      }

      // Mine recommended categories from all_products in the result
      const allProducts = result?.all_products || []
      const newCategoryEntries = []
      const now = new Date().toISOString()

      allProducts.forEach(prod => {
        const cat = prod.category
        if (!cat || cat === 'system') return
        const alreadyOwned = (p.likely_owned_categories || []).some(o => o.category === cat)
        if (!alreadyOwned && !newCategoryEntries.some(o => o.category === cat)) {
          newCategoryEntries.push({ category: cat, addedAt: now })
        }
        // Update recently_recommended timestamp
        p.recently_recommended_categories = {
          ...(p.recently_recommended_categories || {}),
          [cat]: now,
        }
      })

      p.likely_owned_categories = [
        ...(p.likely_owned_categories || []),
        ...newCategoryEntries,
      ].slice(-MAX_OWNED_CATEGORIES)

      // Track product IDs to avoid re-surfacing exact same items
      const newIds = allProducts.map(p => p.id).filter(Boolean)
      p.recommended_product_ids = [...new Set([...(p.recommended_product_ids || []), ...newIds])].slice(-100)

      // Budget learning
      if (budget && budget > 0) {
        p.budget_history = [...(p.budget_history || []), budget].slice(-5)
      }

      p.session_count = (p.session_count || 0) + 1
      p.last_query_date = now

      _saveProfile(p)
      return p
    })
  }, [])

  /**
   * Returns the `avoid_categories` array to send in the API payload.
   * Contains the user's likely-owned category names.
   */
  const getAvoidCategories = useCallback(() => {
    if (!profile) return []
    return (profile.likely_owned_categories || []).map(o => o.category)
  }, [profile])

  /**
   * Returns the full LLM context string to send as `user_context` in the API payload.
   */
  const getContextString = useCallback(() => {
    return buildContextString(profile)
  }, [profile])

  /**
   * Returns display-ready tag pills for the UserMemoryChip UI.
   */
  const memoryTags = (() => {
    if (!profile || profile.session_count < 1) return []
    const tags = []
    if (profile.city) tags.push({ icon: '🏙', label: profile.city.charAt(0).toUpperCase() + profile.city.slice(1) })
    if (profile.company) tags.push({ icon: '💼', label: profile.company.toUpperCase() })
    profile.lifestyle_tags?.slice(0, 2).forEach(t => {
      const icons = { tech: '💻', student: '🎓', professional: '👔', traveller: '✈️', homemaker: '🏠', festive: '🪔' }
      tags.push({ icon: icons[t] || '⭐', label: t.charAt(0).toUpperCase() + t.slice(1) })
    })
    if (profile.session_count > 1) tags.push({ icon: '⭐', label: `${profile.session_count} sessions` })
    return tags
  })()

  /**
   * Returns the "skipping" categories (likely owned) for the memory panel.
   */
  const skippingCategories = (() => {
    if (!profile) return []
    return (profile.likely_owned_categories || []).slice(-6).map(o => ({
      category: o.category,
      reason: 'Likely already owned',
      accessories: getAccessoryHints([o.category]).slice(0, 3),
    }))
  })()

  /**
   * Clears the entire memory profile.
   */
  const clearMemory = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY)
    setProfile(null)
  }, [])

  const hasMemory = !!profile && profile.session_count >= 1

  return {
    profile,
    hasMemory,
    memoryTags,
    skippingCategories,
    addSessionResult,
    getAvoidCategories,
    getContextString,
    getAccessoryHints,
    clearMemory,
  }
}
