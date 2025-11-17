'use client'

import { useState, useEffect } from 'react'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Exercise {
  id: string
  name: string
  description: string
  icon: string
  default_duration: number
  video_url: string
  muscle_groups: string[]
  difficulty: string
  equipment: string[]
}

export function useExercises() {
  const [exercises, setExercises] = useState<Exercise[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchExercises = async () => {
      try {
        setLoading(true)
        const response = await fetch(`${API_BASE_URL}/api/exercises`)

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const data = await response.json()
        setExercises(data || [])
        setError(null)
      } catch (err) {
        console.error('Erreur lors du chargement des exercices:', err)
        setError(err instanceof Error ? err.message : 'Erreur inconnue')
        setExercises([])
      } finally {
        setLoading(false)
      }
    }

    fetchExercises()
  }, [])

  return {
    exercises,
    loading,
    error,
    refetch: () => {
      setLoading(true)
      setError(null)
      // Re-trigger useEffect
      setExercises([])
    }
  }
}
