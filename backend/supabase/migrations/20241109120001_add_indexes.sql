-- Migration: Add indexes for early_access_signups
-- Created: 2024-11-09 12:00:01
-- Description: Add performance indexes for email lookup and feature interest filtering

-- Index pour recherche rapide par email
CREATE INDEX IF NOT EXISTS idx_early_access_email ON early_access_signups(email);

-- Index pour recherche par fonctionnalité
CREATE INDEX IF NOT EXISTS idx_early_access_feature ON early_access_signups(feature_interest);

-- Index pour tri par date de création
CREATE INDEX IF NOT EXISTS idx_early_access_created_at ON early_access_signups(created_at DESC);
