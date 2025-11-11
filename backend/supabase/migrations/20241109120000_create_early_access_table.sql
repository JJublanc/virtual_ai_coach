-- Migration: Create early_access_signups table
-- Created: 2024-11-09 12:00:00
-- Description: Initial table for storing early access user signups

-- Create the early_access_signups table
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

-- Add comments for documentation
COMMENT ON TABLE early_access_signups IS 'Stockage des inscriptions early access pour les fonctionnalités à venir';
COMMENT ON COLUMN early_access_signups.email IS 'Email de l''utilisateur (unique)';
COMMENT ON COLUMN early_access_signups.first_name IS 'Prénom de l''utilisateur';
COMMENT ON COLUMN early_access_signups.last_name IS 'Nom de l''utilisateur';
COMMENT ON COLUMN early_access_signups.feature_interest IS 'Nom de la fonctionnalité qui intéresse l''utilisateur';
COMMENT ON COLUMN early_access_signups.comment IS 'Commentaire optionnel de l''utilisateur';
