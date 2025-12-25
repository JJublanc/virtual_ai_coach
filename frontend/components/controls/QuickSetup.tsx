// components/controls/QuickSetup.tsx
'use client'

import { RefreshCw } from 'lucide-react'
import { useTrainingStore } from '@/store/trainingStore'
import { useComingSoon } from '@/providers/ComingSoonProvider'
import { useEffect } from 'react'

export function QuickSetup() {
  const { config, setIntensity } = useTrainingStore()
  const { openModal } = useComingSoon()

  // Ensure intensity is always set to medium_intensity
  useEffect(() => {
    if (config.intensity !== 'medium_intensity') {
      setIntensity('medium_intensity')
    }
  }, [config.intensity, setIntensity])

  const handleIntensityChange = () => {
    // Show coming soon modal
    openModal('Quick Setup')
    // Reset to medium intensity
    setIntensity('medium_intensity')
  }

  return (
    <div className="space-y-2">
      <label className="flex items-center gap-3 cursor-pointer">
        <input
          type="radio"
          name="intensity"
          value="low_impact"
          checked={config.intensity === 'low_impact'}
          onChange={handleIntensityChange}
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
          onChange={handleIntensityChange}
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
          onChange={handleIntensityChange}
          className="w-4 h-4"
        />
        <span className="text-sm">High intensity</span>
      </label>
    </div>
  )
}
