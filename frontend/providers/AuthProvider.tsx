'use client'

import { createContext, useContext, useEffect, useState, useRef } from 'react'
import { User, Session, AuthError, Provider } from '@supabase/supabase-js'
import { supabase } from '@/lib/supabase'
import { useRouter } from 'next/navigation'

interface AuthContextType {
  user: User | null
  session: Session | null
  loading: boolean
  signUp: (email: string, password: string) => Promise<{ error: AuthError | null }>
  signIn: (email: string, password: string) => Promise<{ error: AuthError | null }>
  signInWithProvider: (provider: Provider, featureName?: string) => Promise<{ error: AuthError | null }>
  signOut: () => Promise<{ error: AuthError | null }>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Helper pour récupérer un cookie
function getCookie(name: string): string | null {
  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)
  if (parts.length === 2) return parts.pop()?.split(';').shift() || null
  return null
}

// Helper pour supprimer un cookie
function deleteCookie(name: string) {
  document.cookie = `${name}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT`
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()
  const hasProcessedOAuth = useRef(false)

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      console.log('[AuthProvider] Event:', event)
      console.log('[AuthProvider] Session:', !!session)
      console.log('[AuthProvider] hasProcessedOAuth:', hasProcessedOAuth.current)

      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)

      // Gérer l'inscription à la waitlist après OAuth
      if (event === 'SIGNED_IN' && session?.user && !hasProcessedOAuth.current) {
        hasProcessedOAuth.current = true

        // Récupérer la feature depuis le cookie
        const featureName = getCookie('pending_feature')
        console.log('[AuthProvider] Feature depuis cookie:', featureName)

        if (featureName) {
          // Vérifier si l'utilisateur est déjà dans la waitlist pour cette feature
          const { data: existingEntry } = await supabase
            .from('waitlist')
            .select('id')
            .eq('user_id', session.user.id)
            .eq('feature_name', decodeURIComponent(featureName))
            .maybeSingle()

          if (!existingEntry) {
            // Ajouter à la waitlist
            const { error: insertError } = await supabase
              .from('waitlist')
              .insert({
                user_id: session.user.id,
                feature_name: decodeURIComponent(featureName),
                comment: null
              })

            if (insertError) {
              console.error('[AuthProvider] Erreur insertion waitlist:', insertError)
            } else {
              console.log('[AuthProvider] Utilisateur ajouté à la waitlist pour:', featureName)
            }
          } else {
            console.log('[AuthProvider] Utilisateur déjà dans la waitlist pour:', featureName)
          }

          // Supprimer le cookie et rediriger vers la page de commentaire
          deleteCookie('pending_feature')
          router.push(`/auth/complete-signup?feature=${encodeURIComponent(featureName)}`)
        } else {
          // Pas de feature, redirection simple vers la home
          router.push('/')
        }
      }
    })

    return () => subscription.unsubscribe()
  }, [router])

  const signUp = async (email: string, password: string) => {
    const { error } = await supabase.auth.signUp({
      email,
      password,
    })
    return { error }
  }

  const signIn = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })
    return { error }
  }

  const signInWithProvider = async (provider: Provider, featureName?: string) => {
    // Stocker la feature dans un cookie avant la redirection OAuth
    if (featureName) {
      document.cookie = `pending_feature=${encodeURIComponent(featureName)}; path=/; max-age=600; SameSite=Lax`
    }

    const { error } = await supabase.auth.signInWithOAuth({
      provider,
      options: {
        redirectTo: `${window.location.origin}/auth/v1/callback`,
      },
    })
    return { error }
  }

  const signOut = async () => {
    const { error } = await supabase.auth.signOut()
    return { error }
  }

  const value = {
    user,
    session,
    loading,
    signUp,
    signIn,
    signInWithProvider,
    signOut,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
