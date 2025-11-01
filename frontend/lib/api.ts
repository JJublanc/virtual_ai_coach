// lib/api.ts

import { WorkoutConfig } from './types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface GenerateAutoWorkoutRequest {
  config: WorkoutConfig
  total_duration: number
  name: string
}

/**
 * Génère automatiquement un workout et télécharge la vidéo
 *
 * @param request Configuration du workout à générer
 * @returns Promise<Blob> La vidéo MP4 générée
 */
export async function generateAutoWorkoutVideo(
  request: GenerateAutoWorkoutRequest
): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/api/generate-auto-workout-video`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      config: {
        intensity: request.config.intensity,
        intervals: request.config.intervals,
        no_repeat: request.config.no_repeat,
        no_jump: request.config.no_jump,
        exercice_intensity_levels: request.config.intensity_levels,
        include_warm_up: request.config.include_warm_up,
        include_cool_down: request.config.include_cool_down,
        target_duration: request.config.target_duration,
      },
      total_duration: request.total_duration,
      name: request.name,
    }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP error! status: ${response.status}`)
  }

  // Récupérer les headers personnalisés
  const workoutId = response.headers.get('X-Workout-ID')
  const exerciseCount = response.headers.get('X-Exercise-Count')

  console.log('Workout generated:', { workoutId, exerciseCount })

  return await response.blob()
}

/**
 * Télécharge un blob en tant que fichier
 */
export function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  window.URL.revokeObjectURL(url)
  document.body.removeChild(a)
}
