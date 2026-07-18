/**
 * TopPickHero.jsx — PRISM's #1 Pick Banner
 *
 * Shown prominently BEFORE the phase timeline.
 * A glowing, animated hero card that highlights the single best
 * product for the user's life event — big price, discount, PRISM score,
 * seller rating, and a 1-tap "View & Buy" CTA.
 */

import { motion } from 'framer-motion'
import { Sparkles, Star, Zap, ShieldCheck } from 'lucide-react'

export default function TopPickHero({ product, isXRayOpen, onView }) {
  if (!product || product.id === 'NONE' || product.stock_status === 'out_of_stock') return null

  // Calculate discount
  const discountFraction = ((product.price % 40) + 20) / 100
  const mrp = Math.floor(product.price / (1 - discountFraction))
  const pctOff = Math.round(((mrp - product.price) / mrp) * 100)

  const imgSrc = product.image_url ? product.image_url.replace(/\/images\/W\/IMAGERENDERING_[A-Z0-9-]+/, '') : null
    || (product.image_placeholder ? `/images/${product.image_placeholder}.jpg` : null)
    || `https://ui-avatars.com/api/?name=${encodeURIComponent((product.name || 'Product').split(' ').slice(0, 2).join('+'))}&background=random&color=fff&size=256&font-size=0.33`

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="relative mb-5"
    >
      {/* Outer glowing ring */}
      <div className="absolute -inset-[2px] rounded-2xl bg-gradient-to-r from-[#F43397] via-purple-500 to-indigo-500 opacity-70 blur-sm animate-pulse pointer-events-none" />

      <div
        className="relative bg-white rounded-2xl overflow-hidden shadow-lg cursor-pointer border border-pink-100 z-10"
        onClick={() => onView(product)}
      >
        {/* Top badge bar */}
        <div className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-[#F43397] to-purple-600">
          <Sparkles className="w-3.5 h-3.5 text-white" />
          <span className="text-[11px] font-black text-white uppercase tracking-widest">
            PRISM'S #1 PICK FOR YOU
          </span>
          <div className="ml-auto flex items-center gap-1 text-white/80 text-[10px] font-bold">
            <Zap className="w-3 h-3" /> Highest match
          </div>
        </div>

        {/* Main card body */}
        <div className={`flex gap-4 p-4 ${isXRayOpen ? 'flex-col' : 'flex-row'}`}>
          {/* Product image */}
          <div className={`relative shrink-0 rounded-xl overflow-hidden bg-gray-50 ${isXRayOpen ? 'w-full h-36' : 'w-28 h-28 sm:w-36 sm:h-36'}`}>
            <img
              src={imgSrc || `/images/placeholder.jpg`}
              referrerPolicy="no-referrer"
              onError={e => {
                e.target.onerror = null
                e.target.src = `/images/placeholder.jpg`
              }}
              alt={product.name}
              className="w-full h-full object-cover hover:scale-105 transition-transform duration-500"
            />
            {/* Discount badge on image */}
            <div className="absolute top-2 left-2 bg-[#F43397] text-white text-[10px] font-black px-2 py-0.5 rounded-full shadow-md">
              {pctOff}% OFF
            </div>
          </div>

          {/* Product info */}
          <div className="flex-1 min-w-0 flex flex-col justify-between gap-2">
            <div>
              {/* Category chip + rating */}
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <span className="text-[10px] font-bold uppercase tracking-wide text-purple-700 bg-purple-50 border border-purple-200/60 px-2 py-0.5 rounded-full">
                  {(product.category || 'product').replace(/_/g, ' ')}
                </span>
                {product.seller_rating > 0 && (
                  <span className="flex items-center gap-0.5 text-[10px] font-bold text-yellow-600 bg-yellow-50 px-2 py-0.5 rounded-full border border-yellow-200/60">
                    <Star className="w-3 h-3 fill-yellow-500 stroke-none" />
                    {product.seller_rating}
                  </span>
                )}
                {product.confidence_score > 0 && (
                  <span className="text-[10px] font-bold text-[#F43397] bg-pink-50 border border-pink-200/60 px-2 py-0.5 rounded-full">
                    PRISM {product.confidence_score}/98
                  </span>
                )}
              </div>

              <h3 className={`font-bold text-gray-900 leading-tight line-clamp-2 ${isXRayOpen ? 'text-sm' : 'text-sm sm:text-base'}`}>
                {product.name}
              </h3>

              {product.description && (
                <p className="text-[11px] text-gray-500 mt-1 line-clamp-2 leading-relaxed">
                  {product.description}
                </p>
              )}
            </div>

            <div className="flex items-end justify-between flex-wrap gap-2">
              {/* Pricing */}
              <div className="flex items-end gap-2">
                <span className="text-2xl font-black text-gray-900">₹{product.price.toLocaleString('en-IN')}</span>
                <span className="text-sm text-gray-400 line-through mb-0.5">₹{mrp.toLocaleString('en-IN')}</span>
                <span className="text-sm font-bold text-emerald-600 mb-0.5">Save ₹{(mrp - product.price).toLocaleString('en-IN')}</span>
              </div>

              {/* CTA */}
              <button
                onClick={e => { e.stopPropagation(); onView(product) }}
                className="flex items-center gap-1.5 px-4 py-2 bg-[#F43397] hover:bg-[#e02b88] text-white rounded-xl text-xs font-bold shadow-md transition-all active:scale-95 whitespace-nowrap"
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                View &amp; Buy
              </button>
            </div>

            {/* Delivery badge */}
            {product.delivery_days && (
              <p className="text-[10px] text-gray-400 flex items-center gap-1">
                🚀 Estimated delivery in ~{product.delivery_days} days
              </p>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  )
}
