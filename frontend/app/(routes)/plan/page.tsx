'use client'

import { useEffect } from 'react'
import { useComingSoon } from '@/providers/ComingSoonProvider'

export default function PlanPage() {
  const { openModal } = useComingSoon()

  useEffect(() => {
    openModal('Plan')
  }, [openModal])

  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-4rem)]">
      <h1 className="text-4xl font-bold">Plan Page (Coming Soon)</h1>
    </div>
  )
}
