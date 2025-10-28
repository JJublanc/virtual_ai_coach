// components/controls/WarmupOptions.tsx
'use client'

import { useTrainingStore } from '@/store/trainingStore'

export function WarmupOptions() {
  const { config, toggleWarmUp, toggleCoolDown } = useTrainingStore()

  return (
    <div>
      <h4 className="text-sm text-gray-600 mb-2">warm up and streching</h4>
      <div className="space-y-2">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={config.include_warm_up}
            onChange={toggleWarmUp}
            className="w-4 h-4 rounded border-gray-300"
          />
          <span className="text-sm">Include Warm Up</span>
        </label>

        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={config.include_cool_down}
            onChange={toggleCoolDown}
            className="w-4 h-4 rounded border-gray-300"
          />
          <span className="text-sm">Include Cool Down and Streching</span>
        </label>
      </div>
    </div>
  )
}
