// lib/exerciseIcons.ts
import {
  Dumbbell,     // General strength/weight training
  Activity,     // General cardio/activity
  Zap,          // Explosive/plyometric exercises
  Heart,        // Cardiovascular exercises
  Target,       // Targeted/isolated exercises
  Flame,        // High intensity exercises
  Timer,        // Timed holds/static exercises
  RotateCw,     // Rotational exercises
  ArrowUp,      // Jumping/upward movements
  ArrowDown,    // Floor/downward movements
  Pause,        // Break periods
  CircleDot,    // Core exercises
  Move,         // Dynamic movements
  Scale,        // Balance exercises
  Footprints,   // Leg exercises
  Hand,         // Arm exercises
  type LucideIcon
} from 'lucide-react'

// Mapping of exercise names to icons
export const exerciseIconMap: Record<string, LucideIcon> = {
  // Common exercise names (normalized to lowercase)
  'push-ups': ArrowDown,
  'pushups': ArrowDown,
  'push ups': ArrowDown,
  'squats': ArrowUp,
  'squat': ArrowUp,
  'air squat': ArrowUp,
  'burpees': Flame,
  'burpee': Flame,
  'plank': Timer,
  'planks': Timer,
  'jumping jacks': Activity,
  'jumping jack': Activity,
  'mountain climbers': Zap,
  'mountain climber': Zap,
  'lunges': Footprints,
  'lunge': Footprints,
  'pull-ups': ArrowUp,
  'pullups': ArrowUp,
  'pull ups': ArrowUp,
  'sit-ups': CircleDot,
  'situps': CircleDot,
  'sit ups': CircleDot,
  'crunches': CircleDot,
  'crunch': CircleDot,
  'bicep curls': Hand,
  'bicep curl': Hand,
  'tricep dips': Hand,
  'tricep dip': Hand,
  'shoulder press': Hand,
  'deadlift': Dumbbell,
  'deadlifts': Dumbbell,
  'bench press': Dumbbell,
  'high knees': Activity,
  'high knee': Activity,
  'box jumps': ArrowUp,
  'box jump': ArrowUp,
  'jump rope': Activity,
  'rope jump': Activity,
  'russian twist': RotateCw,
  'russian twists': RotateCw,
  'leg raises': Footprints,
  'leg raise': Footprints,
  'wall sit': Timer,
  'wall sits': Timer,
  'bicycle crunches': RotateCw,
  'bicycle crunch': RotateCw,
  'side plank': Timer,
  'side planks': Timer,
  'bear crawl': Move,
  'bear crawls': Move,
  'inchworm': Move,
  'inchworms': Move,
  'flutter kicks': Footprints,
  'flutter kick': Footprints,
  'running': Activity,
  'run': Activity,
  'jogging': Activity,
  'jog': Activity,

  // Exercise categories/types
  'strength': Dumbbell,
  'cardio': Heart,
  'hiit': Flame,
  'explosive': Zap,
  'targeted': Target,
  'timed': Timer,
  'rotation': RotateCw,
  'upper': Hand,
  'lower': Footprints,
  'activity': Activity,
  'core': CircleDot,
  'balance': Scale,

  // Special states
  'break': Pause,
  'rest': Pause,
}

/**
 * Get the appropriate Lucide icon for an exercise
 * @param exerciseName - Name of the exercise
 * @param exerciseType - Optional type/category of the exercise
 * @returns Lucide icon component
 */
export function getExerciseIcon(exerciseName: string, exerciseType?: string): LucideIcon {
  // Normalize the exercise name (lowercase, trim)
  const normalizedName = exerciseName.toLowerCase().trim()

  // First, try exact match
  if (exerciseIconMap[normalizedName]) {
    return exerciseIconMap[normalizedName]
  }

  // Then, try to find a partial match (for compound names)
  const partialMatch = Object.keys(exerciseIconMap).find(key =>
    normalizedName.includes(key) || key.includes(normalizedName)
  )

  if (partialMatch) {
    return exerciseIconMap[partialMatch]
  }

  // Try by exercise type if provided
  if (exerciseType && exerciseIconMap[exerciseType.toLowerCase()]) {
    return exerciseIconMap[exerciseType.toLowerCase()]
  }

  // Heuristic matching based on keywords
  if (normalizedName.includes('jump')) return ArrowUp
  if (normalizedName.includes('press') || normalizedName.includes('push')) return ArrowDown
  if (normalizedName.includes('pull')) return ArrowUp
  if (normalizedName.includes('squat')) return ArrowUp
  if (normalizedName.includes('plank')) return Timer
  if (normalizedName.includes('twist') || normalizedName.includes('rotate')) return RotateCw
  if (normalizedName.includes('crunch') || normalizedName.includes('core')) return CircleDot
  if (normalizedName.includes('leg') || normalizedName.includes('lunge')) return Footprints
  if (normalizedName.includes('arm') || normalizedName.includes('curl')) return Hand
  if (normalizedName.includes('run') || normalizedName.includes('jog')) return Activity
  if (normalizedName.includes('burpee') || normalizedName.includes('hiit')) return Flame

  // Default fallback
  return Dumbbell
}

/**
 * Get icon color classes based on exercise intensity or state
 * @param isBreak - Whether this is a break period
 * @param intensity - Exercise intensity level
 * @returns Tailwind CSS color classes
 */
export function getIconColorClasses(isBreak?: boolean, intensity?: 'easy' | 'medium' | 'hard'): string {
  if (isBreak) {
    return 'text-blue-600'
  }

  switch (intensity) {
    case 'easy':
      return 'text-green-600'
    case 'medium':
      return 'text-yellow-600'
    case 'hard':
      return 'text-red-600'
    default:
      return 'text-gray-700'
  }
}
