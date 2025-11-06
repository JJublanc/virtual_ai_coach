// components/video/VideoPlayer.tsx
'use client'

import { Play, Pause, Maximize2, Loader2 } from 'lucide-react'
import { useRef, useEffect, useState } from 'react'

interface WorkoutExercise {
  name: string
  description: string
  icon: string
  duration: number
  order: number
  is_break?: boolean
}

interface VideoPlayerProps {
  videoUrl?: string | null
  isGenerating?: boolean
  progress?: number
  error?: string | null
  workoutExercises?: WorkoutExercise[]
  workoutInfo?: {
    name: string
    totalDuration: number
    exerciseCount: number
  } | null
  onExerciseChange?: (exerciseIndex: number) => void
}

export function VideoPlayer({ videoUrl, isGenerating = false, progress = 0, error, workoutExercises = [], workoutInfo, onExerciseChange }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [currentExercise, setCurrentExercise] = useState<WorkoutExercise | null>(null)
  const [exerciseTimeRemaining, setExerciseTimeRemaining] = useState(0)
  const [currentExerciseIndex, setCurrentExerciseIndex] = useState(1)
  const [isExerciseDescriptionExpanded, setIsExerciseDescriptionExpanded] = useState(true)

  useEffect(() => {
    if (videoUrl && videoRef.current) {
      videoRef.current.load()
    }
  }, [videoUrl])

  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause()
      } else {
        videoRef.current.play()
      }
      setIsPlaying(!isPlaying)
    }
  }


  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (videoRef.current && duration > 0) {
      const rect = e.currentTarget.getBoundingClientRect()
      const clickX = e.clientX - rect.left
      const clickRatio = clickX / rect.width
      const newTime = clickRatio * duration
      videoRef.current.currentTime = newTime
    }
  }

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      const time = videoRef.current.currentTime
      setCurrentTime(time)

      // Calculer quel exercice est en cours et le temps restant
      if (workoutExercises.length > 0) {
        let cumulativeTime = 0
        for (let i = 0; i < workoutExercises.length; i++) {
          const exercise = workoutExercises[i]
          const exerciseEndTime = cumulativeTime + exercise.duration
          if (time >= cumulativeTime && time < exerciseEndTime) {
            setCurrentExercise(exercise)
            setCurrentExerciseIndex(i + 1) // Index commence à 1
            // Notifier le parent du changement d'exercice
            if (onExerciseChange) {
              onExerciseChange(i)
            }
            // Calculer le temps restant pour cet exercice
            const timeRemainingInExercise = exerciseEndTime - time
            setExerciseTimeRemaining(Math.ceil(timeRemainingInExercise))
            break
          }
          cumulativeTime += exercise.duration
        }
      }
    }
  }

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      // Utiliser la durée totale prévue du workout si disponible,
      // sinon utiliser la durée de la vidéo HTML5
      const totalWorkoutDuration = workoutInfo?.totalDuration || 0
      if (totalWorkoutDuration > 0) {
        setDuration(totalWorkoutDuration)
      } else {
        setDuration(videoRef.current.duration)
      }
    }
  }

  // Mettre à jour la durée quand workoutInfo change
  useEffect(() => {
    if (workoutInfo?.totalDuration) {
      setDuration(workoutInfo.totalDuration)
    }
  }, [workoutInfo])

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60)
    const seconds = Math.floor(time % 60)
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  }

  const progressPercentage = duration > 0 ? (currentTime / duration) * 100 : 0
  return (
    <div className="relative bg-gray-900 rounded-lg overflow-hidden aspect-video">
      {/* Vidéo réelle ou placeholder */}
      {videoUrl ? (
        <video
          ref={videoRef}
          className="w-full h-full object-cover"
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleLoadedMetadata}
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
        >
          <source src={videoUrl} type="video/mp4" />
          Votre navigateur ne supporte pas la lecture vidéo.
        </video>
      ) : (
        <div className="absolute inset-0 bg-gradient-to-br from-gray-800 to-gray-900" />
      )}

      {/* État de génération */}
      {isGenerating && (
        <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
          <div className="bg-white/90 backdrop-blur-sm rounded-lg p-6 text-center">
            <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-gray-900" />
            <p className="text-gray-900 font-medium mb-2">Génération de la vidéo...</p>
            <div className="w-48 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-sm text-gray-600 mt-2">{progress}%</p>
          </div>
        </div>
      )}

      {/* Erreur */}
      {error && (
        <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center max-w-md">
            <p className="text-red-800 font-medium mb-2">Erreur de génération</p>
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Contrôles vidéo - seulement si vidéo disponible */}
      {videoUrl && !isGenerating && !error && (
        <>
          {/* Overlay BREAK pendant les périodes de repos */}
          {currentExercise?.is_break && (
            <div
              className="absolute inset-0 z-10"
              style={{
                backgroundImage: 'url(/sport_room.png)',
                backgroundSize: 'cover',
                backgroundPosition: 'center',
              }}
            >
              {/* Overlay semi-transparent pour assurer la lisibilité */}
              <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />

              {/* Contenu centré */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <h1 className="text-9xl font-bold text-white mb-8 tracking-wider drop-shadow-2xl">
                    BREAK
                  </h1>
                  <div className="text-7xl font-mono text-blue-400 font-bold drop-shadow-lg">
                    {Math.floor(exerciseTimeRemaining / 60)}:{(exerciseTimeRemaining % 60).toString().padStart(2, '0')}
                  </div>
                  <p className="text-3xl text-white/90 mt-6 drop-shadow-lg">
                    Récupération en cours...
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Exercise description overlay - top left - masqué pendant les breaks */}
          {!currentExercise?.is_break && (
            <div className="absolute top-4 left-4 bg-white/60 backdrop-blur-sm rounded-lg p-4 w-80 transition-all duration-300">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 min-w-0 flex-1">
                <span className="text-2xl flex-shrink-0">{currentExercise?.icon || "🏋️"}</span>
                <h3 className="font-bold text-lg truncate">{currentExercise?.name || "Entraînement"}</h3>
              </div>
              <button
                onClick={() => setIsExerciseDescriptionExpanded(!isExerciseDescriptionExpanded)}
                className="text-gray-600 hover:text-gray-800 transition-all duration-300 flex-shrink-0 ml-2"
              >
                <span className={`inline-block transition-transform duration-300 ${isExerciseDescriptionExpanded ? 'rotate-180' : 'rotate-0'}`}>
                  ▼
                </span>
              </button>
            </div>
            {isExerciseDescriptionExpanded && (
              <div className="overflow-hidden transition-all duration-300">
                <p className="text-sm text-gray-600 leading-relaxed">
                  {currentExercise?.description || "Votre vidéo d'entraînement personnalisée est prête. Suivez les exercices et donnez le meilleur de vous-même !"}
                </p>
              </div>
            )}
            </div>
          )}

          {/* Timer circle - top right - couleur dynamique selon break ou exercice */}
          <div className="absolute top-4 right-4">
            <div className="relative w-24 h-24">
              <svg className="w-24 h-24 transform -rotate-90">
                <circle
                  cx="48"
                  cy="48"
                  r="40"
                  stroke="rgba(255,255,255,0.2)"
                  strokeWidth="8"
                  fill="none"
                />
                {/* Cercle de progression - couleur dynamique */}
                <circle
                  cx="48"
                  cy="48"
                  r="40"
                  stroke={currentExercise?.is_break ? "#60a5fa" : "#4ade80"}
                  strokeWidth="8"
                  fill="none"
                  strokeDasharray={`${2 * Math.PI * 40}`}
                  strokeDashoffset={`${2 * Math.PI * 40 * (1 - (currentExercise ? (currentExercise.duration - exerciseTimeRemaining) / currentExercise.duration : 0))}`}
                  className="transition-all duration-300"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className={`text-2xl font-bold ${currentExercise?.is_break ? 'text-blue-400' : 'text-white'}`}>
                  {exerciseTimeRemaining > 0 ? exerciseTimeRemaining : '0'}
                </span>
              </div>
            </div>

            {/* Indicateur exercice actuel - sous le timer */}
            <div className="mt-2 text-center">
              <span className="text-white text-sm font-medium bg-black/30 backdrop-blur-sm px-2 py-1 rounded">
                {workoutExercises.length > 0 ? `${currentExerciseIndex} / ${workoutExercises.length}` : '1 / -'}
              </span>
            </div>
          </div>

          {/* Progress bar - bottom */}
          <div className="absolute bottom-0 left-0 right-0 p-4">
            <div className="flex items-center justify-between mb-2">
              {/* Temps écoulé à gauche */}
              <span className="text-white text-sm font-medium">
                {formatTime(currentTime)} / {formatTime(duration)}
              </span>

              {/* Contrôles de lecture - alignés au centre */}
              <div className="flex items-center gap-2">
                {/* Bouton play/pause */}
                <button
                  onClick={togglePlay}
                  className="w-10 h-10 flex items-center justify-center bg-white/20 backdrop-blur-sm rounded-full border-2 border-white/40 hover:bg-white/30 transition-colors"
                >
                  {isPlaying ? (
                    <Pause className="w-5 h-5 text-white" fill="white" />
                  ) : (
                    <Play className="w-5 h-5 text-white ml-0.5" fill="white" />
                  )}
                </button>
              </div>

              {/* Bouton plein écran à droite */}
              <button className="text-white hover:text-gray-300 transition-colors">
                <Maximize2 className="w-5 h-5" />
              </button>
            </div>
            <div
              className="h-2 bg-white/20 rounded-full overflow-hidden cursor-pointer hover:h-3 transition-all"
              onClick={handleProgressClick}
              title="Cliquez pour naviguer dans la vidéo"
            >
              <div
                className="h-full bg-green-400 rounded-full transition-all duration-300"
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
          </div>
        </>
      )}

      {/* État par défaut - pas de vidéo */}
      {!videoUrl && !isGenerating && !error && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center text-white">
            <Play className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p className="text-lg font-medium mb-2">Prêt à commencer ?</p>
            <p className="text-sm opacity-75">Configurez votre entraînement et cliquez sur "Generate training"</p>
          </div>
        </div>
      )}
    </div>
  )
}
