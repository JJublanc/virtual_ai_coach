// components/modals/ComingSoonModal.tsx
'use client'

import { useState, FormEvent, useEffect } from 'react'
import { X, Sparkles, Mail, Lock, MessageSquare, CheckCircle } from 'lucide-react'
import { FeatureName } from '@/lib/types'
import { useAuth } from '@/providers/AuthProvider'
import { supabase } from '@/lib/supabase'
import Image from 'next/image'

interface ComingSoonModalProps {
  isOpen: boolean
  onClose: () => void
  featureName: FeatureName
  featureDescription: string
}

type AuthMode = 'signin' | 'signup'

export function ComingSoonModal({
  isOpen,
  onClose,
  featureName,
  featureDescription,
}: ComingSoonModalProps) {
  const { user, signUp, signIn, signInWithProvider, signOut } = useAuth()
  const [authMode, setAuthMode] = useState<AuthMode>('signup')
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    comment: '',
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [isOnWaitlist, setIsOnWaitlist] = useState(false)

  // Vérifier si l'utilisateur est déjà sur la waitlist pour cette feature
  useEffect(() => {
    const checkWaitlistStatus = async () => {
      if (user) {
        const { data, error } = await supabase
          .from('waitlist')
          .select('id')
          .eq('user_id', user.id)
          .eq('feature_name', featureName)
          .maybeSingle()

        if (data && !error) {
          setIsOnWaitlist(true)
        }
      }
    }

    if (isOpen) {
      checkWaitlistStatus()
    }
  }, [user, featureName, isOpen])

  if (!isOpen) return null

  const handleAuthSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)

    try {
      let authError

      if (authMode === 'signup') {
        const result = await signUp(formData.email, formData.password)
        authError = result.error
      } else {
        const result = await signIn(formData.email, formData.password)
        authError = result.error
      }

      if (authError) {
        throw new Error(authError.message)
      }

      // Attendre que l'utilisateur soit connecté
      await new Promise(resolve => setTimeout(resolve, 500))

      // Ajouter à la waitlist
      const { data: userData } = await supabase.auth.getUser()

      if (userData.user) {
        const { error: waitlistError } = await supabase
          .from('waitlist')
          .insert({
            user_id: userData.user.id,
            feature_name: featureName,
            comment: formData.comment || null,
          })

        if (waitlistError && !waitlistError.message.includes('duplicate')) {
          throw new Error(waitlistError.message)
        }
      }

      setSuccess(true)

      // Auto-fermeture après 3 secondes
      setTimeout(() => {
        onClose()
        setTimeout(() => {
          setFormData({ email: '', password: '', comment: '' })
          setSuccess(false)
          setIsOnWaitlist(false)
        }, 300)
      }, 3000)

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleCommentSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)

    try {
      if (!user) return

      const { error: updateError } = await supabase
        .from('waitlist')
        .update({ comment: formData.comment })
        .eq('user_id', user.id)
        .eq('feature_name', featureName)

      if (updateError) {
        throw new Error(updateError.message)
      }

      setSuccess(true)
      setTimeout(() => {
        onClose()
        setTimeout(() => {
          setFormData({ email: '', password: '', comment: '' })
          setSuccess(false)
        }, 300)
      }, 2000)

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    if (!isSubmitting) {
      onClose()
      setTimeout(() => {
        setFormData({ email: '', password: '', comment: '' })
        setError(null)
        setSuccess(false)
        setIsOnWaitlist(false)
        setAuthMode('signup')
      }, 300)
    }
  }

  const handleSocialSignIn = async (provider: 'google' | 'github' | 'facebook') => {
    setError(null)
    setIsSubmitting(true)

    try {
      const { error } = await signInWithProvider(provider, featureName)

      if (error) {
        throw new Error(error.message)
      }

      // L'utilisateur sera redirigé vers le provider OAuth
      // Après retour, le callback ajoutera automatiquement à la waitlist

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue')
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="relative w-full max-w-2xl bg-white rounded-2xl shadow-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 p-6 flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gray-100 rounded-lg">
              <Sparkles className="w-6 h-6 text-gray-900" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Bientôt disponible</h2>
              <p className="text-sm text-gray-600">{featureName}</p>
            </div>
          </div>
          <button
            onClick={handleClose}
            disabled={isSubmitting}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {success ? (
            // Message de succès
            <div className="py-12 text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Merci !</h3>
              <p className="text-gray-600">
                {isOnWaitlist
                  ? 'Votre commentaire a été enregistré.'
                  : 'Vous êtes maintenant sur la liste d\'attente.'}
                <br />
                Nous vous tiendrons informé dès que cette fonctionnalité sera disponible.
              </p>
            </div>
          ) : user && isOnWaitlist ? (
            // Utilisateur déjà sur la waitlist
            <>
              <div className="bg-green-50 rounded-lg p-6 border border-green-200">
                <div className="flex items-start gap-3">
                  <CheckCircle className="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="font-semibold text-green-900 mb-1">Vous êtes sur la liste d'attente</h3>
                    <p className="text-sm text-green-700">
                      Merci pour votre intérêt ! Vous recevrez un email dès que la fonctionnalité <strong>{featureName}</strong> sera disponible.
                    </p>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Cette fonctionnalité vous permettra de :</h3>
                <p className="text-gray-600 leading-relaxed">{featureDescription}</p>
              </div>

              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <p className="text-sm text-gray-700">
                  <strong>Statut :</strong> En cours de développement<br />
                  <strong>Lancement estimé :</strong> Prochainement
                </p>
              {/* Bouton de déconnexion pour permettre à d'autres utilisateurs de s'inscrire */}
              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={async () => {
                    await signOut()
                    setIsOnWaitlist(false)
                  }}
                  className="text-sm text-gray-600 hover:text-gray-900 underline transition-colors"
                >
                  Se déconnecter (pour permettre à quelqu'un d'autre de s'inscrire)
                </button>
              </div>

              </div>

              {/* Formulaire de commentaire optionnel */}
              <form onSubmit={handleCommentSubmit} className="space-y-4">
                <div>
                  <label htmlFor="comment" className="block text-sm font-medium text-gray-700 mb-2">
                    Ajoutez ou modifiez vos suggestions (optionnel)
                  </label>
                  <div className="relative">
                    <MessageSquare className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
                    <textarea
                      id="comment"
                      value={formData.comment}
                      onChange={(e) => setFormData({ ...formData, comment: e.target.value })}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent resize-none"
                      placeholder="Partagez vos idées pour améliorer cette fonctionnalité..."
                      rows={3}
                      disabled={isSubmitting}
                    />
                  </div>
                </div>

                {error && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={isSubmitting || !formData.comment.trim()}
                  className="w-full py-3 bg-gray-900 text-white rounded-lg font-medium hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? 'Enregistrement...' : 'Enregistrer le commentaire'}
                </button>
              </form>
            </>
          ) : (
            // Formulaire d'authentification pour utilisateurs non connectés
            <>
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <p className="text-gray-700 leading-relaxed">
                  Notre application est en cours de développement actif. La fonctionnalité <strong>{featureName}</strong> arrive bientôt !
                </p>
              </div>

              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Cette fonctionnalité vous permettra de :</h3>
                <p className="text-gray-600 leading-relaxed">{featureDescription}</p>
              </div>

              <div className="bg-gradient-to-r from-gray-900 to-gray-700 rounded-lg p-4 text-white">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="w-5 h-5" />
                  <h3 className="font-semibold">Offre Early Access</h3>
                </div>
                <p className="text-sm text-gray-200">
                  Inscrivez-vous maintenant et bénéficiez d'une réduction exclusive pour les 3 premiers mois lors du lancement !
                </p>
              </div>

              {/* Onglets Sign In / Sign Up */}
              <div className="flex border-b border-gray-200">
                <button
                  type="button"
                  onClick={() => setAuthMode('signup')}
                  className={`flex-1 py-3 font-medium transition-colors ${
                    authMode === 'signup'
                      ? 'text-gray-900 border-b-2 border-gray-900'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Créer un compte
                </button>
                <button
                  type="button"
                  onClick={() => setAuthMode('signin')}
                  className={`flex-1 py-3 font-medium transition-colors ${
                    authMode === 'signin'
                      ? 'text-gray-900 border-b-2 border-gray-900'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Se connecter
                </button>
              </div>

              {/* Formulaire d'authentification */}
              <form onSubmit={handleAuthSubmit} className="space-y-4">
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                    Email <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      id="email"
                      type="email"
                      required
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                      placeholder="votre@email.com"
                      disabled={isSubmitting}
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                    Mot de passe <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      id="password"
                      type="password"
                      required
                      minLength={6}
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                      placeholder="Minimum 6 caractères"
                      disabled={isSubmitting}
                    />
                  </div>
                </div>

                {authMode === 'signup' && (
                  <div>
                    <label htmlFor="comment" className="block text-sm font-medium text-gray-700 mb-2">
                      Vos attentes (optionnel)
                    </label>
                    <div className="relative">
                      <MessageSquare className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
                      <textarea
                        id="comment"
                        value={formData.comment}
                        onChange={(e) => setFormData({ ...formData, comment: e.target.value })}
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent resize-none"
                        placeholder="Dites-nous ce que vous attendez de cette fonctionnalité..."
                        rows={3}
                        disabled={isSubmitting}
                      />
                    </div>
                  </div>
                )}

                {error && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
                    {error}
                  </div>
                )}

                {/* Boutons SSO */}
                <div className="space-y-3">
                  <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-gray-300"></div>
                    </div>
                    <div className="relative flex justify-center text-sm">
                      <span className="px-2 bg-white text-gray-500">Ou continuer avec</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 gap-3">
                    <button
                      type="button"
                      onClick={() => handleSocialSignIn('google')}
                      disabled={isSubmitting}
                      className="w-full flex items-center justify-center gap-3 py-2.5 px-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <svg className="w-5 h-5" viewBox="0 0 24 24">
                        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                      </svg>
                      <span className="text-gray-700 font-medium">Google</span>
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full py-3 bg-gray-900 text-white rounded-lg font-medium hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isSubmitting ? (
                    <>
                      <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      {authMode === 'signup' ? 'Création du compte...' : 'Connexion...'}
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-5 h-5" />
                      {authMode === 'signup' ? 'Créer un compte et rejoindre la waitlist' : 'Se connecter et rejoindre la waitlist'}
                    </>
                  )}
                </button>
              </form>

              <p className="text-xs text-gray-500 text-center">
                {authMode === 'signup'
                  ? 'En créant un compte, vous acceptez de recevoir des informations sur le lancement de cette fonctionnalité.'
                  : 'Vous serez automatiquement ajouté à la liste d\'attente après connexion.'}
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
