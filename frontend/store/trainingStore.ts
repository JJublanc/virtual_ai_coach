// store/trainingStore.ts
import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { Exercise, WorkoutExercise, IntensityLevel, IntervalConfig, WorkoutConfig, TrainingSession, AIGenerationRequest, AIGenerationResponse, VideoPlayerState } from '@/lib/types'

interface TrainingStore {
  // État de la séance
  session: TrainingSession | null

  // Configuration
  config: WorkoutConfig

  // État du player
  player: VideoPlayerState

  // Actions - Exercices
  addExercise: (exercise: Exercise) => void
  removeExercise: (exerciseId: string) => void
  reorderExercises: (startIndex: number, endIndex: number) => void
  updateExerciseDuration: (exerciseId: string, duration: number) => void

  // Actions - Configuration
  setIntensity: (intensity: IntensityLevel) => void
  setIntervals: (intervals: IntervalConfig) => void
  toggleNoRepeat: () => void
  toggleNoJump: () => void
  toggleIntensityLevel: (level: 'easy' | 'medium' | 'hard') => void
  toggleWarmUp: () => void
  toggleCoolDown: () => void
  setTargetDuration: (minutes: number) => void

  // Actions - Séance
  generateTraining: (aiRequest?: AIGenerationRequest) => Promise<void>
  startTraining: () => void
  pauseTraining: () => void
  resumeTraining: () => void
  nextExercise: () => void
  previousExercise: () => void

  // Actions - Player
  updatePlayerState: (state: Partial<VideoPlayerState>) => void

  // Utilitaires
  reset: () => void
  calculateTotalDuration: () => number
}

const initialConfig: WorkoutConfig = {
  intensity: 'medium_intensity',
  intervals: { work_time: 40, rest_time: 20 },
  no_repeat: false,
  no_jump: false,
  intensity_levels: ['easy', 'medium', 'hard'],
  include_warm_up: false,
  include_cool_down: false,
}

export const useTrainingStore = create<TrainingStore>()(
  devtools(
    persist(
      (set, get) => ({
        session: null,
        config: initialConfig,
        player: {
          is_playing: false,
          current_time: 0,
          total_duration: 0,
          current_exercise: null,
          current_round: 1,
          progress_percentage: 0,
        },

        // Implémentation des actions...
        addExercise: (exercise) =>
          set((state) => {
            const newExercise: WorkoutExercise = {
              exercise,
              order: state.session?.exercises.length || 0,
            }
            return {
              session: {
                ...state.session!,
                exercises: [...(state.session?.exercises || []), newExercise],
              },
            }
          }),

        removeExercise: (exerciseId) =>
          set((state) => ({
            session: {
              ...state.session!,
              exercises: state.session!.exercises.filter(
                (e) => e.exercise.id !== exerciseId
              ),
            },
          })),

        reorderExercises: (startIndex, endIndex) =>
          set((state) => {
            const exercises = [...state.session!.exercises]
            const [removed] = exercises.splice(startIndex, 1)
            exercises.splice(endIndex, 0, removed)

            // Réindexer
            exercises.forEach((ex, idx) => {
              ex.order = idx
            })

            return { session: { ...state.session!, exercises } }
          }),

        updateExerciseDuration: (exerciseId, duration) =>
          set((state) => ({
            session: {
              ...state.session!,
              exercises: state.session!.exercises.map((we) =>
                we.exercise.id === exerciseId
                  ? { ...we, custom_duration: duration }
                  : we
              ),
            },
          })),

        setIntensity: (intensity) =>
          set((state) => ({
            config: { ...state.config, intensity },
          })),

        setIntervals: (intervals) =>
          set((state) => ({
            config: { ...state.config, intervals },
          })),

        toggleNoRepeat: () =>
          set((state) => ({
            config: { ...state.config, no_repeat: !state.config.no_repeat },
          })),

        toggleNoJump: () =>
          set((state) => ({
            config: { ...state.config, no_jump: !state.config.no_jump },
          })),

        toggleIntensityLevel: (level) =>
          set((state) => {
            const levels = state.config.intensity_levels.includes(level)
              ? state.config.intensity_levels.filter((l) => l !== level)
              : [...state.config.intensity_levels, level]
            return { config: { ...state.config, intensity_levels: levels } }
          }),

        toggleWarmUp: () =>
          set((state) => ({
            config: {
              ...state.config,
              include_warm_up: !state.config.include_warm_up,
            },
          })),

        toggleCoolDown: () =>
          set((state) => ({
            config: {
              ...state.config,
              include_cool_down: !state.config.include_cool_down,
            },
          })),

        setTargetDuration: (minutes) =>
          set((state) => ({
            config: { ...state.config, target_duration: minutes },
          })),

        generateTraining: async (aiRequest) => {
          // Appel API pour génération (IA ou logique simple)
          // TODO: Implémenter
        },

        startTraining: () =>
          set((state) => ({
            session: { ...state.session!, status: 'in_progress' },
            player: { ...state.player, is_playing: true },
          })),

        pauseTraining: () =>
          set((state) => ({
            player: { ...state.player, is_playing: false },
          })),

        resumeTraining: () =>
          set((state) => ({
            player: { ...state.player, is_playing: true },
          })),

        nextExercise: () =>
          set((state) => {
            if (!state.session) return state
            const nextIndex = (state.player.current_exercise_index || 0) + 1
            if (nextIndex < state.session.exercises.length) {
              return {
                player: {
                  ...state.player,
                  current_exercise_index: nextIndex,
                  current_exercise: state.session.exercises[nextIndex],
                  current_time: 0,
                },
              }
            }
            return state // Fin de la séance
          }),

        previousExercise: () =>
          set((state) => {
            if (!state.session) return state
            const prevIndex = (state.player.current_exercise_index || 0) - 1
            if (prevIndex >= 0) {
              return {
                player: {
                  ...state.player,
                  current_exercise_index: prevIndex,
                  current_exercise: state.session.exercises[prevIndex],
                  current_time: 0,
                },
              }
            }
            return state // Début de la séance
          }),

        updatePlayerState: (playerState) =>
          set((state) => ({
            player: { ...state.player, ...playerState },
          })),

        calculateTotalDuration: () => {
          const state = get()
          if (!state.session) return 0

          const { exercises } = state.session
          const { intervals, include_warm_up, include_cool_down } = state.config

          let total = 0

          // Warm up
          if (include_warm_up) total += 300 // 5 min

          // Exercices
          exercises.forEach((we) => {
            const duration = we.custom_duration || we.exercise.default_duration
            total += duration + intervals.rest_time
          })

          // Cool down
          if (include_cool_down) total += 300 // 5 min

          return total
        },

        reset: () =>
          set({
            session: null,
            config: initialConfig,
            player: {
              is_playing: false,
              current_time: 0,
              total_duration: 0,
              current_exercise: null,
              current_round: 1,
              progress_percentage: 0,
            },
          }),
      }),
      {
        name: 'training-storage',
      }
    )
  )
)
