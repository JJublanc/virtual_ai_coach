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
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        console.log('URL API utilisée:', `${apiUrl}/api/generate-auto-workout-video`)
        console.log('Configuration envoyée:', {
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
        })

        const response = await fetch(`${apiUrl}/api/generate-auto-workout-video`, {
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

        console.log('Réponse API reçue:', response.status, response.statusText)
        console.log('Headers de réponse:', Object.fromEntries(response.headers.entries()))

        if (!response.ok) {
          const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
          console.error('Erreur API:', error)
          throw new Error(error.detail || `HTTP error! status: ${response.status}`)
        }

        // Récupérer les headers avec les informations du workout
        const workoutId = response.headers.get('X-Workout-ID')
        console.log('Workout ID extrait des headers:', workoutId)

        // Arrêter la progression simulée
        clearInterval(progressInterval)

        // Créer une URL pour le blob vidéo
        const videoBlob = await response.blob()
        const videoUrl = URL.createObjectURL(videoBlob)

        // Récupérer les détails réels du workout depuis le backend
        let workoutExercises: WorkoutExercise[] = []
        let workoutInfo = null

        if (workoutId) {
          try {
            console.log('Récupération des détails du workout:', workoutId)
            const detailsResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/workout-details/${workoutId}`)
            console.log('Réponse détails workout:', detailsResponse.status)
            if (detailsResponse.ok) {
              const workoutDetails = await detailsResponse.json()
              console.log('Détails du workout reçus:', workoutDetails)
              workoutExercises = workoutDetails.exercises.map((ex: any) => ({
                name: ex.name,
                icon: ex.icon,
                duration: ex.duration,
                order: ex.order,
              }))
              workoutInfo = {
                name: workoutDetails.name,
                totalDuration: workoutDetails.total_duration,
                exerciseCount: workoutDetails.exercise_count,
              }
              console.log('Exercices mappés:', workoutExercises)
            } else {
              console.error('Erreur lors de la récupération des détails:', detailsResponse.status)
            }
          } catch (error) {
            console.warn('Impossible de récupérer les détails du workout:', error)
          }
        } else {
          console.warn('Aucun workout ID reçu dans les headers')
        }

        setState({
          isGenerating: false,
          error: null,
          videoUrl,
          progress: 100,
          workoutExercises,
          workoutInfo,
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
