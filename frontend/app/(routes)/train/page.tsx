// app/train/page.tsx
'use client'

import { VideoPlayer } from '@/components/video/VideoPlayer'
import { ExerciseList } from '@/components/exercises/ExerciseList'
import { AIAssistant } from '@/components/controls/AIAssistant'
import { QuickSetup } from '@/components/controls/QuickSetup'
import { ParameterizedSetup } from '@/components/controls/ParameterizedSetup'
import { useTrainingStore } from '@/store/trainingStore'

export default function TrainPage() {
  const { session, player } = useTrainingStore()

  return (
    <div className="grid grid-cols-[1fr,400px] gap-6 p-6">
      {/* Colonne gauche - Vidéo + Exercices */}
      <div className="space-y-4">
        <VideoPlayer />
        <ExerciseList />
      </div>

      {/* Colonne droite - Contrôles */}
      <div className="space-y-6">
        <AIAssistant />

        <div className="space-y-2">
          <label className="text-sm text-gray-600">Training duration</label>
          <input
            type="number"
            className="w-full px-4 py-2 border rounded-lg"
            placeholder="Minutes"
          />
        </div>

        <QuickSetup />
        <ParameterizedSetup />

        <button className="w-full py-4 bg-black text-white rounded-lg font-medium hover:bg-gray-800">
          Generate training
        </button>
      </div>
    </div>
  )
}
