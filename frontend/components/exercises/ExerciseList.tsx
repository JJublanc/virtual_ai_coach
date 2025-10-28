// components/exercises/ExerciseList.tsx
'use client'

import { GripVertical, Trash2 } from 'lucide-react'

const mockExercises = [
  { id: '1', name: 'Squate', icon: '🏋️' },
  { id: '2', name: 'Push ups', icon: '💪' },
  { id: '3', name: 'Burpees', icon: '🔥' },
  { id: '4', name: 'abs', icon: '⚡' },
  { id: '5', name: 'Mountain climber', icon: '⛰️' },
]

export function ExerciseList() {
  return (
    <div className="space-y-2">
      {mockExercises.map((exercise) => (
        <div
          key={exercise.id}
          className="flex items-center gap-3 bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
        >
          <GripVertical className="w-5 h-5 text-gray-400 cursor-grab" />
          <span className="text-2xl">{exercise.icon}</span>
          <span className="flex-1 font-medium">{exercise.name}</span>
          <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <Trash2 className="w-5 h-5 text-gray-400 hover:text-red-500" />
          </button>
        </div>
      ))}
    </div>
  )
}
