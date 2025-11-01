// components/video/VideoPlayer.tsx
'use client'

import { Play, Pause, SkipBack, SkipForward, Maximize2, Loader2 } from 'lucide-react'
import { useRef, useEffect, useState } from 'react'

interface VideoPlayerProps {
  videoUrl?: string | null
  isGenerating?: boolean
  progress?: number
  error?: string | null
}

export function VideoPlayer({ videoUrl, isGenerating = false, progress = 0, error }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)

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

  const skipBackward = () => {
    if (videoRef.current) {
      videoRef.current.currentTime = Math.max(0, videoRef.current.currentTime - 10)
    }
  }

  const skipForward = () => {
    if (videoRef.current) {
      videoRef.current.currentTime = Math.min(duration, videoRef.current.currentTime + 10)
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
      setCurrentTime(videoRef.current.currentTime)
    }
  }

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration)
    }
  }

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
          {/* Exercise description overlay - top left */}
          <div className="absolute top-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg p-4 max-w-xs">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-bold text-lg">Entraînement</h3>
              <button className="text-gray-600">▼</button>
            </div>
            <p className="text-sm text-gray-600 leading-relaxed">
              Votre vidéo d'entraînement personnalisée est prête. Suivez les exercices et donnez le meilleur de vous-même !
            </p>
          </div>

          {/* Timer circle - top right */}
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
                <circle
                  cx="48"
                  cy="48"
                  r="40"
                  stroke="#4ade80"
                  strokeWidth="8"
                  fill="none"
                  strokeDasharray={`${2 * Math.PI * 40}`}
                  strokeDashoffset={`${2 * Math.PI * 40 * (1 - progressPercentage / 100)}`}
                  className="transition-all duration-300"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-white text-lg font-bold">
                  {formatTime(currentTime)}
                </span>
              </div>
            </div>
          </div>

          {/* Contrôles de lecture - centre */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="flex items-center gap-4">
              {/* Bouton reculer */}
              <button
                onClick={skipBackward}
                className="w-12 h-12 flex items-center justify-center bg-white/20 backdrop-blur-sm rounded-full border-2 border-white/50 hover:bg-white/30 transition-colors"
              >
                <SkipBack className="w-6 h-6 text-white" fill="white" />
              </button>

              {/* Bouton play/pause principal */}
              <button
                onClick={togglePlay}
                className="w-20 h-20 flex items-center justify-center bg-white/20 backdrop-blur-sm rounded-full border-4 border-white/50 hover:bg-white/30 transition-colors"
              >
                {isPlaying ? (
                  <Pause className="w-10 h-10 text-white" fill="white" />
                ) : (
                  <Play className="w-10 h-10 text-white ml-1" fill="white" />
                )}
              </button>

              {/* Bouton avancer */}
              <button
                onClick={skipForward}
                className="w-12 h-12 flex items-center justify-center bg-white/20 backdrop-blur-sm rounded-full border-2 border-white/50 hover:bg-white/30 transition-colors"
              >
                <SkipForward className="w-6 h-6 text-white" fill="white" />
              </button>
            </div>
          </div>

          {/* Progress bar - bottom */}
          <div className="absolute bottom-0 left-0 right-0 p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-white text-sm font-medium">
                {formatTime(currentTime)} / {formatTime(duration)}
              </span>
              <div className="flex items-center gap-2">
                {/* Contrôles supplémentaires */}
                <button
                  onClick={skipBackward}
                  className="p-1 text-white hover:text-gray-300 transition-colors"
                  title="Reculer de 10s"
                >
                  <SkipBack className="w-4 h-4" />
                </button>
                <button
                  onClick={togglePlay}
                  className="p-1 text-white hover:text-gray-300 transition-colors"
                  title={isPlaying ? "Pause" : "Lecture"}
                >
                  {isPlaying ? (
                    <Pause className="w-4 h-4" />
                  ) : (
                    <Play className="w-4 h-4" />
                  )}
                </button>
                <button
                  onClick={skipForward}
                  className="p-1 text-white hover:text-gray-300 transition-colors"
                  title="Avancer de 10s"
                >
                  <SkipForward className="w-4 h-4" />
                </button>
                <button className="p-1 text-white hover:text-gray-300 transition-colors">
                  <Maximize2 className="w-4 h-4" />
                </button>
              </div>
            </div>
            <div
              className="h-2 bg-white/20 rounded-full overflow-hidden cursor-pointer"
              onClick={handleProgressClick}
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
