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

const mockExercises = [
  { name: 'Squate', icon: '🏋️', duration: 45, order: 1 },
  { name: 'Push ups', icon: '💪', duration: 30, order: 2 },
  { name: 'Burpees', icon: '🔥', duration: 40, order: 3 },
  { name: 'Abs', icon: '⚡', duration: 60, order: 4 },
  { name: 'Mountain climber', icon: '⛰️', duration: 35, order: 5 },
]

function formatDuration(seconds: number): string {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  if (minutes > 0) {
    return `${minutes}m ${remainingSeconds}s`
  }
  return `${remainingSeconds}s`
}

export function ExerciseList({ exercises, workoutInfo }: ExerciseListProps) {
  const displayExercises = exercises && exercises.length > 0 ? exercises : mockExercises
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
      <div className="space-y-2">
        <h4 className="text-sm font-medium text-gray-700 mb-3">
          Séquence d'exercices {exercises && exercises.length > 0 ? '(générée)' : '(exemple)'}
        </h4>
        {displayExercises.map((exercise, index) => (
          <div
            key={`${exercise.name}-${index}`}
            className="flex items-center gap-3 bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center justify-center w-8 h-8 bg-gray-100 rounded-full text-sm font-medium text-gray-600">
              {exercise.order || index + 1}
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

      {/* Message si pas d'exercices générés */}
      {(!exercises || exercises.length === 0) && (
        <div className="text-center py-4 text-gray-500 text-sm">
          <p>Générez un entraînement pour voir la séquence d'exercices personnalisée</p>
        </div>
      )}
    </div>
  )
}
