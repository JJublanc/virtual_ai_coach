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

// Descriptions par défaut pour chaque fonctionnalité
const defaultDescriptions: Record<FeatureName, string> = {
  Dashboard: "Visualiser vos statistiques d'entraînement, suivre vos progrès au fil du temps, et consulter vos performances détaillées avec des graphiques interactifs.",
  Profile: "Gérer votre profil utilisateur, personnaliser vos préférences d'entraînement, définir vos objectifs personnels et suivre votre évolution.",
  Goals: "Définir des objectifs SMART (Spécifiques, Mesurables, Atteignables, Réalistes, Temporels) et recevoir des recommandations d'entraînement adaptées pour les atteindre.",
  Plan: "Créer et gérer des programmes d'entraînement hebdomadaires personnalisés avec planification automatique basée sur vos disponibilités.",
  'Advanced Intervals': "Configurer des intervalles d'entraînement complexes avec des variations de temps de travail et de repos pour chaque exercice, incluant des progressions automatiques.",
  'Custom Intensity': "Ajuster finement l'intensité de chaque exercice individuellement, avec des recommandations basées sur votre niveau de forme physique et vos objectifs.",
  'Advanced Warmup': "Personnaliser votre échauffement avec des routines spécifiques selon le type d'entraînement prévu, incluant mobilité articulaire et activation musculaire ciblée.",
  'AI Assistant': "Bénéficier d'un assistant personnel intelligent qui comprend vos objectifs, analyse vos sensations et génère des séances d'entraînement parfaitement adaptées à votre état du moment.",
  'Select Exercises': "Créer votre propre sélection d'exercices favoris, exclure certains mouvements, et construire des bibliothèques personnalisées pour vos entraînements.",
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
