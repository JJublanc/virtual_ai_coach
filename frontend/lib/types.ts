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
  current_exercise_index?: number // Index de l'exercice en cours
  current_round: number
  progress_percentage: number
}
