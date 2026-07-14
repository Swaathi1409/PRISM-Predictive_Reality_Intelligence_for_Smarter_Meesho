/**
 * usePrismAnalysis.js — React Query wrapper for the PRISM analyze API call.
 *
 * Library: @tanstack/react-query (MIT) — handles loading, error, and success
 * states declaratively, eliminating manual useState/useEffect chains.
 */

import { useMutation } from '@tanstack/react-query'
import { analyzePrism } from '../utils/api'

export function usePrismAnalysis() {
  return useMutation({
    mutationFn: analyzePrism,
    onError: (error) => {
      console.error('[usePrismAnalysis] Error:', error.message)
    },
  })
}
