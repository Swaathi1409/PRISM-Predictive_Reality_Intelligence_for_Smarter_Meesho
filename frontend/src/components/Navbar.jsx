/**
 * Navbar.jsx — Persistent navigation bar with PRISM branding.
 *
 * Library: react-router-dom (MIT) for navigation, lucide-react (ISC) for icons.
 * Framer Motion (MIT) for entrance animation.
 */

import { Link, useNavigate, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Home, Info, RefreshCw, Sparkles } from 'lucide-react'
import { usePrism } from '../context/PrismContext'

export default function Navbar() {
  const navigate = useNavigate()
  const location = useLocation()
  const { clearResult } = usePrism()

  const handleTryAgain = () => {
    clearResult()
    navigate('/')
  }

  return (
    <motion.nav
      initial={{ y: -60, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="fixed top-0 left-0 right-0 z-50 border-b border-surface-border bg-surface-DEFAULT/80 backdrop-blur-xl"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-lg bg-prism-gradient flex items-center justify-center shadow-prism">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="font-display font-bold text-xl text-white group-hover:text-prism-300 transition-colors">
              PRISM
            </span>
            <span className="hidden sm:block text-xs text-prism-400 font-medium border border-prism-500/30 rounded-full px-2 py-0.5">
              Beta
            </span>
          </Link>

          {/* Nav links */}
          <div className="flex items-center gap-1 sm:gap-2">
            <NavLink to="/" icon={<Home className="w-4 h-4" />} label="Home" current={location.pathname === '/'} />
            <NavLink to="/about" icon={<Info className="w-4 h-4" />} label="About" current={location.pathname === '/about'} />

            {location.pathname === '/demo' && (
              <motion.button
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                onClick={handleTryAgain}
                id="try-again-btn"
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-prism-600 hover:bg-prism-500 text-white text-sm font-medium transition-all hover:shadow-prism active:scale-95"
              >
                <RefreshCw className="w-4 h-4" />
                <span className="hidden sm:block">Try Again</span>
              </motion.button>
            )}
          </div>
        </div>
      </div>
    </motion.nav>
  )
}

function NavLink({ to, icon, label, current }) {
  return (
    <Link
      to={to}
      className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all
        ${current
          ? 'bg-prism-500/20 text-prism-300 border border-prism-500/30'
          : 'text-gray-400 hover:text-white hover:bg-white/5'
        }`}
    >
      {icon}
      <span className="hidden sm:block">{label}</span>
    </Link>
  )
}
