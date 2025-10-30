// components/controls/WarmupOptions.tsx
'use client'

import { useTrainingStore } from '@/store/trainingStore'

export function WarmupOptions() {
  const { config, toggleWarmUp, toggleCoolDown } = useTrainingStore()

  return (
    <div>
      <h4 className="text-sm text-gray-600 mb-2">warm up and streching</h4>
      <div className="space-y-2">
        <label className="flex items-center justify-between cursor-pointer">
          <span className="text-sm">Include Warm Up</span>
          <div
            className={`relative inline-block w-11 h-6 rounded-full transition-colors ${
              config.include_warm_up ? 'bg-gray-900' : 'bg-gray-300'
            }`}
            onClick={toggleWarmUp}
          >
            <span
              className={`absolute top-0.5 left-0.5 bg-white w-5 h-5 rounded-full transition-transform ${
                config.include_warm_up ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </div>
        </label>

        <label className="flex items-center justify-between cursor-pointer">
          <span className="text-sm">Include Cool Down and Streching</span>
          <div
            className={`relative inline-block w-11 h-6 rounded-full transition-colors ${
              config.include_cool_down ? 'bg-gray-900' : 'bg-gray-300'
            }`}
            onClick={toggleCoolDown}
          >
            <span
              className={`absolute top-0.5 left-0.5 bg-white w-5 h-5 rounded-full transition-transform ${
                config.include_cool_down ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </div>
        </label>
      </div>
    </div>
  )
}
