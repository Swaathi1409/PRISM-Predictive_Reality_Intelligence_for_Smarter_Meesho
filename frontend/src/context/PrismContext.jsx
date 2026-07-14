/**
 * PrismContext.jsx — Global state for the current PRISM analysis result.
 *
 * Library: React 18 Context API (MIT) — provides the analysis result
 * to all components without prop drilling.
 */

import { createContext, useContext, useState } from 'react'

const PrismContext = createContext(null)

export function PrismProvider({ children }) {
  const [result, setResult] = useState(null)
  const [query, setQuery] = useState(null) // The input that produced the result

  const clearResult = () => {
    setResult(null)
    setQuery(null)
  }

  return (
    <PrismContext.Provider value={{ result, setResult, query, setQuery, clearResult }}>
      {children}
    </PrismContext.Provider>
  )
}

export function usePrism() {
  const ctx = useContext(PrismContext)
  if (!ctx) throw new Error('usePrism must be used within a PrismProvider')
  return ctx
}
