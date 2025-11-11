'use client'

import { useEffect } from 'react'
import { useComingSoon } from '@/providers/ComingSoonProvider'

export default function GoalsPage() {
  const { openModal } = useComingSoon()

  useEffect(() => {
    openModal('Goals')
  }, [openModal])

  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-4rem)]">
      <h1 className="text-4xl font-bold">Goals Page (Coming Soon)</h1>
    </div>
  )
}
