// components/exercises/ExerciseList.tsx
'use client'

import { GripVertical, Trash2, Clock } from 'lucide-react'
import { getExerciseIcon, getIconColorClasses } from '@/lib/exerciseIcons'

interface WorkoutExercise {
  name: string
  icon: string
  duration: number
  order: number
  is_break?: boolean
}

interface ExerciseListProps {
  exercises?: WorkoutExercise[]
  workoutInfo?: {
    name: string
    totalDuration: number
    exerciseCount: number
  } | null
  activeExerciseIndex?: number
}


function formatDuration(seconds: number): string {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  if (minutes > 0) {
    return `${minutes}m ${remainingSeconds}s`
  }
  return `${remainingSeconds}s`
}

export function ExerciseList({ exercises, workoutInfo, activeExerciseIndex = 0 }: ExerciseListProps) {
  return (
    <div className="space-y-4">
      {/* Liste des exercices */}
      {exercises && exercises.length > 0 ? (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700 mb-3">
            Exercise sequence
          </h4>
          <div className="max-h-80 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100 hover:scrollbar-thumb-gray-400">
            <div className="space-y-2 pr-2">
              {exercises.map((exercise, index) => {
                const isActive = index === activeExerciseIndex
                const isBreak = exercise.is_break
                const IconComponent = getExerciseIcon(exercise.name)
                const iconColorClass = getIconColorClasses(isBreak)
                // Calculate exercise number excluding breaks
                const exerciseNumber = exercises.slice(0, index + 1).filter(ex => !ex.is_break).length

                return (
                  <div
                    key={`${exercise.name}-${index}`}
                    className={`flex items-center gap-3 rounded-lg p-4 transition-all ${
                      isBreak
                        ? isActive
                          ? 'bg-blue-50 border-2 border-blue-400 shadow-lg scale-[1.02]'
                          : 'bg-blue-50/50 border border-blue-200 hover:shadow-md'
                        : isActive
                          ? 'bg-green-50 border-2 border-green-300 shadow-lg scale-[1.02]'
                          : 'bg-white border border-gray-200 hover:shadow-md'
                    }`}
                  >
                    {!isBreak && (
                      <div className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${
                        isActive
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-100 text-gray-600'
                      }`}>
                        {exerciseNumber}
                      </div>
                    )}
                    {isBreak && (
                      <div className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium ${
                        isActive
                          ? 'bg-blue-500 text-white'
                          : 'bg-blue-200 text-blue-700'
                      }`}>
                        <Clock className="w-4 h-4" />
                      </div>
                    )}
                    <div className={`flex items-center justify-center w-10 h-10 rounded-full ${
                      isBreak
                        ? 'bg-blue-50'
                        : 'bg-gray-50'
                    }`}>
                      <IconComponent className={`w-5 h-5 ${iconColorClass}`} />
                    </div>
                    <div className="flex-1">
                      <span className={`font-medium block ${
                        isBreak
                          ? isActive ? 'text-blue-800' : 'text-blue-700'
                          : isActive ? 'text-green-800' : 'text-gray-900'
                      }`}>
                        {exercise.name}
                      </span>
                      <span className={`text-sm ${
                        isBreak
                          ? isActive ? 'text-blue-600' : 'text-blue-500'
                          : isActive ? 'text-green-600' : 'text-gray-500'
                      }`}>
                        {formatDuration(exercise.duration)}
                        {isActive && <span className="ml-2 font-medium">• In progress</span>}
                      </span>
                    </div>
                    {!isBreak && <GripVertical className="w-5 h-5 text-gray-400 cursor-grab" />}
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          <div className="mb-4">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
              {(() => {
                const IconComponent = getExerciseIcon('Training')
                return <IconComponent className="w-8 h-8 text-gray-600" />
              })()}
            </div>
            <h4 className="font-medium text-gray-700 mb-2">No training generated</h4>
            <p className="text-sm">Configure your settings and click "Generate training" to see your personalized exercise sequence.</p>
          </div>
        </div>
      )}
    </div>
  )
}
