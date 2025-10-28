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
    <header className="sticky top-0 z-40 w-full border-b bg-white">
      <div className="container mx-auto flex h-16 items-center justify-between px-6">
        {/* Logo */}
        <Link href="/" className="flex items-center space-x-2">
          <span className="text-xl font-bold">Personal Trainer</span>
        </Link>

        {/* Navigation centrale */}
        <nav className="flex gap-8">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`text-base font-medium transition-colors hover:text-gray-900 ${
                pathname === item.href ? 'text-gray-900' : 'text-gray-600'
              }`}
            >
              {item.name}
            </Link>
          ))}
        </nav>

        {/* Dashboard et Profile */}
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard"
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-full hover:bg-gray-50 transition-colors"
          >
            <LayoutDashboard className="h-4 w-4" />
            <span className="text-sm font-medium">Dashboard</span>
          </Link>
          <Link
            href="/profile"
            className="flex items-center justify-center w-10 h-10 bg-gray-100 rounded-full hover:bg-gray-200 transition-colors"
          >
            <User className="h-5 w-5 text-gray-700" />
          </Link>
        </div>
      </div>
    </header>
  )
}
