// components/video/VideoPlayer.tsx
'use client'

import { Play, Maximize2 } from 'lucide-react'

export function VideoPlayer() {
  return (
    <div className="relative bg-gray-900 rounded-lg overflow-hidden aspect-video">
      {/* Video background placeholder */}
      <div className="absolute inset-0 bg-gradient-to-br from-gray-800 to-gray-900">
        {/* Exercise description overlay - top left */}
        <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg p-4 max-w-xs">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-bold text-lg">Squate</h3>
            <button className="text-gray-600">▼</button>
          </div>
          <p className="text-sm text-gray-600 leading-relaxed">
            stand with your feet shoulder-width apart, keep your chest up, and tighten your core. Push your hips back as if sitting in a chair, lower until your thighs are parallel to the ground, then drive through your heels to stand back up.
          </p>
        </div>

        {/* Timer circle - top right */}
        <div className="absolute top-4 right-4">
          <div className="relative w-24 h-24">
            <svg className="w-24 h-24 transform -rotate-90">
              <circle
                cx="48"
                cy="48"
                r="40"
                stroke="rgba(255,255,255,0.2)"
                strokeWidth="8"
                fill="none"
              />
              <circle
                cx="48"
                cy="48"
                r="40"
                stroke="#4ade80"
                strokeWidth="8"
                fill="none"
                strokeDasharray={`${2 * Math.PI * 40}`}
                strokeDashoffset={`${2 * Math.PI * 40 * 0.5}`}
                className="transition-all duration-1000"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-white text-2xl font-bold">23</span>
            </div>
          </div>
        </div>

        {/* Round indicator */}
        <div className="absolute top-32 right-4 bg-white/90 backdrop-blur-sm rounded-lg px-4 py-2">
          <span className="text-sm font-medium">Round 2/5</span>
        </div>

        {/* Play button - center */}
        <div className="absolute inset-0 flex items-center justify-center">
          <button className="w-20 h-20 flex items-center justify-center bg-white/20 backdrop-blur-sm rounded-full border-4 border-white/50 hover:bg-white/30 transition-colors">
            <Play className="w-10 h-10 text-white ml-1" fill="white" />
          </button>
        </div>

        {/* Progress bar - bottom */}
        <div className="absolute bottom-0 left-0 right-0 p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-white text-sm font-medium">35%</span>
            <button className="text-white hover:text-gray-300 transition-colors">
              <Maximize2 className="w-5 h-5" />
            </button>
          </div>
          <div className="h-2 bg-white/20 rounded-full overflow-hidden">
            <div className="h-full bg-green-400 rounded-full" style={{ width: '35%' }}></div>
          </div>
        </div>
      </div>
    </div>
  )
}
