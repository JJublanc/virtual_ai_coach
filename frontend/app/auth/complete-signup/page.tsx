'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/providers/AuthProvider'
import { supabase } from '@/lib/supabase'

export default function CompleteSignupPage() {
  const router = useRouter()
  const { user } = useAuth()
  const [featureName, setFeatureName] = useState<string | null>(null)
  const [comment, setComment] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Récupérer la feature depuis URL params
    const params = new URLSearchParams(window.location.search)
    const feature = params.get('feature')
    if (feature) {
      setFeatureName(decodeURIComponent(feature))
    } else {
      // Pas de feature en paramètre, rediriger vers la page d'accueil
      router.push('/')
    }
  }, [router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!user || !featureName) return

    setIsSubmitting(true)
    setError(null)

    try {
      // Mettre à jour le commentaire dans la waitlist existante
      const { error: updateError } = await supabase
        .from('waitlist')
        .update({
          comment: comment || null,
        })
        .eq('user_id', user.id)
        .eq('feature_name', featureName)

      if (updateError) {
        throw new Error(updateError.message)
      }

      // Rediriger vers la page d'accueil avec un message de succès
      router.push('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue')
      setIsSubmitting(false)
    }
  }

  const handleSkip = async () => {
    // Redirection directe sans mise à jour puisque l'entrée existe déjà sans commentaire
    router.push('/')
  }

  if (!featureName) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">
          Inscription réussie ! 🎉
        </h1>

        <p className="text-gray-600 mb-6">
          Vous êtes maintenant inscrit pour être informé du lancement de la fonctionnalité{' '}
          <span className="font-semibold">{featureName}</span>.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="comment" className="block text-sm font-medium text-gray-700 mb-2">
              Souhaitez-vous ajouter un commentaire ? (optionnel)
            </label>
            <textarea
              id="comment"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Ex: J'aimerais pouvoir... ou Je souhaiterais que..."
              rows={4}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isSubmitting}
            />
          </div>

          {error && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">
              {error}
            </div>
          )}

          <div className="flex gap-3">
            <button
              type="button"
              onClick={handleSkip}
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Passer
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? 'Envoi...' : 'Envoyer'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
