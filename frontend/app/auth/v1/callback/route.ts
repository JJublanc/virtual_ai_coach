// app/auth/v1/callback/route.ts
import { NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { createClient } from '@supabase/supabase-js'

export async function GET(request: Request) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')
  const error = requestUrl.searchParams.get('error')
  const errorDescription = requestUrl.searchParams.get('error_description')

  console.log('[OAuth Callback] URL:', requestUrl.toString())
  console.log('[OAuth Callback] Code présent:', !!code)
  console.log('[OAuth Callback] Error:', error)
  console.log('[OAuth Callback] Error Description:', errorDescription)

  // Récupérer la feature depuis les cookies
  const cookieStore = await cookies()
  const featureCookie = cookieStore.get('pending_feature')
  const feature = featureCookie?.value

  console.log('[OAuth Callback] Feature depuis cookie:', feature)
  console.log('[OAuth Callback] Tous les cookies:', cookieStore.getAll())

  if (code) {
    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    )

    const { data, error } = await supabase.auth.exchangeCodeForSession(code)

    console.log('[OAuth Callback] Exchange réussi:', !!data.session)
    console.log('[OAuth Callback] Erreur:', error)

    if (!error && data.session) {
      console.log('[OAuth Callback] Redirection vers:', feature ? `/auth/complete-signup?feature=${feature}` : '/')

      // Créer la réponse
      const response = feature
        ? NextResponse.redirect(new URL(`/auth/complete-signup?feature=${encodeURIComponent(feature)}`, requestUrl.origin))
        : NextResponse.redirect(new URL('/', requestUrl.origin))

      // Supprimer le cookie après utilisation
      if (feature) {
        response.cookies.delete('pending_feature')
      }

      return response
    }
  }

  console.log('[OAuth Callback] Fallback: redirection vers /')
  // Redirect to home page after successful authentication
  return NextResponse.redirect(new URL('/', requestUrl.origin))
}
