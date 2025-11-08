// components/video/VideoPlayer.tsx
'use client'

import { Play, Pause, Maximize2, Minimize2, Loader2 } from 'lucide-react'
import { useRef, useEffect, useState } from 'react'
import { getExerciseIcon, getIconColorClasses } from '@/lib/exerciseIcons'

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
  const containerRef = useRef<HTMLDivElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [currentExercise, setCurrentExercise] = useState<WorkoutExercise | null>(null)
  const [exerciseTimeRemaining, setExerciseTimeRemaining] = useState(0)
  const [currentExerciseIndex, setCurrentExerciseIndex] = useState(1)
  const [isExerciseDescriptionExpanded, setIsExerciseDescriptionExpanded] = useState(true)
  const [lastBeepSecond, setLastBeepSecond] = useState<number | null>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)

  useEffect(() => {
    if (videoUrl && videoRef.current) {
      videoRef.current.load()
    }
  }, [videoUrl])

  // Function to play beep sound using Web Audio API
  const playBeep = (frequency: number = 800, duration: number = 350) => {
    try {
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
      const oscillator = audioContext.createOscillator()
      const gainNode = audioContext.createGain()

      oscillator.connect(gainNode)
      gainNode.connect(audioContext.destination)

      oscillator.frequency.value = frequency
      oscillator.type = 'sine'

      gainNode.gain.setValueAtTime(0.9, audioContext.currentTime)
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration / 1000)

      oscillator.start(audioContext.currentTime)
      oscillator.stop(audioContext.currentTime + duration / 1000)
    } catch (error) {
      console.error('Error playing beep:', error)
    }
  }

  // Effect to handle countdown beeps for last 5 seconds
  useEffect(() => {
    // Only beep for exercises, not breaks
    if (currentExercise && !currentExercise.is_break && exerciseTimeRemaining > 0 && exerciseTimeRemaining <= 5) {
      // Check if we haven't beeped for this second yet
      if (lastBeepSecond !== exerciseTimeRemaining) {
        playBeep()
        setLastBeepSecond(exerciseTimeRemaining)
      }
    } else if (exerciseTimeRemaining > 5) {
      // Reset the beep tracker when we're not in countdown range
      setLastBeepSecond(null)
    }
  }, [exerciseTimeRemaining, currentExercise, lastBeepSecond])

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

  const toggleFullscreen = async () => {
    if (!containerRef.current) return

    try {
      if (!document.fullscreenElement) {
        await containerRef.current.requestFullscreen()
        setIsFullscreen(true)
      } else {
        await document.exitFullscreen()
        setIsFullscreen(false)
      }
    } catch (error) {
      console.error('Error toggling fullscreen:', error)
    }
  }

  // Listen for fullscreen changes (user can exit with ESC)
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }

    document.addEventListener('fullscreenchange', handleFullscreenChange)
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange)
  }, [])


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

      // Calculate which exercise is in progress and remaining time
      if (workoutExercises.length > 0) {
        let cumulativeTime = 0
        for (let i = 0; i < workoutExercises.length; i++) {
          const exercise = workoutExercises[i]
          const exerciseEndTime = cumulativeTime + exercise.duration
          if (time >= cumulativeTime && time < exerciseEndTime) {
            setCurrentExercise(exercise)
            setCurrentExerciseIndex(i + 1) // Index starts at 1
            // Notify parent of exercise change
            if (onExerciseChange) {
              onExerciseChange(i)
            }
            // Calculate remaining time for this exercise
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
      // Use the total expected workout duration if available,
      // otherwise use the HTML5 video duration
      const totalWorkoutDuration = workoutInfo?.totalDuration || 0
      if (totalWorkoutDuration > 0) {
        setDuration(totalWorkoutDuration)
      } else {
        setDuration(videoRef.current.duration)
      }
    }
  }

  // Update duration when workoutInfo changes
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
    <div ref={containerRef} className="relative bg-gray-900 rounded-lg overflow-hidden aspect-video">
      {/* Actual video or placeholder */}
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
          Your browser does not support video playback.
        </video>
      ) : (
        <div className="absolute inset-0 bg-gradient-to-br from-gray-800 to-gray-900" />
      )}

      {/* Generation state */}
      {isGenerating && (
        <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
          <div className="bg-white/90 backdrop-blur-sm rounded-lg p-6 text-center">
            <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-gray-900" />
            <p className="text-gray-900 font-medium mb-2">Generating video...</p>
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

      {/* Error */}
      {error && (
        <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center max-w-md">
            <p className="text-red-800 font-medium mb-2">Generation error</p>
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Video controls - only if video available */}
      {videoUrl && !isGenerating && !error && (
        <>
          {/* BREAK overlay during rest periods */}
          {currentExercise?.is_break && (
            <div
              className="absolute inset-0 z-10"
              style={{
                backgroundImage: 'url(/sport_room.png)',
                backgroundSize: 'cover',
                backgroundPosition: 'center',
              }}
            >
              {/* Semi-transparent overlay for readability */}
              <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />

              {/* Next exercise indicator - top left */}
              {(() => {
                const nextExercise = workoutExercises[currentExerciseIndex]
                if (nextExercise && !nextExercise.is_break) {
                  const NextIconComponent = getExerciseIcon(nextExercise.name)
                  return (
                    <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg p-4 max-w-sm shadow-2xl">
                      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Next up</p>
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                          <NextIconComponent className="w-6 h-6 text-green-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-bold text-lg text-gray-900 truncate">{nextExercise.name}</h3>
                          <p className="text-sm text-gray-600">{nextExercise.duration}s</p>
                        </div>
                      </div>
                    </div>
                  )
                }
                return null
              })()}

              {/* Centered content */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <h1 className="text-9xl font-bold text-white mb-8 tracking-wider drop-shadow-2xl">
                    BREAK
                  </h1>
                  <div className="text-7xl font-mono text-blue-400 font-bold drop-shadow-lg">
                    {Math.floor(exerciseTimeRemaining / 60)}:{(exerciseTimeRemaining % 60).toString().padStart(2, '0')}
                  </div>
                  <p className="text-3xl text-white/90 mt-6 drop-shadow-lg">
                    Recovery in progress...
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Exercise description overlay - top left - hidden during breaks */}
          {!currentExercise?.is_break && (
            <div className="absolute top-4 left-4 bg-white/60 backdrop-blur-sm rounded-lg p-4 w-80 transition-all duration-300">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 min-w-0 flex-1">
                {(() => {
                  const IconComponent = getExerciseIcon(currentExercise?.name || 'Training')
                  return <IconComponent className="w-6 h-6 text-gray-700 flex-shrink-0" />
                })()}
                <h3 className="font-bold text-lg truncate">{currentExercise?.name || "Training"}</h3>
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
                  {currentExercise?.description || "Your personalized training video is ready. Follow the exercises and give it your best!"}
                </p>
              </div>
            )}
            </div>
          )}

          {/* Timer circle - top right - dynamic color based on break or exercise */}
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
                {/* Progress circle - dynamic color */}
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

            {/* Current exercise indicator - below timer */}
            <div className="mt-2 text-center">
              <span className="text-white text-sm font-medium bg-black/30 backdrop-blur-sm px-2 py-1 rounded">
                {workoutExercises.length > 0 ? `${currentExerciseIndex} / ${workoutExercises.length}` : '1 / -'}
              </span>
            </div>
          </div>

          {/* Progress bar - bottom */}
          <div className="absolute bottom-0 left-0 right-0 p-4">
            <div className="flex items-center justify-between mb-2">
              {/* Elapsed time on the left */}
              <span className="text-white text-sm font-medium">
                {formatTime(currentTime)} / {formatTime(duration)}
              </span>

              {/* Playback controls - centered */}
              <div className="flex items-center gap-2">
                {/* Play/pause button */}
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

              {/* Fullscreen button on the right */}
              <button
                onClick={toggleFullscreen}
                className="text-white hover:text-gray-300 transition-colors"
                title={isFullscreen ? "Exit fullscreen (ESC)" : "Enter fullscreen"}
              >
                {isFullscreen ? (
                  <Minimize2 className="w-5 h-5" />
                ) : (
                  <Maximize2 className="w-5 h-5" />
                )}
              </button>
            </div>
            <div
              className="h-2 bg-white/20 rounded-full overflow-hidden cursor-pointer hover:h-3 transition-all"
              onClick={handleProgressClick}
              title="Click to navigate in the video"
            >
              <div
                className="h-full bg-green-400 rounded-full transition-all duration-300"
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
          </div>
        </>
      )}

      {/* Default state - no video */}
      {!videoUrl && !isGenerating && !error && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center text-white">
            <Play className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p className="text-lg font-medium mb-2">Ready to start?</p>
            <p className="text-sm opacity-75">Configure your training and click "Generate training"</p>
          </div>
        </div>
      )}
    </div>
  )
}
