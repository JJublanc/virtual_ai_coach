// providers/ComingSoonProvider.tsx
'use client'

import { createContext, useContext, ReactNode } from 'react'
import { ComingSoonModal } from '@/components/modals/ComingSoonModal'
import { useComingSoonModal } from '@/hooks/useComingSoonModal'
import { FeatureName } from '@/lib/types'

interface ComingSoonContextType {
  openModal: (feature: FeatureName, description?: string) => void
  closeModal: () => void
  isOpen: boolean
}

const ComingSoonContext = createContext<ComingSoonContextType | undefined>(undefined)

export function ComingSoonProvider({ children }: { children: ReactNode }) {
  const { isOpen, featureName, featureDescription, openModal, closeModal } = useComingSoonModal()

  return (
    <ComingSoonContext.Provider value={{ openModal, closeModal, isOpen }}>
      {children}
      <ComingSoonModal
        isOpen={isOpen}
        onClose={closeModal}
        featureName={featureName}
        featureDescription={featureDescription}
      />
    </ComingSoonContext.Provider>
  )
}

export function useComingSoon() {
  const context = useContext(ComingSoonContext)
  if (context === undefined) {
    throw new Error('useComingSoon must be used within a ComingSoonProvider')
  }
  return context
}
