/**
 * ProductCatalog.jsx — Two-row product display for PRISM results.
 *
 * Row 1 — PRISM Top Picks (horizontal scroll):
 *   One card per subcategory. The 4 agents (Kismat, Paisa, Samay, Soch) voted
 *   on every product; this row shows the winner in each product class.
 *   Cards are larger, show the PRISM score badge, and have a gold border.
 *
 * Row 2 — More to Explore (horizontal scroll):
 *   Budget variants and alternatives that didn't win their subcategory.
 *   Smaller, subdued cards.
 *
 * OOS gap cards are shown in Row 1 with a grayscale placeholder so users
 * know what PRISM searched for but couldn't find.
 */

import { useRef } from 'react'
import { motion } from 'framer-motion'
import {
  Star, Truck, ShieldCheck, TrendingDown, TrendingUp,
  ChevronLeft, ChevronRight, Sparkles, LayoutGrid, Package,
  ShoppingBag, BadgeCheck, Zap,
} from 'lucide-react'

// ─── helpers ────────────────────────────────────────────────────────────────

function scoreColor(score) {
  if (score >= 80) return { text: '#22d3ee', bg: 'rgba(34,211,238,0.12)', border: 'rgba(34,211,238,0.3)' }
  if (score >= 65) return { text: '#a78bfa', bg: 'rgba(167,139,250,0.12)', border: 'rgba(167,139,250,0.3)' }
  return { text: '#94a3b8', bg: 'rgba(148,163,184,0.08)', border: 'rgba(148,163,184,0.2)' }
}

function stockBadge(status) {
  if (status === 'in_stock') return { label: '● In Stock', color: '#34d399', bg: 'rgba(52,211,153,0.1)' }
  if (status === 'low_stock') return { label: '⚠ Low Stock', color: '#fbbf24', bg: 'rgba(251,191,36,0.1)' }
  return { label: '✕ Out of Stock', color: '#f87171', bg: 'rgba(248,113,113,0.1)' }
}

function formatPrice(price) {
  if (!price || price === 0) return null
  return '₹' + price.toLocaleString('en-IN')
}

// ─── Horizontal scroll row with arrow buttons ────────────────────────────────

function ScrollRow({ children, id }) {
  const ref = useRef(null)
  const scroll = (dir) => {
    if (ref.current) ref.current.scrollBy({ left: dir * 280, behavior: 'smooth' })
  }
  return (
    <div className="relative group" id={id}>
      {/* Left arrow */}
      <button
        onClick={() => scroll(-1)}
        aria-label="Scroll left"
        style={{
          position: 'absolute', left: -14, top: '50%', transform: 'translateY(-50%)',
          zIndex: 10, width: 32, height: 32, borderRadius: '50%',
          background: 'rgba(15,10,30,0.95)', border: '1px solid rgba(167,139,250,0.3)',
          color: '#a78bfa', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
          opacity: 0, transition: 'opacity 0.2s',
        }}
        className="group-hover:opacity-100"
      >
        <ChevronLeft size={16} />
      </button>

      {/* Scroll container */}
      <div
        ref={ref}
        style={{
          display: 'flex', gap: 14, overflowX: 'auto', paddingBottom: 8,
          scrollbarWidth: 'none', msOverflowStyle: 'none',
        }}
      >
        {children}
      </div>

      {/* Right arrow */}
      <button
        onClick={() => scroll(1)}
        aria-label="Scroll right"
        style={{
          position: 'absolute', right: -14, top: '50%', transform: 'translateY(-50%)',
          zIndex: 10, width: 32, height: 32, borderRadius: '50%',
          background: 'rgba(15,10,30,0.95)', border: '1px solid rgba(167,139,250,0.3)',
          color: '#a78bfa', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
          opacity: 0, transition: 'opacity 0.2s',
        }}
        className="group-hover:opacity-100"
      >
        <ChevronRight size={16} />
      </button>
    </div>
  )
}

// ─── Top Pick Card (Row 1) ───────────────────────────────────────────────────

function TopPickCard({ product, index }) {
  const score = Math.round(product.confidence_score || 0)
  const sc = scoreColor(score)
  const sb = stockBadge(product.stock_status)
  const isOOS = product.stock_status === 'out_of_stock'
  const priceChange = product.price_trend_7d || 0
  const hasDiscount = product.discount_percent > 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.4, ease: 'easeOut' }}
      id={`top-pick-${product.id}`}
      style={{
        flexShrink: 0,
        width: 220,
        borderRadius: 16,
        border: isOOS ? '1px solid rgba(148,163,184,0.2)' : '1px solid rgba(167,139,250,0.35)',
        background: isOOS
          ? 'rgba(15,10,30,0.6)'
          : 'linear-gradient(145deg, rgba(108,43,217,0.14) 0%, rgba(15,10,30,0.9) 100%)',
        padding: '14px 14px 12px',
        position: 'relative',
        boxShadow: isOOS ? 'none' : '0 0 24px rgba(108,43,217,0.15)',
        opacity: isOOS ? 0.6 : 1,
        cursor: isOOS ? 'default' : 'pointer',
        transition: 'transform 0.2s, box-shadow 0.2s',
      }}
      whileHover={!isOOS ? { y: -3, boxShadow: '0 8px 32px rgba(108,43,217,0.28)' } : {}}
    >
      {/* PRISM score badge — top right */}
      {!isOOS && score > 0 && (
        <div style={{
          position: 'absolute', top: 10, right: 10,
          fontSize: 10, fontWeight: 700, letterSpacing: '0.02em',
          padding: '2px 7px', borderRadius: 20,
          background: sc.bg, color: sc.text, border: `1px solid ${sc.border}`,
        }}>
          {score}
        </div>
      )}

      {/* Product image / placeholder */}
      <div style={{
        width: '100%', height: 110, borderRadius: 10, marginBottom: 10,
        background: isOOS ? 'rgba(148,163,184,0.05)' : 'rgba(15,10,30,0.5)',
        border: '1px solid rgba(255,255,255,0.06)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        overflow: 'hidden',
      }}>
        {product.image_url && !product.image_url.includes('placehold') ? (
          <img
            src={product.image_url.replace(/\/images\/W\/IMAGERENDERING_[A-Z0-9-]+/, '')}
            alt={product.name}
            referrerPolicy="no-referrer"
            style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 10 }}
            onError={(e) => { e.target.style.display = 'none' }}
          />
        ) : (
          <Package size={32} color={isOOS ? '#4b5563' : '#6b7280'} />
        )}
      </div>

      {/* Category chip */}
      <div style={{
        fontSize: 9, fontWeight: 600, letterSpacing: '0.05em', textTransform: 'uppercase',
        color: isOOS ? '#6b7280' : '#a78bfa', marginBottom: 4,
      }}>
        {(product.subcategory || product.category || '').replace(/_/g, ' ')}
      </div>

      {/* Name */}
      <p style={{
        fontSize: 12, fontWeight: 600, color: isOOS ? '#6b7280' : '#e2e8f0',
        lineHeight: 1.4, marginBottom: 6,
        display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden',
      }}>
        {product.name}
      </p>

      {/* Price row */}
      {!isOOS && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
          <span style={{ fontSize: 15, fontWeight: 800, color: '#fff' }}>
            {formatPrice(product.price)}
          </span>
          {hasDiscount && (
            <span style={{
              fontSize: 10, fontWeight: 600, color: '#34d399',
              background: 'rgba(52,211,153,0.1)', padding: '1px 6px', borderRadius: 10,
            }}>
              -{product.discount_percent}%
            </span>
          )}
          {priceChange !== 0 && (
            <span style={{ fontSize: 10, color: priceChange > 0 ? '#f87171' : '#34d399', display: 'flex', alignItems: 'center', gap: 2 }}>
              {priceChange > 0 ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
              {Math.abs(priceChange).toFixed(1)}%
            </span>
          )}
        </div>
      )}

      {/* Stock + delivery row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
        <span style={{
          fontSize: 10, fontWeight: 500, color: sb.color,
          background: sb.bg, padding: '2px 7px', borderRadius: 10,
        }}>
          {sb.label}
        </span>
        {!isOOS && product.delivery_days && (
          <span style={{ fontSize: 10, color: '#64748b', display: 'flex', alignItems: 'center', gap: 3 }}>
            <Truck size={9} />
            {product.delivery_days}d
          </span>
        )}
      </div>

      {/* Seller + rating */}
      {!isOOS && (
        <div style={{
          borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 8,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <span style={{ fontSize: 10, color: '#64748b', maxWidth: 110, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {product.seller_name}
          </span>
          {product.seller_rating > 0 && (
            <span style={{ fontSize: 10, fontWeight: 600, color: '#fbbf24', display: 'flex', alignItems: 'center', gap: 2 }}>
              <Star size={10} fill="#fbbf24" />
              {product.seller_rating?.toFixed(1)}
            </span>
          )}
        </div>
      )}

      {/* OOS label */}
      {isOOS && (
        <div style={{ textAlign: 'center', paddingTop: 4 }}>
          <span style={{ fontSize: 10, color: '#64748b' }}>Not in catalog yet</span>
        </div>
      )}
    </motion.div>
  )
}

// ─── Other Product Card (Row 2, smaller) ────────────────────────────────────

function OtherProductCard({ product, index }) {
  const score = Math.round(product.confidence_score || 0)
  const sc = scoreColor(score)
  const hasDiscount = product.discount_percent > 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04, duration: 0.35 }}
      id={`other-product-${product.id}`}
      style={{
        flexShrink: 0,
        width: 164,
        borderRadius: 12,
        border: '1px solid rgba(255,255,255,0.07)',
        background: 'rgba(15,10,30,0.7)',
        padding: '10px 10px 8px',
        cursor: 'pointer',
        transition: 'border-color 0.2s',
      }}
      whileHover={{ borderColor: 'rgba(167,139,250,0.25)', y: -2 }}
    >
      {/* Image */}
      <div style={{
        width: '100%', height: 76, borderRadius: 8, marginBottom: 8,
        background: 'rgba(15,10,30,0.5)', border: '1px solid rgba(255,255,255,0.05)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden',
      }}>
        {product.image_url && !product.image_url.includes('placehold') ? (
          <img
            src={product.image_url.replace(/\/images\/W\/IMAGERENDERING_[A-Z0-9-]+/, '')}
            alt={product.name}
            referrerPolicy="no-referrer"
            style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 8 }}
            onError={(e) => { e.target.style.display = 'none' }}
          />
        ) : (
          <Package size={22} color="#4b5563" />
        )}
      </div>

      {/* Name */}
      <p style={{
        fontSize: 11, fontWeight: 500, color: '#94a3b8', lineHeight: 1.35, marginBottom: 5,
        display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden',
      }}>
        {product.name}
      </p>

      {/* Price + discount */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 5 }}>
        <span style={{ fontSize: 12, fontWeight: 700, color: '#e2e8f0' }}>
          {formatPrice(product.price)}
        </span>
        {hasDiscount && (
          <span style={{ fontSize: 9, color: '#34d399', fontWeight: 600 }}>
            -{product.discount_percent}%
          </span>
        )}
      </div>

      {/* Score + rating */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        {score > 0 && (
          <span style={{
            fontSize: 9, fontWeight: 600, color: sc.text, background: sc.bg,
            border: `1px solid ${sc.border}`, padding: '1px 5px', borderRadius: 8,
          }}>
            {score}
          </span>
        )}
        {product.seller_rating > 0 && (
          <span style={{ fontSize: 10, color: '#fbbf24', display: 'flex', alignItems: 'center', gap: 2 }}>
            <Star size={9} fill="#fbbf24" />
            {product.seller_rating?.toFixed(1)}
          </span>
        )}
      </div>
    </motion.div>
  )
}

// ─── Main Component ──────────────────────────────────────────────────────────

export default function ProductCatalog({ topPicks = [], otherProducts = [], isSpecificAsk = false, primaryItemLabel = null }) {
  if (!topPicks.length && !otherProducts.length) return null

  const itemDisplay = primaryItemLabel
    ? primaryItemLabel.charAt(0).toUpperCase() + primaryItemLabel.slice(1)
    : 'Product'

  return (
    <section id="product-catalog-section" aria-label="PRISM Product Recommendations">
      {/* ── Row 1: PRISM Top Picks ── */}
      {topPicks.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
          style={{
            borderRadius: 18,
            border: '1px solid rgba(167,139,250,0.25)',
            background: 'linear-gradient(135deg, rgba(108,43,217,0.08) 0%, rgba(15,10,30,0.85) 100%)',
            padding: '18px 18px 14px',
            marginBottom: 14,
          }}
        >
          {/* Header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
            <div style={{
              width: 28, height: 28, borderRadius: 8,
              background: 'linear-gradient(135deg, #7c3aed, #4f46e5)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Sparkles size={14} color="#fff" />
            </div>
            <div>
              <p style={{ fontSize: 13, fontWeight: 700, color: '#e2e8f0', margin: 0 }}>
                {isSpecificAsk ? `Best ${itemDisplay} Match` : 'PRISM Top Picks'}
              </p>
              <p style={{ fontSize: 10, color: '#64748b', margin: 0 }}>
                {isSpecificAsk
                  ? `Showing only ${itemDisplay.toLowerCase()}s · 4-agent verified`
                  : 'Best in class · 4-agent verified · One per product type'}
              </p>
            </div>
            <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 4 }}>
              <Zap size={11} color="#a78bfa" />
              <span style={{ fontSize: 10, color: '#a78bfa', fontWeight: 600 }}>
                {topPicks.filter(p => p.stock_status !== 'out_of_stock').length} picks
              </span>
            </div>
          </div>

          {/* Agent badges */}
          <div style={{ display: 'flex', gap: 6, marginBottom: 14, flexWrap: 'wrap' }}>
            {[
              { name: 'Kismat', label: 'Trust', color: '#34d399' },
              { name: 'Paisa', label: 'Budget', color: '#fbbf24' },
              { name: 'Samay', label: 'Timing', color: '#60a5fa' },
              { name: 'Soch', label: 'Intelligence', color: '#f472b6' },
            ].map((a) => (
              <span key={a.name} style={{
                fontSize: 9, fontWeight: 600, padding: '2px 8px', borderRadius: 10,
                color: a.color, background: `${a.color}15`, border: `1px solid ${a.color}30`,
                display: 'flex', alignItems: 'center', gap: 3,
              }}>
                <BadgeCheck size={9} color={a.color} />
                {a.name} · {a.label}
              </span>
            ))}
          </div>

          {/* Cards scroll row */}
          <ScrollRow id="top-picks-scroll">
            {topPicks.map((product, i) => (
              <TopPickCard key={product.id} product={product} index={i} />
            ))}
          </ScrollRow>
        </motion.div>
      )}

      {/* ── Row 2: More to Explore ── */}
      {otherProducts.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 0.15 }}
          style={{
            borderRadius: 16,
            border: '1px solid rgba(255,255,255,0.07)',
            background: 'rgba(15,10,30,0.6)',
            padding: '16px 16px 12px',
          }}
        >
          {/* Header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
            <LayoutGrid size={15} color="#64748b" />
            <div>
              <p style={{ fontSize: 12, fontWeight: 600, color: '#94a3b8', margin: 0 }}>
                {isSpecificAsk && primaryItemLabel
                  ? `You may also need after buying your ${itemDisplay.toLowerCase()}`
                  : 'More to Explore'}
              </p>
              <p style={{ fontSize: 10, color: '#475569', margin: 0 }}>
                {isSpecificAsk ? 'Accessories & essentials · Optional add-ons' : 'Budget variants & alternatives'}
              </p>
            </div>
            <span style={{ marginLeft: 'auto', fontSize: 10, color: '#475569' }}>
              {otherProducts.length} items
            </span>
          </div>

          {/* Cards scroll row */}
          <ScrollRow id="other-products-scroll">
            {otherProducts.map((product, i) => (
              <OtherProductCard key={product.id} product={product} index={i} />
            ))}
          </ScrollRow>
        </motion.div>
      )}
    </section>
  )
}
