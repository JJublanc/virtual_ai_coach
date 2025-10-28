// components/controls/AIAssistant.tsx
'use client'

import { User } from 'lucide-react'

export function AIAssistant() {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-start gap-3">
        <div className="flex-1">
          <p className="text-gray-600 text-sm mb-3">
            Hello, I'm your personal trainer, let's create a workout!
          </p>
        </div>
        <div className="flex-shrink-0">
          <div className="w-12 h-12 rounded-full bg-green-200 flex items-center justify-center overflow-hidden">
            <User className="w-8 h-8 text-green-700" />
          </div>
        </div>
      </div>
    </div>
  )
}
