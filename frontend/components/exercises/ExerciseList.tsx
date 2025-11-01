// components/exercises/ExerciseList.tsx
'use client'

import { GripVertical, Trash2, Clock } from 'lucide-react'

interface WorkoutExercise {
  name: string
  icon: string
  duration: number
  order: number
}

interface ExerciseListProps {
  exercises?: WorkoutExercise[]
  workoutInfo?: {
    name: string
    totalDuration: number
    exerciseCount: number
  } | null
}


function formatDuration(seconds: number): string {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  if (minutes > 0) {
    return `${minutes}m ${remainingSeconds}s`
  }
  return `${remainingSeconds}s`
}

export function ExerciseList({ exercises, workoutInfo }: ExerciseListProps) {
  return (
    <div className="space-y-4">
      {/* En-tête avec informations du workout */}
      {workoutInfo && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-2">{workoutInfo.name}</h3>
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <div className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              <span>{formatDuration(workoutInfo.totalDuration)}</span>
            </div>
            <span>•</span>
            <span>{workoutInfo.exerciseCount} exercices</span>
          </div>
        </div>
      )}

      {/* Liste des exercices */}
      {exercises && exercises.length > 0 ? (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700 mb-3">
            Séquence d'exercices
          </h4>
          {exercises.map((exercise, index) => (
            <div
              key={`${exercise.name}-${index}`}
              className="flex items-center gap-3 bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-center w-8 h-8 bg-gray-100 rounded-full text-sm font-medium text-gray-600">
                {exercise.order}
              </div>
              <span className="text-2xl">{exercise.icon}</span>
              <div className="flex-1">
                <span className="font-medium block">{exercise.name}</span>
                <span className="text-sm text-gray-500">{formatDuration(exercise.duration)}</span>
              </div>
              <GripVertical className="w-5 h-5 text-gray-400 cursor-grab" />
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          <div className="mb-4">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <span className="text-2xl">🏋️</span>
            </div>
            <h4 className="font-medium text-gray-700 mb-2">Aucun entraînement généré</h4>
            <p className="text-sm">Configurez vos paramètres et cliquez sur "Generate training" pour voir votre séquence d'exercices personnalisée.</p>
          </div>
        </div>
      )}
    </div>
  )
}
