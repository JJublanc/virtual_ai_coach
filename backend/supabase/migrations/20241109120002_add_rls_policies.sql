-- Migration: Add RLS policies for early_access_signups
-- Created: 2024-11-09 12:00:02
-- Description: Configure Row Level Security policies for the early_access_signups table

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

-- Politique: Empêcher les mises à jour et suppressions
-- (optionnel, par défaut RLS bloque déjà)
CREATE POLICY "Deny updates" ON early_access_signups
  FOR UPDATE
  TO public
  USING (false);

CREATE POLICY "Deny deletes" ON early_access_signups
  FOR DELETE
  TO public
  USING (false);
