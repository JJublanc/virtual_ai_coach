// components/controls/IntensityCheckboxes.tsx
'use client'

import { useTrainingStore } from '@/store/trainingStore'

export function IntensityCheckboxes() {
  const { config, toggleIntensityLevel } = useTrainingStore()

  return (
    <div>
      <h4 className="text-sm text-gray-600 mb-2">exercise intensity</h4>
      <div className="flex gap-3">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={config.intensity_levels.includes('easy')}
            onChange={() => toggleIntensityLevel('easy')}
            className="w-4 h-4 rounded border-gray-300"
          />
          <span className="text-sm">Easy</span>
        </label>

        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={config.intensity_levels.includes('medium')}
            onChange={() => toggleIntensityLevel('medium')}
            className="w-4 h-4 rounded border-gray-300"
          />
          <span className="text-sm">Medium</span>
        </label>

        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={config.intensity_levels.includes('hard')}
            onChange={() => toggleIntensityLevel('hard')}
            className="w-4 h-4 rounded border-gray-300"
          />
          <span className="text-sm">Hard</span>
        </label>
      </div>
    </div>
  )
}
