// app/api/early-access/signup/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'
import { z } from 'zod'

// Schéma de validation avec Zod
const signupSchema = z.object({
  email: z.string().email({ message: 'Email invalide' }),
  firstName: z.string().min(1, { message: 'Le prénom est requis' }).max(100),
  lastName: z.string().min(1, { message: 'Le nom est requis' }).max(100),
  featureInterest: z.string().min(1, { message: 'La fonctionnalité d\'intérêt est requise' }),
  comment: z.string().optional(),
})

export async function POST(request: NextRequest) {
  try {
    // Parse le body de la requête
    const body = await request.json()

    // Validation des données
    const validationResult = signupSchema.safeParse(body)

    if (!validationResult.success) {
      return NextResponse.json(
        {
          error: 'Données invalides',
          details: validationResult.error.flatten().fieldErrors
        },
        { status: 400 }
      )
    }

    const { email, firstName, lastName, featureInterest, comment } = validationResult.data

    // Insertion dans Supabase
    const { data, error } = await supabase
      .from('early_access_signups')
      .insert([
        {
          email,
          first_name: firstName,
          last_name: lastName,
          feature_interest: featureInterest,
          comment: comment || null,
        }
      ])
      .select()
      .single()

    // Gestion des erreurs Supabase
    if (error) {
      // Erreur de contrainte unique (email déjà existant)
      if (error.code === '23505') {
        return NextResponse.json(
          { error: 'Cet email est déjà inscrit' },
          { status: 409 }
        )
      }

      console.error('Supabase error:', error)
      return NextResponse.json(
        { error: 'Erreur lors de l\'inscription' },
        { status: 500 }
      )
    }

    // Succès
    return NextResponse.json(
      {
        message: 'Inscription réussie',
        data: {
          id: data.id,
          email: data.email,
          featureInterest: data.feature_interest,
        }
      },
      { status: 201 }
    )

  } catch (error) {
    console.error('Unexpected error:', error)
    return NextResponse.json(
      { error: 'Erreur serveur inattendue' },
      { status: 500 }
    )
  }
}

// Optionnel: GET pour récupérer les inscriptions (admin uniquement)
export async function GET(request: NextRequest) {
  try {
    const { data, error } = await supabase
      .from('early_access_signups')
      .select('*')
      .order('created_at', { ascending: false })

    if (error) {
      console.error('Supabase error:', error)
      return NextResponse.json(
        { error: 'Erreur lors de la récupération des données' },
        { status: 500 }
      )
    }

    return NextResponse.json({ data }, { status: 200 })

  } catch (error) {
    console.error('Unexpected error:', error)
    return NextResponse.json(
      { error: 'Erreur serveur inattendue' },
      { status: 500 }
    )
  }
}
