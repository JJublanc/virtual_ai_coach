-- Schema SQL pour Supabase - Table early_access_signups
-- Ce fichier doit être exécuté dans le SQL Editor de votre projet Supabase

-- Création de la table early_access_signups
CREATE TABLE IF NOT EXISTS early_access_signups (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  feature_interest VARCHAR(100) NOT NULL,
  comment TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index pour recherche rapide par email
CREATE INDEX IF NOT EXISTS idx_early_access_email ON early_access_signups(email);

-- Index pour recherche par fonctionnalité
CREATE INDEX IF NOT EXISTS idx_early_access_feature ON early_access_signups(feature_interest);

-- Activer Row Level Security (RLS)
ALTER TABLE early_access_signups ENABLE ROW LEVEL SECURITY;

-- Politique: Tout le monde peut insérer (anonyme)
CREATE POLICY "Allow public insert" ON early_access_signups
  FOR INSERT
  TO anon
  WITH CHECK (true);

-- Politique: Seuls les utilisateurs authentifiés peuvent lire
-- Note: À ajuster selon vos besoins de sécurité
CREATE POLICY "Allow authenticated read" ON early_access_signups
  FOR SELECT
  TO authenticated
  USING (true);

-- Fonction pour mettre à jour automatiquement updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger pour mettre à jour updated_at automatiquement
CREATE TRIGGER update_early_access_signups_updated_at
  BEFORE UPDATE ON early_access_signups
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Commentaires pour documentation
COMMENT ON TABLE early_access_signups IS 'Stockage des inscriptions early access pour les fonctionnalités à venir';
COMMENT ON COLUMN early_access_signups.email IS 'Email de l''utilisateur (unique)';
COMMENT ON COLUMN early_access_signups.first_name IS 'Prénom de l''utilisateur';
COMMENT ON COLUMN early_access_signups.last_name IS 'Nom de l''utilisateur';
COMMENT ON COLUMN early_access_signups.feature_interest IS 'Nom de la fonctionnalité qui intéresse l''utilisateur';
COMMENT ON COLUMN early_access_signups.comment IS 'Commentaire optionnel de l''utilisateur';
