
# Plan détaillé du Frontend Next.js - Personal Trainer

## Objectif
Créer une interface Personal Trainer permettant de :
1. Configurer une séance d'entraînement avec assistant IA
2. Visualiser la vidéo d'exercice en temps réel avec overlays
3. Paramétrer finement l'intensité, les intervalles, et les options

## Stack technique

- **Next.js 14+** (App Router)
- **TypeScript** pour type safety
- **Tailwind CSS** + **Shadcn/ui** pour les composants UI
- **React Player** ou custom video player HTML5
- **Zustand** pour state management
- **React Query (TanStack Query)** pour data fetching
- **React DnD** pour drag & drop des exercices
- **Framer Motion** pour animations
- **Vercel** pour déploiement

## Architecture Frontend basée sur le design

### Layout principal

```
┌─────────────────────────────────────────────────────────────────────┐
│  Personal Trainer    Goals  Plan  Train          ⊕ Dashboard  👤   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────┐  ┌─────────────────────────┐│
│  │                                   │  │ Hello, I'm your         ││
│  │  ┌─────────────────┐             │  │ personal trainer        ││
│  │  │ Squate       ▼  │  ○ ○ ○      │  │                         ││
│  │  │ Description...  │             │  │ [Avatar]                ││
│  │  └─────────────────┘     23      │  │                         ││
│  │         [▶]          Round 2/5   │  │ Training duration       ││
│  │                                   │  │                         ││
│  │                                   │  │ Quick setup         🔄  ││
│  │         [Progress bar 35%]    ⛶  │  │ ○ Low impact            ││
│  └──────────────────────────────────┘  │ ○ Medium intensity      ││
│                                         │ ○ High intensity        ││
│  ┌──────────────────────────────────┐  │                         ││
│  │ ::: Squate                    🗑 │  │ Parameterized       ⚙  ││
│  │ ::: Push ups                  🗑 │  │ intervals    40s/20s    ││
│  │ ::: Burpees                   🗑 │  │ ●───────────────────●   ││
│  │ ::: abs                       🗑 │  │                         ││
│  │ ::: Mountain climber          🗑 │  │ 🔁 No repeat      ⚫    ││
│  └──────────────────────────────────┘  │ 🤸 No jump        ⚫    ││
│                                         │                         ││
│                                         │ exercise intensity      ││
│                                         │ ☑ Easy ☑ Medium ☑ Hard ││
│                                         │                         ││
│                                         │ warm up and streching   ││
│                                         │ ☑ Include Warm Up       ││
│                                         │ ☑ Include Cool Down     ││
│                                         │                         ││
│                                         │ IA assisted         🔄  ││
│                                         │ [Description IA...]     ││
│                                         │                         ││
│                                         │ [Generate training]     ││
│                                         └─────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

### Structure de fichiers

```
app/
├── (routes)/
│   ├── layout.tsx                  # Layout global avec header
│   ├── page.tsx                    # Redirection vers /train
│   ├── goals/
│   │   └── page.tsx                # Page Goals (à venir)
│   ├── plan/
│   │   └── page.tsx                # Page Plan (à venir)
│   └── train/
│       └── page.tsx                # Page principale Train (screenshot)
│
├── components/
│   ├── layout/
│   │   ├── Header.tsx              # Header avec navigation
│   │   └── MainLayout.tsx          # Layout principal 2 colonnes
│   │
│   ├── video/
│   │   ├── VideoPlayer.tsx         # Player vidéo principal avec overlays
│   │   ├── ExerciseDescription.tsx # Panel description exercice
│   │   ├── RoundIndicator.tsx      # Indicateur "Round 2/5"
│   │   ├── TimerCircle.tsx         # Timer circulaire
│   │   └── ProgressBar.tsx         # Barre de progression 35%
│   │
│   ├── exercises/
│   │   ├── ExerciseList.tsx        # Liste drag & drop exercices
│   │   ├── ExerciseCard.tsx        # Card exercice avec drag handle
│   │   └── ExerciseIcon.tsx        # Icône exercice
│   │
│   └── controls/
│       ├── AIAssistant.tsx         # Panel assistant IA
│       ├── QuickSetup.tsx          # Sélection intensité rapide
│       ├── ParameterizedSetup.tsx  # Paramètres avancés
│       ├── IntervalSlider.tsx      # Slider intervalles
│       ├── ToggleSwitch.tsx        # Toggle No repeat/No jump
│       ├── IntensityCheckboxes.tsx # Checkboxes Easy/Medium/Hard
│       └── WarmupOptions.tsx       # Options échauffement
│
├── lib/
│   ├── api.ts                      # Client API
│   ├── types.ts                    # Types TypeScript
│   └── utils.ts                    # Utilitaires
│
├── hooks/
│   ├── useTraining.ts              # Hook pour gestion séance
│   ├── useExercises.ts             # Hook pour exercices
│   ├── useVideoPlayer.ts           # Hook pour contrôle vidéo
│   └── useAIGeneration.ts          # Hook pour génération IA
│
└── store/
    └── trainingStore.ts            # Zustand store pour état global
```

## Schéma de données ajusté

### Types TypeScript

```typescript
// lib/types.ts

export interface Exercise {
  id: string
  name: string
  description: string
  icon: string // Nom de l'icône ou chemin SVG
  video_path: string
  thumbnail?: string
  default_duration: number // en secondes
  categories: ('cardio' | 'strength' | 'flexibility')[]
  difficulty: 'easy' | 'medium' | 'hard'
  has_jump: boolean
  metadata?: {
    muscles_targeted?: string[]
    equipment_needed?: string[]
  }
}

export interface WorkoutExercise {
  exercise: Exercise
  order: number
  custom_duration?: number // Override si différent du default
}

export type IntensityLevel = 'low_impact' | 'medium_intensity' | 'high_intensity'

export interface IntervalConfig {
  work_time: number // Temps d'activité en secondes (ex: 40)
  rest_time: number // Temps de repos en secondes (ex: 20)
}

export interface WorkoutConfig {
  // Quick Setup
  intensity: IntensityLevel
  
  // Parameterized
  intervals: IntervalConfig
  no_repeat: boolean
  no_jump: boolean
  
  // Exercise Intensity (peut sélectionner plusieurs)
  intensity_levels: ('easy' | 'medium' | 'hard')[]
  
  // Warm up and Stretching
  include_warm_up: boolean
  include_cool_down: boolean
  
  // Training duration (minutes)
  target_duration?: number
}

export interface TrainingSession {
  id: string
  exercises: WorkoutExercise[]
  config: WorkoutConfig
  total_duration: number // Calculé
  rounds: number // Nombre de tours calculé
  current_round?: number // Pour tracking pendant exercice
  current_exercise_index?: number
  current_time?: number // Temps écoulé en secondes
  status: 'draft' | 'ready' | 'in_progress' | 'completed'
}

export interface AIGenerationRequest {
  user_input: string // Texte libre de l'utilisateur
  config: Partial<WorkoutConfig> // Paramètres déjà sélectionnés
}

export interface AIGenerationResponse {
  exercises: WorkoutExercise[]
  suggested_config: WorkoutConfig
  explanation: string
}

export interface VideoPlayerState {
  is_playing: boolean
  current_time: number
  total_duration: number
  current_exercise: WorkoutExercise | null
  current_round: number
  progress_percentage: number
}
```

### Zustand Store

```typescript
// store/trainingStore.ts
import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

interface TrainingStore {
  // État de la séance
  session: TrainingSession | null
  
  // Configuration
  config: WorkoutConfig
  
  // État du player
  player: VideoPlayerState
  
  // Actions - Exercices
  addExercise: (exercise: Exercise) => void
  removeExercise: (exerciseId: string) => void
  reorderExercises: (startIndex: number, endIndex: number) => void
  updateExerciseDuration: (exerciseId: string, duration: number) => void
  
  // Actions - Configuration
  setIntensity: (intensity: IntensityLevel) => void
  setIntervals: (intervals: IntervalConfig) => void
  toggleNoRepeat: () => void
  toggleNoJump: () => void
  toggleIntensityLevel: (level: 'easy' | 'medium' | 'hard') => void
  toggleWarmUp: () => void
  toggleCoolDown: () => void
  setTargetDuration: (minutes: number) => void
  
  // Actions - Séance
  generateTraining: (aiRequest?: AIGenerationRequest) => Promise<void>
  startTraining: () => void
  pauseTraining: () => void
  resumeTraining: () => void
  nextExercise: () => void
  previousExercise: () => void
  
  // Actions - Player
  updatePlayerState: (state: Partial<VideoPlayerState>) => void
  
  // Utilitaires
  reset: () => void
  calculateTotalDuration: () => number
}

const initialConfig: WorkoutConfig = {
  intensity: 'medium_intensity',
  intervals: { work_time: 40, rest_time: 20 },
  no_repeat: false,
  no_jump: false,
  intensity_levels: ['easy', 'medium', 'hard'],
  include_warm_up: true,
  include_cool_down: true,
}

export const useTrainingStore = create<TrainingStore>()(
  devtools(
    persist(
      (set, get) => ({
        session: null,
        config: initialConfig,
        player: {
          is_playing: false,
          current_time: 0,
          total_duration: 0,
          current_exercise: null,
          current_round: 1,
          progress_percentage: 0,
        },

        // Implémentation des actions...
        addExercise: (exercise) =>
          set((state) => {
            const newExercise: WorkoutExercise = {
              exercise,
              order: state.session?.exercises.length || 0,
            }
            return {
              session: {
                ...state.session!,
                exercises: [...(state.session?.exercises || []), newExercise],
              },
            }
          }),

        removeExercise: (exerciseId) =>
          set((state) => ({
            session: {
              ...state.session!,
              exercises: state.session!.exercises.filter(
                (e) => e.exercise.id !== exerciseId
              ),
            },
          })),

        reorderExercises: (startIndex, endIndex) =>
          set((state) => {
            const exercises = [...state.session!.exercises]
            const [removed] = exercises.splice(startIndex, 1)
            exercises.splice(endIndex, 0, removed)
            
            // Réindexer
            exercises.forEach((ex, idx) => {
              ex.order = idx
            })
            
            return { session: { ...state.session!, exercises } }
          }),

        setIntensity: (intensity) =>
          set((state) => ({
            config: { ...state.config, intensity },
          })),

        setIntervals: (intervals) =>
          set((state) => ({
            config: { ...state.config, intervals },
          })),

        toggleNoRepeat: () =>
          set((state) => ({
            config: { ...state.config, no_repeat: !state.config.no_repeat },
          })),

        toggleNoJump: () =>
          set((state) => ({
            config: { ...state.config, no_jump: !state.config.no_jump },
          })),

        toggleIntensityLevel: (level) =>
          set((state) => {
            const levels = state.config.intensity_levels.includes(level)
              ? state.config.intensity_levels.filter((l) => l !== level)
              : [...state.config.intensity_levels, level]
            return { config: { ...state.config, intensity_levels: levels } }
          }),

        toggleWarmUp: () =>
          set((state) => ({
            config: {
              ...state.config,
              include_warm_up: !state.config.include_warm_up,
            },
          })),

        toggleCoolDown: () =>
          set((state) => ({
            config: {
              ...state.config,
              include_cool_down: !state.config.include_cool_down,
            },
          })),

        setTargetDuration: (minutes) =>
          set((state) => ({
            config: { ...state.config, target_duration: minutes },
          })),

        generateTraining: async (aiRequest) => {
          // Appel API pour génération (IA ou logique simple)
          // TODO: Implémenter
        },

        startTraining: () =>
          set((state) => ({
            session: { ...state.session!, status: 'in_progress' },
            player: { ...state.player, is_playing: true },
          })),

        updatePlayerState: (playerState) =>
          set((state) => ({
            player: { ...state.player, ...playerState },
          })),

        calculateTotalDuration: () => {
          const state = get()
          if (!state.session) return 0
          
          const { exercises } = state.session
          const { intervals, include_warm_up, include_cool_down } = state.config
          
          let total = 0
          
          // Warm up
          if (include_warm_up) total += 300 // 5 min
          
          // Exercices
          exercises.forEach((we) => {
            const duration = we.custom_duration || we.exercise.default_duration
            total += duration + intervals.rest_time
          })
          
          // Cool down
          if (include_cool_down) total += 300 // 5 min
          
          return total
        },

        reset: () =>
          set({
            session: null,
            config: initialConfig,
            player: {
              is_playing: false,
              current_time: 0,
              total_duration: 0,
              current_exercise: null,
              current_round: 1,
              progress_percentage: 0,
            },
          }),
      }),
      {
        name: 'training-storage',
      }
    )
  )
)
```

## Composants principaux

### Page Train

```tsx
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
```

### VideoPlayer avec overlays

```tsx
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
  const videoRef = useRef<HTMLVideoElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const { player, session } = useTrainingStore()

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause()
      } else {
        videoRef.current.play()
      }
      setIsPlaying(!isPlaying)
    }
  }

  const toggleFullscreen = () => {
    if (videoRef.current) {
      videoRef.current.requestFullscreen()
    }
  }

  const currentExercise = player.current_exercise

  return (
    <div className="relative bg-gray-900 rounded-2xl overflow-hidden aspect-video">
      {/* Video */}
      <video
        ref={videoRef}
        className="w-full h-full object-cover"
        src={currentExercise?.exercise.video_path}
      />

      {/* Overlays */}
      <div className="absolute inset-0 pointer-events-none">
        {/* Description exercice - Top left */}
        <div className="absolute top-4 left-4 pointer-events-auto">
          <ExerciseDescription exercise={currentExercise?.exercise} />
        </div>

        {/* Indicateurs de progression - Top right */}
        <div className="absolute top-4 right-4 flex flex-col items-center gap-2">
          {/* Petits points de progression */}
          <div className="flex gap-2">
            {[1, 2, 3].map((dot) => (
              <div
                key={dot}
                className="w-2 h-2 rounded-full bg-white/50"
              />
            ))}
          </div>
          
          <TimerCircle seconds={player.current_time} />
          <RoundIndicator current={player.current_round} total={session?.rounds || 5} />
        </div>

        {/* Bouton Play/Pause - Centre */}
        <button
          onClick={togglePlay}
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 
                     w-20 h-20 rounded-full border-4 border-white/30 
                     flex items-center justify-center pointer-events-auto
                     hover:border-white/50 transition"
        >
          {isPlaying ? (
            <Pause className="w-8 h-8 text-white" />
          ) : (
            <Play className="w-8 h-8 text-white ml-1" />
          )}
        </button>

        {/* Barre de progression - Bottom */}
        <div className="absolute bottom-4 left-4 right-16 pointer-events-auto">
          <ProgressBar percentage={player.progress_percentage} />
        </div>

        {/* Bouton fullscreen - Bottom right */}
        <button
          onClick={toggleFullscreen}
          className="absolute bottom-4 right-4 p-2 hover:bg-white/10 rounded-lg pointer-events-auto"
        >
          <Maximize2 className="w-6 h-6 text-white" />
        </button>
      </div>
    </div>
  )
}
```

### ExerciseList avec drag & drop

```tsx
// components/exercises/ExerciseList.tsx
'use client'

import { DndContext, closestCenter, DragEndEvent } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { ExerciseCard } from './ExerciseCard'
import { useTrainingStore } from '@/store/trainingStore'

export function ExerciseList() {
  const { session, reorderExercises } = useTrainingStore()

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    
    if (active.id !== over?.id) {
      const oldIndex = session!.exercises.findIndex(
        (e) => e.exercise.id === active.id
      )
      const newIndex = session!.exercises.findIndex(
        (e) => e.exercise.id === over?.id
      )
      
      reorderExercises(oldIndex, newIndex)
    }
  }

  if (!session?.exercises.length) {
    return (
      <div className="text-center py-12 text-gray-400">
        Aucun exercice sélectionné. Utilisez l'assistant IA ou ajoutez des exercices manuellement.
      </div>
    )
  }

  return (
    <DndContext collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <SortableContext
        items={session.exercises.map((e) => e.exercise.id)}
        strategy={verticalListSortingStrategy}
      >
        <div className="space-y-2">
          {session.exercises.map((workoutExercise) => (
            <ExerciseCard
              key={workoutExercise.exercise.id}
              workoutExercise={workoutExercise}
            />
          ))}
        </div>
      </SortableContext>
    </DndContext>
  )
}
```

### ExerciseCard

```tsx
// components/exercises/ExerciseCard.tsx
'use client'

import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical, Trash2 } from 'lucide-react'
import { WorkoutExercise } from '@/lib/types'
import { useTrainingStore } from '@/store/trainingStore'
import { ExerciseIcon } from './ExerciseIcon'

interface ExerciseCardProps {
  workoutExercise: WorkoutExercise
}

export function ExerciseCard({ workoutExercise }: ExerciseCardProps) {
  const { exercise } = workoutExercise
  const { removeExercise } = useTrainingStore()

  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: exercise.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="flex items-center gap-3 px-4 py-3 bg-white border border-gray-200 
                 rounded-lg hover:shadow-md transition"
    >
      {/* Drag handle */}
      <button
        {...attributes}
        {...listeners}
        className="cursor-grab active:cursor-grabbing text-gray-400"
      >
        <GripVertical className="w-5 h-5" />
      </button>

      {/* Icône exercice */}
      <ExerciseIcon icon={exercise.icon} />

      {/* Nom */}
      <span className="flex-1 font-medium">{exercise.name}</span>

      {/* Bouton supprimer */}
      <button
        onClick={() => removeExercise(exercise.id)}
        className="p-2 hover:bg-red-50 rounded-lg text-gray-400 hover:text-red-600"
      >
        <Trash2 className="w-5 h-5" />
      </button>
    </div>
  )
}
```

### QuickSetup

```tsx
// components/controls/QuickSetup.tsx
'use client'

import { RefreshCw } from 'lucide-react'
import { useTrainingStore } from '@/store/trainingStore'
import { IntensityLevel } from '@/lib/types'

export function QuickSetup() {
  const { config, setIntensity } = useTrainingStore()

  const intensities: { value: IntensityLevel; label: string }[] = [
    { value: 'low_impact', label: 'Low impact' },
    { value: 'medium_intensity', label: 'Medium intensity' },
    { value: 'high_intensity', label: 'High intensity' },
  ]

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-medium">Quick setup</h3>
        <button className="p-1 hover:bg-gray-100 rounded">
          <RefreshCw className="w-4 h-4 text-gray-400" />
        </button>
      </div>

      <div className="space-y-2">
        {intensities.map(({ value, label }) => (
          <label key={value} className="flex items-center gap-3 cursor-pointer">
            <input
              type="radio"
              name="intensity"
              checked={config.intensity === value}
              onChange={() => setIntensity(value)}
              className="w-4 h-4"
            />
            <span className="text-sm">{label}</span>
          </label>
        ))}
      </div>
    </div>
  )
}
```

### IntervalSlider

```tsx
// components/controls/IntervalSlider.tsx
'use client'

import { useTrainingStore } from '@/store/trainingStore'

export function IntervalSlider() {
  const { config, setIntervals } = useTrainingStore()
  const { work_time, rest_time } = config.intervals

  const handleWorkTimeChange = (value: number) => {
    setIntervals({ work_time: value, rest_time })
  }

  const handleRestTimeChange = (value: number) => {
    setIntervals({ work_time, rest_time: value })
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-sm">
        <span>intervals</span>
        <span className="font-mono">{work_time}s/{rest_time}s</span>
      </div>

      <div className="space-y-2">
        {/* Work time slider */}
        <input
          type="range"
          min="10"
          max="60"
          step="5"
          value={work_time}
          onChange={(e) => handleWorkTimeChange(Number(e.target.value))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
        />

        <p className="text-xs text-gray-500">
          activity time / rest time for each exercise
        </p>
      </div>
    </div>
  )
}
```

## API Integration

```typescript
// lib/api.ts

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function generateTrainingWithAI(
  request: AIGenerationRequest
): Promise<AIGenerationResponse> {
  const response = await fetch(`${API_BASE_URL}/api/generate-training`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })

  if (!response.ok) throw new Error('Failed to generate training')
  return response.json()
}

export async function getWorkout