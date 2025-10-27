// components/video/VideoPlayer.tsx
'use client'

import { useRef, useEffect, useState } from 'react'
import { Play, Pause, Maximize2 } from 'lucide-react'
import { ExerciseDescription } from './ExerciseDescription'
import { TimerCircle } from './TimerCircle'
import { RoundIndicator } from './RoundIndicator'
import { ProgressBar } from './ProgressBar'
import { useTrainingStore } from '@/store/trainingStore'

export function VideoPlayer() {
  return (
    <div>
      <h2>Video Player</h2>
    </div>
  )
}
