-- Migration: Ajout du trigger pour mettre à jour automatiquement updated_at

-- Le trigger updated_at utilise la fonction update_updated_at_column()
-- qui a été créée dans la migration 20241109120003_add_updated_at_trigger.sql

-- Créer le trigger pour la table exercises
CREATE TRIGGER update_exercises_updated_at
  BEFORE UPDATE ON exercises
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Commentaire
COMMENT ON TRIGGER update_exercises_updated_at ON exercises
  IS 'Met à jour automatiquement le champ updated_at lors des modifications';
