// hooks/useWorkoutGeneration.ts
'use client'

import { useState, useCallback } from 'react'
import { generateAutoWorkoutVideo } from '@/lib/api'
import { useTrainingStore } from '@/store/trainingStore'

interface WorkoutExercise {
  name: string
  description: string
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
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

        // ============================================================================
        // NOUVEAU WORKFLOW STREAMING PROGRESSIF - PHASE 1.3
        // ============================================================================

        // 1. Générer un ID UUID valide pour ce workout
        const workoutId = crypto.randomUUID()
        console.log('🚀 Démarrage streaming progressif pour workout:', workoutId)

        // 2. Démarrer la génération en arrière-plan
        console.log('📡 Démarrage génération en arrière-plan...')
        const startResponse = await fetch(`${apiUrl}/api/start-workout-generation`, {
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
            workout_id: workoutId,
          }),
        })

        if (!startResponse.ok) {
          const error = await startResponse.json().catch(() => ({ detail: 'Unknown error' }))
          console.error('❌ Erreur démarrage génération:', error)
          throw new Error(error.detail || `HTTP error! status: ${startResponse.status}`)
        }

        const startResult = await startResponse.json()
        console.log('✅ Génération démarrée:', startResult)

        // 3. Créer immédiatement l'URL de streaming (pas d'attente !)
        const videoUrl = `${apiUrl}/api/stream-workout/${workoutId}`
        console.log('🎥 URL de streaming créée:', videoUrl)

        // 4. Simuler une progression plus réaliste (démarrage rapide)
        setState(prev => ({ ...prev, progress: 10 }))

        const progressInterval = setInterval(() => {
          setState(prev => ({
            ...prev,
            progress: Math.min(prev.progress + 3, 85), // Progression plus lente mais continue
          }))
        }, 1000)

        // 5. Récupérer les détails du workout (exercices générés)
        let workoutExercises: WorkoutExercise[] = []
        let workoutInfo = {
          name: workoutName,
          totalDuration: totalDurationSeconds,
          exerciseCount: startResult.total_exercises || 0,
        }

        // Récupérer les exercices du workout depuis le backend
        try {
          console.log('📋 Récupération des exercices du workout...')
          const exercisesResponse = await fetch(`${apiUrl}/api/workout-exercises/${workoutId}`)
          if (exercisesResponse.ok) {
            const exercisesData = await exercisesResponse.json()
            workoutExercises = exercisesData.exercises || []
            console.log('✅ Exercices récupérés:', workoutExercises.length)
          } else {
            console.warn('⚠️ Impossible de récupérer les exercices, utilisation de données par défaut')
          }
        } catch (exerciseError) {
          console.warn('⚠️ Erreur lors de la récupération des exercices:', exerciseError)
          // Continuer sans les exercices, ce n'est pas bloquant pour le streaming
        }

        // Arrêter la progression simulée après un délai
        setTimeout(() => {
          clearInterval(progressInterval)
          setState(prev => ({ ...prev, progress: 100 }))
        }, 5000) // 5 secondes pour simuler le démarrage

        console.log('🎯 Streaming progressif configuré - la vidéo peut commencer à jouer immédiatement')

        setState({
          isGenerating: false, // ✨ IMPORTANT: On n'est plus "en génération" côté UX
          error: null,
          videoUrl, // ✨ URL directe vers le stream, pas de blob !
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
    // Note: Plus besoin de révoquer l'URL car nous utilisons maintenant
    // des URLs directes vers l'API au lieu de blob URLs
    setState({
      isGenerating: false,
      error: null,
      videoUrl: null,
      progress: 0,
      workoutExercises: [],
      workoutInfo: null,
    })
  }, [])

  return {
    ...state,
    generateVideo,
    resetVideo,
  }
}
