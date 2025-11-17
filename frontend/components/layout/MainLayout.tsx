// components/layout/MainLayout.tsx
import React from 'react'

interface MainLayoutProps {
  children: React.ReactNode
}

export function MainLayout({ children }: MainLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col">
      <main className="flex-1">{children}</main>
    </div>
  )
}
