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
  overlay_type?: 'intro' | 'none' | 'break_classic' | 'break_transparent' | 'outro'
  next_exercise_name?: string
  next_exercise_icon?: string
  next_exercise_duration?: number
  exercise_id?: string
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
  const [isInitialLoading, setIsInitialLoading] = useState(false)
  const [canPlay, setCanPlay] = useState(false)
  const [isBuffering, setIsBuffering] = useState(false)
  const [bufferingStartTime, setBufferingStartTime] = useState<number | null>(null)
  const wasPlayingBeforeHidden = useRef(false)

  useEffect(() => {
    if (videoUrl && videoRef.current) {
      setIsInitialLoading(true)
      setCanPlay(false)
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
    // Only beep for exercises (overlay_type === 'none'), not breaks or warnings
    if (currentExercise && currentExercise.overlay_type === 'none' && exerciseTimeRemaining > 0 && exerciseTimeRemaining <= 5) {
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
    if (videoRef.current && canPlay) {
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

  // Keep video playing even when tab is in background
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        console.log('[VideoPlayer] 👁️ Tab hidden - keeping video playing in background')
        // Save the playing state before hiding
        wasPlayingBeforeHidden.current = !!(isPlaying && videoRef.current && !videoRef.current.paused)

        // Try to keep video playing even in background
        if (wasPlayingBeforeHidden.current) {
          setTimeout(() => {
            if (videoRef.current && videoRef.current.paused) {
              console.log('[VideoPlayer] ▶️ Resuming video in background')
              videoRef.current.play().catch(err => {
                console.warn('[VideoPlayer] Could not resume video in background:', err)
              })
            }
          }, 100)
        }
      } else {
        console.log('[VideoPlayer] 👁️ Tab visible again')
        // Resume video if it was playing before being hidden
        if (wasPlayingBeforeHidden.current && videoRef.current && videoRef.current.paused) {
          console.log('[VideoPlayer] ▶️ Resuming video after returning to tab')
          videoRef.current.play().catch(err => {
            console.warn('[VideoPlayer] Could not resume video:', err)
          })
        }
        wasPlayingBeforeHidden.current = false
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [isPlaying])


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
        let exerciseCount = 0 // Count only non-break exercises

        console.log(`[VideoPlayer] Time: ${time.toFixed(2)}s, Total segments: ${workoutExercises.length}`)

        for (let i = 0; i < workoutExercises.length; i++) {
          const exercise = workoutExercises[i]
          const exerciseEndTime = cumulativeTime + exercise.duration

          console.log(`[VideoPlayer] Segment ${i}: ${exercise.name} (${exercise.overlay_type}), Time range: ${cumulativeTime}-${exerciseEndTime}s`)

          if (time >= cumulativeTime && time < exerciseEndTime) {
            console.log(`[VideoPlayer] ✓ Active segment: ${exercise.name} (${exercise.overlay_type})`)
            setCurrentExercise(exercise)
            // Only increment exercise count for actual exercises (not intro/outro/breaks/previews)
            if (exercise.overlay_type === 'none') {
              exerciseCount++
            }
            setCurrentExerciseIndex(exerciseCount)
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
          // Count actual exercises that have passed (not intro/outro/breaks/previews)
          if (exercise.overlay_type === 'none') {
            exerciseCount++
          }
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

  const handleCanPlay = () => {
    setIsInitialLoading(false)
    setCanPlay(true)
  }

  const handleWaiting = () => {
    // La vidéo attend des données (buffering)
    console.log('[VideoPlayer] 🔄 WAITING - Video is buffering')
    setIsBuffering(true)
    setBufferingStartTime(Date.now())
  }

  const handlePlaying = () => {
    // La vidéo joue, s'assurer que le loading initial est terminé
    console.log('[VideoPlayer] ▶️ PLAYING - Video is playing')
    setIsInitialLoading(false)

    // Log buffering duration if it was buffering
    if (isBuffering && bufferingStartTime) {
      const bufferingDuration = Date.now() - bufferingStartTime
      console.log(`[VideoPlayer] ✅ Buffering ended after ${bufferingDuration}ms`)
    }
    setIsBuffering(false)
    setBufferingStartTime(null)
  }

  const handleStalled = () => {
    console.log('[VideoPlayer] ⚠️ STALLED - Browser is trying to fetch data but nothing is arriving')
    setIsBuffering(true)
  }

  const handleSuspend = () => {
    console.log('[VideoPlayer] ⏸️ SUSPEND - Browser suspended media data loading')
  }

  const handleError = (e: React.SyntheticEvent<HTMLVideoElement, Event>) => {
    const video = e.currentTarget
    const error = video.error
    if (error) {
      console.error('[VideoPlayer] ❌ VIDEO ERROR:', {
        code: error.code,
        message: error.message,
        currentTime: video.currentTime,
        readyState: video.readyState,
        networkState: video.networkState
      })
    }
  }

  const handleProgress = () => {
    if (videoRef.current) {
      const buffered = videoRef.current.buffered
      if (buffered.length > 0) {
        const bufferedEnd = buffered.end(buffered.length - 1)
        const duration = videoRef.current.duration
        const bufferedPercent = (bufferedEnd / duration) * 100
        console.log(`[VideoPlayer] 📊 PROGRESS - Buffered: ${bufferedPercent.toFixed(1)}% (${bufferedEnd.toFixed(1)}s / ${duration.toFixed(1)}s)`)
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
          onPlay={() => {
            console.log('[VideoPlayer] ▶️ onPlay event')
            setIsPlaying(true)
          }}
          onPause={() => {
            // Don't update isPlaying if tab is hidden (automatic browser pause)
            if (!document.hidden) {
              console.log('[VideoPlayer] ⏸️ onPause event (user action)')
              setIsPlaying(false)
            } else {
              console.log('[VideoPlayer] ⏸️ onPause event (ignored - tab hidden)')
            }
          }}
          onCanPlay={handleCanPlay}
          onWaiting={handleWaiting}
          onPlaying={handlePlaying}
          onStalled={handleStalled}
          onSuspend={handleSuspend}
          onError={handleError}
          onProgress={handleProgress}
        >
          <source src={videoUrl} type="video/mp4" />
          Your browser does not support video playback.
        </video>
      ) : (
        <div className="absolute inset-0 bg-gradient-to-br from-gray-800 to-gray-900" />
      )}

      {/* Buffering state - show loading only during initial load */}
      {videoUrl && isInitialLoading && !canPlay && (
        <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-30">
          <div className="bg-white/90 backdrop-blur-sm rounded-lg p-6 text-center">
            <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-gray-900" />
            <p className="text-gray-900 font-medium mb-2">Loading video...</p>
            <p className="text-sm text-gray-600">Preparing your workout</p>
          </div>
        </div>
      )}

      {/* Buffering indicator - show when video is buffering during playback */}
      {videoUrl && !isInitialLoading && isBuffering && (
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-30">
          <div className="bg-black/70 backdrop-blur-sm rounded-full p-4">
            <Loader2 className="w-12 h-12 animate-spin text-white" />
          </div>
        </div>
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

      {/* Video controls - only if video available and ready to play */}
      {videoUrl && !isGenerating && !error && canPlay && (
        <>
          {/* INTRO overlay - safety warning at the start of workout */}
          {currentExercise?.overlay_type === 'intro' && (
            <div className="absolute inset-0 z-10 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
              {/* Centered content */}
              <div className="absolute inset-0 flex items-center justify-center px-8">
                <div className="max-w-4xl text-center space-y-6">
                  <h1 className="text-6xl font-bold text-red-500 mb-8 tracking-wider">
                    WARNING
                  </h1>
                  <p className="text-2xl text-white/90 leading-relaxed">
                    Before starting a workout, make sure you are fit enough to do cardio exercise.
                  </p>
                  <p className="text-2xl text-white/90 leading-relaxed">
                    Don't hesitate to consult your doctor if you have any doubt.
                  </p>
                  <p className="text-2xl text-white/90 leading-relaxed">
                    Stop immediately if you feel unwell during a session.
                  </p>
                  <p className="text-2xl text-white/90 leading-relaxed">
                    Remember to stay hydrated and take as many breaks as needed.
                  </p>
                  <p className="text-2xl text-white/90 leading-relaxed">
                    It is highly recommended to warm up before a workout and stretch afterward.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* OUTRO overlay - congratulations at the end */}
          {currentExercise?.overlay_type === 'outro' && (
            <div
              className="absolute inset-0 z-10"
              style={{
                backgroundImage: 'url(/sport_room.png)',
                backgroundSize: 'cover',
                backgroundPosition: 'center',
              }}
            >
              {/* Semi-transparent overlay */}
              <div className="absolute inset-0 bg-black/20" />

              {/* Congratulations text */}
              <div className="absolute inset-0 flex items-center justify-center">
                <h1 className="text-9xl font-bold text-white tracking-wider drop-shadow-2xl">
                  Congratulations!
                </h1>
              </div>
            </div>
          )}

          {/* BREAK CLASSIC overlay - opaque break screen */}
          {currentExercise?.overlay_type === 'break_classic' && (
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
              {currentExercise.next_exercise_name && (
                <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg p-4 max-w-sm shadow-2xl">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Next up</p>
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                      {(() => {
                        const NextIconComponent = getExerciseIcon(currentExercise.next_exercise_name)
                        return <NextIconComponent className="w-6 h-6 text-green-600" />
                      })()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-bold text-lg text-gray-900 truncate">{currentExercise.next_exercise_name}</h3>
                      <p className="text-sm text-gray-600">{currentExercise.next_exercise_duration}s</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Centered content */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <h1 className="text-9xl font-bold text-white mb-8 tracking-wider drop-shadow-2xl">
                    BREAK
                  </h1>
                  <div className="text-7xl font-mono text-blue-400 font-bold drop-shadow-lg">
                    {(() => {
                      // Add 5 seconds to show countdown from 20 to 5 (including upcoming preview)
                      const totalBreakTime = exerciseTimeRemaining + 5
                      return `${Math.floor(totalBreakTime / 60)}:${(totalBreakTime % 60).toString().padStart(2, '0')}`
                    })()}
                  </div>
                  <p className="text-3xl text-white/90 mt-6 drop-shadow-lg">
                    Recovery in progress...
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* BREAK TRANSPARENT overlay - preview of next exercise */}
          {currentExercise?.overlay_type === 'break_transparent' && (
            <div className="absolute inset-0 z-10">
              {/* Transparent overlay (20% opacity = 80% transparent) to show video underneath */}
              <div className="absolute inset-0 bg-black/20" />

              {/* Next exercise indicator - top left (same position as break classic) */}
              <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg p-4 max-w-sm shadow-2xl">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Next up</p>
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                    {(() => {
                      const NextIconComponent = getExerciseIcon(currentExercise.next_exercise_name || '')
                      return <NextIconComponent className="w-6 h-6 text-green-600" />
                    })()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-bold text-lg text-gray-900 truncate">{currentExercise.next_exercise_name}</h3>
                    <p className="text-sm text-gray-600">Get ready!</p>
                  </div>
                </div>
              </div>

              {/* Countdown - centered and prominent for preview (5 to 0) */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <div className="text-8xl font-mono text-green-400 font-bold drop-shadow-2xl">
                    {exerciseTimeRemaining}
                  </div>
                  <p className="text-2xl text-white/90 mt-4 drop-shadow-lg">
                    Get ready...
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* NO OVERLAY - clean view during exercise (overlay_type === 'none') */}
          {/* Only show exercise description for 'none' overlay type */}
          {currentExercise?.overlay_type === 'none' && (
            <div className="absolute top-4 left-4 bg-white/60 backdrop-blur-sm rounded-lg p-4 w-80 transition-all duration-300 z-20">
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

          {/* Timer circle - top right - only visible during exercises */}
          {currentExercise?.overlay_type === 'none' && (
          <div className="absolute top-4 right-4 z-20">
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
                {/* Progress circle - green for exercises */}
                <circle
                  cx="48"
                  cy="48"
                  r="40"
                  stroke="#4ade80"
                  strokeWidth="8"
                  fill="none"
                  strokeDasharray={`${2 * Math.PI * 40}`}
                  strokeDashoffset={`${2 * Math.PI * 40 * (1 - (currentExercise ? (currentExercise.duration - exerciseTimeRemaining) / currentExercise.duration : 0))}`}
                  className="transition-all duration-300"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-2xl font-bold text-white">
                  {exerciseTimeRemaining > 0 ? exerciseTimeRemaining : '0'}
                </span>
              </div>
            </div>

            {/* Current exercise indicator - below timer */}
            <div className="mt-2 text-center">
              <span className="text-white text-sm font-medium bg-black/30 backdrop-blur-sm px-2 py-1 rounded">
                {workoutExercises.length > 0 ? `${currentExerciseIndex} / ${workoutExercises.filter(ex => ex.overlay_type === 'none').length}` : '1 / -'}
              </span>
            </div>
          </div>
          )}

          {/* Progress bar - bottom */}
          <div className="absolute bottom-0 left-0 right-0 p-4 z-20">
            <div className="flex items-center justify-between mb-2">
              {/* Elapsed time on the left */}
              <span className="text-white text-sm font-medium">
                {formatTime(currentTime)} / {formatTime(duration)}
              </span>

              {/* Playback controls - centered */}
              <div className="flex items-center gap-2">
                {/* Play/pause button - disabled only during initial loading */}
                <button
                  onClick={togglePlay}
                  disabled={!canPlay}
                  className={`w-10 h-10 flex items-center justify-center bg-white/20 backdrop-blur-sm rounded-full border-2 border-white/40 transition-colors ${
                    !canPlay ? 'opacity-50 cursor-not-allowed' : 'hover:bg-white/30'
                  }`}
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
