// components/controls/ParameterizedSetup.tsx
'use client'

import { Settings, Ban, ArrowUp } from 'lucide-react'
import { useTrainingStore } from '@/store/trainingStore'
import { IntensityCheckboxes } from './IntensityCheckboxes'
import { WarmupOptions } from './WarmupOptions'
import { useComingSoon } from '@/providers/ComingSoonProvider'

export function ParameterizedSetup() {
  const { config, setIntervals, toggleNoRepeat, toggleNoJump } = useTrainingStore()
  const { openModal } = useComingSoon()

  const handleWorkTimeChange = (value: number) => {
    const restTime = 60 - value
    setIntervals({ work_time: value, rest_time: restTime })
  }

  return (
    <div className="space-y-4">
      {/* Intervals - Coming Soon Wrapper */}
      <div className="relative">
        <div className="pointer-events-none opacity-90">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">intervals</span>
            <span className="text-sm font-medium">{config.intervals.work_time}s/{config.intervals.rest_time}s</span>
          </div>
          <div className="relative">
            <input
              type="range"
              min="10"
              max="60"
              value={config.intervals.work_time}
              disabled
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">
            activity time / rest time for each exercise
          </p>
        </div>
        <div
          onClick={() => openModal('Advanced Intervals')}
          className="absolute inset-0 cursor-pointer bg-white/30 hover:bg-white/40 transition-colors rounded-lg"
        />
      </div>

      {/* Toggles - Coming Soon Wrapper */}
      <div className="relative">
        <div className="pointer-events-none opacity-90 space-y-2">
          <label className="flex items-center justify-between cursor-pointer">
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 flex items-center justify-center">
                <Ban className="w-5 h-5 text-gray-600" />
              </div>
              <span className="text-sm">No repeat</span>
            </div>
            <div
              className={`relative inline-block w-11 h-6 rounded-full transition-colors ${
                config.no_repeat ? 'bg-gray-900' : 'bg-gray-300'
              }`}
            >
              <span
                className={`absolute top-0.5 left-0.5 bg-white w-5 h-5 rounded-full transition-transform ${
                  config.no_repeat ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </div>
          </label>

          <label className="flex items-center justify-between cursor-pointer">
            <div className="flex items-center gap-2">
              <div className="w-5 h-5 flex items-center justify-center">
                <ArrowUp className="w-5 h-5 text-gray-600" strokeWidth={2.5} />
              </div>
              <span className="text-sm">No jump</span>
            </div>
            <div
              className={`relative inline-block w-11 h-6 rounded-full transition-colors ${
                config.no_jump ? 'bg-gray-900' : 'bg-gray-300'
              }`}
            >
              <span
                className={`absolute top-0.5 left-0.5 bg-white w-5 h-5 rounded-full transition-transform ${
                  config.no_jump ? 'translate-x-5' : 'translate-x-0'
                }`}
              />
            </div>
          </label>
        </div>
        <div
          onClick={() => openModal('Exercise Filters')}
          className="absolute inset-0 cursor-pointer bg-white/30 hover:bg-white/40 transition-colors rounded-lg"
        />
      </div>

      {/* Intensity Checkboxes - Coming Soon Wrapper */}
      <div className="relative">
        <div className="pointer-events-none opacity-90">
          <IntensityCheckboxes />
        </div>
        <div
          onClick={() => openModal('Custom Intensity')}
          className="absolute inset-0 cursor-pointer bg-white/30 hover:bg-white/40 transition-colors rounded-lg"
        />
      </div>

      {/* Warmup Options - Coming Soon Wrapper */}
      <div className="relative">
        <div className="pointer-events-none opacity-90">
          <WarmupOptions />
        </div>
        <div
          onClick={() => openModal('Advanced Warmup')}
          className="absolute inset-0 cursor-pointer bg-white/30 hover:bg-white/40 transition-colors rounded-lg"
        />
      </div>
    </div>
  )
}
