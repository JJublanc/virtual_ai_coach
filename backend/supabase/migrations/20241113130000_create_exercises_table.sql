-- Migration: Création de la table exercises pour stocker les métadonnées des exercices
-- Les vidéos seront stockées dans Supabase Storage (bucket exercise-videos)

-- Création de la table exercises
CREATE TABLE IF NOT EXISTS exercises (
  id UUID PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  description TEXT NOT NULL,
  icon VARCHAR(10) NOT NULL,
  video_url TEXT NOT NULL,
  default_duration INTEGER DEFAULT 60,
  difficulty VARCHAR(20) NOT NULL CHECK (difficulty IN ('easy', 'medium', 'hard')),
  has_jump BOOLEAN DEFAULT false,
  access_tier VARCHAR(20) DEFAULT 'free' CHECK (access_tier IN ('free', 'premium', 'pro')),
  metadata JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index pour recherche rapide par nom
CREATE INDEX IF NOT EXISTS idx_exercises_name ON exercises(name);

-- Index pour recherche par difficulté
CREATE INDEX IF NOT EXISTS idx_exercises_difficulty ON exercises(difficulty);

-- Index pour recherche par access_tier
CREATE INDEX IF NOT EXISTS idx_exercises_access_tier ON exercises(access_tier);

-- Index sur le champ metadata (JSONB)
CREATE INDEX IF NOT EXISTS idx_exercises_metadata ON exercises USING GIN (metadata);

-- Activer Row Level Security (RLS)
ALTER TABLE exercises ENABLE ROW LEVEL SECURITY;

-- Politique: Lecture publique pour tous (pas d'authentification requise)
CREATE POLICY "Public read access" ON exercises
  FOR SELECT
  TO anon, authenticated
  USING (true);

-- Politique: Seuls les utilisateurs authentifiés peuvent insérer
CREATE POLICY "Authenticated insert" ON exercises
  FOR INSERT
  TO authenticated
  WITH CHECK (true);

-- Politique: Seuls les utilisateurs authentifiés peuvent mettre à jour
CREATE POLICY "Authenticated update" ON exercises
  FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- Politique: Seuls les utilisateurs authentifiés peuvent supprimer
CREATE POLICY "Authenticated delete" ON exercises
  FOR DELETE
  TO authenticated
  USING (true);

-- Commentaires pour documentation
COMMENT ON TABLE exercises IS 'Stockage des métadonnées des exercices (vidéos dans Storage)';
COMMENT ON COLUMN exercises.id IS 'Identifiant unique de l''exercice (UUID)';
COMMENT ON COLUMN exercises.name IS 'Nom de l''exercice';
COMMENT ON COLUMN exercises.description IS 'Description détaillée de l''exercice';
COMMENT ON COLUMN exercises.icon IS 'Emoji représentant l''exercice';
COMMENT ON COLUMN exercises.video_url IS 'URL de la vidéo dans Supabase Storage';
COMMENT ON COLUMN exercises.default_duration IS 'Durée par défaut en secondes';
COMMENT ON COLUMN exercises.difficulty IS 'Niveau de difficulté (easy, medium, hard)';
COMMENT ON COLUMN exercises.has_jump IS 'Indique si l''exercice contient des sauts';
COMMENT ON COLUMN exercises.access_tier IS 'Niveau d''accès (free, premium, pro)';
COMMENT ON COLUMN exercises.metadata IS 'Métadonnées JSON (muscles, équipement, calories)';
