/**
 * ProductCard.jsx — Top recommended product display.
 *
 * Shows the PRISM top product with all key seller details,
 * stock status, delivery info, and the overall verdict badge.
 */

import { motion } from 'framer-motion'
import { Package, Star, TrendingUp, TrendingDown, Truck, ShoppingBag } from 'lucide-react'
import { VERDICT_CONFIG } from '../utils/constants'

export default function ProductCard({ product, finalVerdict }) {
  if (!product) return null

  const verdictCfg = VERDICT_CONFIG[finalVerdict] || VERDICT_CONFIG.caution
  const priceChange = product.price_trend_7d || 0
  const isRising = priceChange > 0
  const isFalling = priceChange < 0

  return (
    <motion.section
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      id="top-recommendation-section"
      aria-label="PRISM Top Recommendation"
    >
      <div className="rounded-2xl border border-prism-500/40 bg-gradient-to-br from-prism-500/10 to-surface-card p-5 shadow-prism">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <ShoppingBag className="w-4 h-4 text-prism-400" />
            <span className="text-sm font-medium text-prism-300">PRISM Top Pick</span>
          </div>
          <span className={`text-sm font-bold px-3 py-1 rounded-full border ${verdictCfg.bg} ${verdictCfg.color}`}>
            {verdictCfg.icon} {verdictCfg.label}
          </span>
        </div>

        {/* Product main info */}
        <div className="flex items-start gap-4">
          {/* Image */}
          <div className="w-20 h-20 rounded-xl bg-surface-elevated border border-surface-border flex-shrink-0 flex items-center justify-center overflow-hidden">
            <img
              src={product.image_url && !product.image_url.includes('placehold') ? product.image_url.replace(/\/images\/W\/IMAGERENDERING_[A-Z0-9-]+/, '') : `/images/${product.id}.jpg`}
              alt={product.name}
              referrerPolicy="no-referrer"
              className="w-full h-full object-cover"
              onError={(e) => {
                if (!e.target.src.includes(product.id)) {
                  e.target.src = `/images/${product.id}.jpg`;
                } else {
                  e.target.onerror = null;
                  e.target.src = `https://placehold.co/400x400/1e293b/94a3b8?text=Image\\nNot\\nAvailable`;
                }
              }}
            />
          </div>

          <div className="flex-1 min-w-0">
            <h2 className="font-display font-bold text-white text-base leading-tight mb-1">
              {product.name}
            </h2>
            <p className="text-xs text-gray-500 mb-2">{product.description}</p>

            {/* Price */}
            <div className="flex items-center gap-3 mb-2">
              <span className="font-display font-extrabold text-2xl text-white">
                ₹{product.price?.toLocaleString('en-IN')}
              </span>
              <div className={`flex items-center gap-1 text-xs font-medium ${
                isRising ? 'text-red-400' : isFalling ? 'text-emerald-400' : 'text-gray-500'
              }`}>
                {isRising && <TrendingUp className="w-3 h-3" />}
                {isFalling && <TrendingDown className="w-3 h-3" />}
                <span>{priceChange > 0 ? '+' : ''}{priceChange.toFixed(1)}% / 7d</span>
              </div>
            </div>

            {/* Stock status */}
            <span className={`inline-block text-xs px-2 py-0.5 rounded-full font-medium mb-2 ${
              product.stock_status === 'in_stock'
                ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                : product.stock_status === 'low_stock'
                ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                : 'bg-red-500/15 text-red-400 border border-red-500/30'
            }`}>
              {product.stock_status === 'in_stock' ? '● In Stock' : product.stock_status === 'low_stock' ? '⚠ Low Stock' : '✕ Out of Stock'}
            </span>
          </div>
        </div>

        {/* Seller info row */}
        <div className="mt-4 pt-4 border-t border-surface-border grid grid-cols-3 gap-3">
          <SellerStat
            icon={<Star className="w-3.5 h-3.5 text-amber-400" />}
            label="Rating"
            value={`${product.seller_rating?.toFixed(1)}★`}
          />
          <SellerStat
            icon={<Truck className="w-3.5 h-3.5 text-blue-400" />}
            label="Delivery"
            value={`${product.delivery_days}d`}
          />
          <SellerStat
            icon={<Package className="w-3.5 h-3.5 text-prism-400" />}
            label="Returns"
            value={`${product.seller_return_rate}%`}
          />
        </div>

        {/* Seller name */}
        <p className="text-xs text-gray-600 mt-3">
          Sold by <span className="text-gray-400 font-medium">{product.seller_name}</span>
          {' · '}{product.seller_review_count?.toLocaleString('en-IN')} reviews
        </p>
      </div>
    </motion.section>
  )
}

function SellerStat({ icon, label, value }) {
  return (
    <div className="text-center">
      <div className="flex items-center justify-center gap-1 mb-1">
        {icon}
        <span className="text-xs text-gray-500">{label}</span>
      </div>
      <span className="text-sm font-semibold text-white">{value}</span>
    </div>
  )
}
