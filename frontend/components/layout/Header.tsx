// components/layout/Header.tsx
'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Dumbbell, LayoutDashboard, User } from 'lucide-react'

export function Header() {
  const pathname = usePathname()

  const navItems = [
    { name: 'Goals', href: '/goals' },
    { name: 'Plan', href: '/plan' },
    { name: 'Train', href: '/train' },
  ]

  return (
    <header className="sticky top-0 z-40 w-full border-b bg-background">
      <div className="container flex h-16 items-center space-x-4 sm:justify-between sm:space-x-0">
        <div className="flex gap-6 md:gap-10">
          <Link href="/" className="flex items-center space-x-2">
            <Dumbbell className="h-6 w-6" />
            <span className="inline-block font-bold">Personal Trainer</span>
          </Link>
          <nav className="flex gap-6">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`text-lg font-medium transition-colors hover:text-primary hidden sm:inline-block ${
                  pathname === item.href ? 'text-primary' : 'text-muted-foreground'
                }`}
              >
                {item.name}
              </Link>
            ))}
          </nav>
        </div>
        <div className="flex flex-1 items-center justify-end space-x-4">
          <nav className="flex items-center space-x-4">
            <Link href="/dashboard" className="flex items-center space-x-2">
              <LayoutDashboard className="h-5 w-5" />
              <span className="hidden sm:inline-block">Dashboard</span>
            </Link>
            <Link href="/profile" className="flex items-center space-x-2">
              <User className="h-5 w-5" />
              <span className="hidden sm:inline-block">Profile</span>
            </Link>
          </nav>
        </div>
      </div>
    </header>
  )
}
