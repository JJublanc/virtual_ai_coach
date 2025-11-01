// hooks/useWorkoutGeneration.ts
'use client'

import { useState, useCallback } from 'react'
import { generateAutoWorkoutVideo } from '@/lib/api'
import { useTrainingStore } from '@/store/trainingStore'

interface WorkoutExercise {
  name: string
  icon: string
  duration: number
  order: number
}

interface GenerationState {
  isGenerating: boolean
  error: string | null
  videoUrl: string | null
  progress: number
  workoutExercises: WorkoutExercise[]
  workoutInfo: {
    name: string
    totalDuration: number
    exerciseCount: number
  } | null
}

export function useWorkoutGeneration() {
  const { config } = useTrainingStore()
  const [state, setState] = useState<GenerationState>({
    isGenerating: false,
    error: null,
    videoUrl: null,
    progress: 0,
    workoutExercises: [],
    workoutInfo: null,
  })

  const generateVideo = useCallback(
    async (trainingDuration: number, workoutName: string = 'Mon Entraînement') => {
      setState({
        isGenerating: true,
        error: null,
        videoUrl: null,
        progress: 0,
        workoutExercises: [],
        workoutInfo: null,
      })

      try {
        // Convertir la durée de minutes en secondes
        const totalDurationSeconds = trainingDuration * 60

        // Simuler la progression (car le streaming ne fournit pas de progression réelle)
        const progressInterval = setInterval(() => {
          setState(prev => ({
            ...prev,
            progress: Math.min(prev.progress + 5, 90),
          }))
        }, 500)

        // Appeler l'API pour générer la vidéo
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/generate-auto-workout-video`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            config: {
              intensity: config.intensity,
              intervals: config.intervals,
              no_repeat: config.no_repeat,
              no_jump: config.no_jump,
              exercice_intensity_levels: config.intensity_levels,
              include_warm_up: config.include_warm_up,
              include_cool_down: config.include_cool_down,
              target_duration: config.target_duration,
            },
            total_duration: totalDurationSeconds,
            name: workoutName,
          }),
        })

        if (!response.ok) {
          const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
          throw new Error(error.detail || `HTTP error! status: ${response.status}`)
        }

        // Récupérer les headers avec les informations du workout
        const workoutId = response.headers.get('X-Workout-ID')
        const exerciseCount = parseInt(response.headers.get('X-Exercise-Count') || '0')

        // Arrêter la progression simulée
        clearInterval(progressInterval)

        // Créer une URL pour le blob vidéo
        const videoBlob = await response.blob()
        const videoUrl = URL.createObjectURL(videoBlob)

        // Générer une séquence d'exercices simulée basée sur la configuration
        // En attendant d'avoir l'API qui retourne la séquence réelle
        const mockExercises = generateMockExerciseSequence(exerciseCount, totalDurationSeconds)

        setState({
          isGenerating: false,
          error: null,
          videoUrl,
          progress: 100,
          workoutExercises: mockExercises,
          workoutInfo: {
            name: workoutName,
            totalDuration: totalDurationSeconds,
            exerciseCount,
          },
        })

        return videoUrl
      } catch (error) {
        setState({
          isGenerating: false,
          error: error instanceof Error ? error.message : 'Erreur lors de la génération',
          videoUrl: null,
          progress: 0,
          workoutExercises: [],
          workoutInfo: null,
        })
        throw error
      }
    },
    [config]
  )

  const resetVideo = useCallback(() => {
    if (state.videoUrl) {
      URL.revokeObjectURL(state.videoUrl)
    }
    setState({
      isGenerating: false,
      error: null,
      videoUrl: null,
      progress: 0,
      workoutExercises: [],
      workoutInfo: null,
    })
  }, [state.videoUrl])

  return {
    ...state,
    generateVideo,
    resetVideo,
  }
}

// Fonction utilitaire pour générer une séquence d'exercices simulée
function generateMockExerciseSequence(exerciseCount: number, totalDuration: number): WorkoutExercise[] {
  const exerciseTemplates = [
    { name: 'Push-ups', icon: '💪' },
    { name: 'Air Squat', icon: '🦵' },
    { name: 'Plank', icon: '🏋️' },
    { name: 'Burpees', icon: '🔥' },
    { name: 'Mountain Climber', icon: '⛰️' },
    { name: 'Jumping Jacks', icon: '⚡' },
    { name: 'Lunges', icon: '🚶' },
    { name: 'High Knees', icon: '🏃' },
  ]

  const exercises: WorkoutExercise[] = []
  const avgDuration = Math.floor(totalDuration / exerciseCount)

  for (let i = 0; i < exerciseCount; i++) {
    const template = exerciseTemplates[i % exerciseTemplates.length]
    exercises.push({
      name: template.name,
      icon: template.icon,
      duration: avgDuration,
      order: i + 1,
    })
  }

  return exercises
}
