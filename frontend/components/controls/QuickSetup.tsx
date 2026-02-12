// components/controls/QuickSetup.tsx
'use client'

import { useTrainingStore } from '@/store/trainingStore'

export function QuickSetup() {
  const { config, setIntensity } = useTrainingStore()

  return (
    <div className="space-y-2">
      <label className="flex items-center gap-3 cursor-pointer">
        <input
          type="radio"
          name="intensity"
          value="all"
          checked={config.intensity === 'all'}
          onChange={() => setIntensity('all')}
          className="w-4 h-4"
        />
        <span className="text-sm">All levels</span>
      </label>

      <label className="flex items-center gap-3 cursor-pointer">
        <input
          type="radio"
          name="intensity"
          value="low_impact"
          checked={config.intensity === 'low_impact'}
          onChange={() => setIntensity('low_impact')}
          className="w-4 h-4"
        />
        <span className="text-sm">Low impact</span>
      </label>

      <label className="flex items-center gap-3 cursor-pointer">
        <input
          type="radio"
          name="intensity"
          value="medium_intensity"
          checked={config.intensity === 'medium_intensity'}
          onChange={() => setIntensity('medium_intensity')}
          className="w-4 h-4"
        />
        <span className="text-sm">Medium intensity</span>
      </label>

      <label className="flex items-center gap-3 cursor-pointer">
        <input
          type="radio"
          name="intensity"
          value="high_intensity"
          checked={config.intensity === 'high_intensity'}
          onChange={() => setIntensity('high_intensity')}
          className="w-4 h-4"
        />
        <span className="text-sm">High intensity</span>
      </label>
    </div>
  )
}
