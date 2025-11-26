// hooks/useComingSoonModal.ts
'use client'

import { useState, useCallback } from 'react'
import { FeatureName } from '@/lib/types'

interface FeatureConfig {
  name: FeatureName
  description: string
}

interface UseComingSoonModalReturn {
  isOpen: boolean
  featureName: FeatureName
  featureDescription: string
  openModal: (feature: FeatureName, description?: string) => void
  closeModal: () => void
}

// Default descriptions for each feature
const defaultDescriptions: Record<FeatureName, string> = {
  Dashboard: "Visualize your training statistics, track your progress over time, and view your detailed performance with interactive charts.",
  Profile: "Manage your user profile, customize your training preferences, set your personal goals, and track your evolution.",
  Goals: "Define SMART goals (Specific, Measurable, Achievable, Realistic, Time-bound) and receive tailored training recommendations to achieve them.",
  Plan: "Create and manage personalized weekly training programs with automatic scheduling based on your availability.",
  'Advanced Intervals': "Configure complex training intervals with variations in work and rest times for each exercise, including automatic progressions.",
  'Custom Intensity': "Fine-tune the intensity of each exercise individually, with recommendations based on your fitness level and goals.",
  'Advanced Warmup': "Customize your warm-up with specific routines according to the planned training type, including joint mobility and targeted muscle activation.",
  'AI Assistant': "Benefit from an intelligent personal assistant that understands your goals, analyzes your feelings, and generates training sessions perfectly adapted to your current state.",
  'Select Exercises': "Create your own selection of favorite exercises, exclude certain movements, and build personalized libraries for your workouts.",
  'Exercise Filters': "Customize exercise filters to exclude repeated movements, jumping exercises, and adapt your training to your preferences and physical constraints.",
}

export function useComingSoonModal(): UseComingSoonModalReturn {
  const [isOpen, setIsOpen] = useState(false)
  const [currentFeature, setCurrentFeature] = useState<FeatureConfig>({
    name: 'Dashboard',
    description: defaultDescriptions.Dashboard,
  })

  const openModal = useCallback((feature: FeatureName, customDescription?: string) => {
    setCurrentFeature({
      name: feature,
      description: customDescription || defaultDescriptions[feature],
    })
    setIsOpen(true)
  }, [])

  const closeModal = useCallback(() => {
    setIsOpen(false)
  }, [])

  return {
    isOpen,
    featureName: currentFeature.name,
    featureDescription: currentFeature.description,
    openModal,
    closeModal,
  }
}
