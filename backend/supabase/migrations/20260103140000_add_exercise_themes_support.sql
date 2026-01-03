-- Migration: Ajout du support des thèmes d'exercices pour la génération par blocs
-- Le champ themes sera stocké dans metadata->themes (JSONB array)
-- Thèmes disponibles: upper_body, legs, cardio, abs, full_body

-- Créer un index GIN pour rechercher efficacement par thème
-- Cet index permet de faire des recherches rapides sur metadata->'themes'
CREATE INDEX IF NOT EXISTS idx_exercises_themes
ON exercises USING GIN ((metadata->'themes'));

-- Créer une fonction pour valider les thèmes
CREATE OR REPLACE FUNCTION validate_exercise_themes()
RETURNS TRIGGER AS $$
DECLARE
  theme TEXT;
  valid_themes TEXT[] := ARRAY['upper_body', 'legs', 'cardio', 'abs', 'full_body'];
BEGIN
  -- Si metadata->themes existe et n'est pas null
  IF NEW.metadata ? 'themes' AND NEW.metadata->'themes' IS NOT NULL THEN
    -- Vérifier chaque thème dans le tableau
    FOR theme IN SELECT jsonb_array_elements_text(NEW.metadata->'themes')
    LOOP
      IF NOT (theme = ANY(valid_themes)) THEN
        RAISE EXCEPTION 'Invalid theme: %. Valid themes are: %', theme, valid_themes;
      END IF;
    END LOOP;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Créer un trigger pour valider les thèmes à l'insertion/update
DROP TRIGGER IF EXISTS validate_themes_trigger ON exercises;
CREATE TRIGGER validate_themes_trigger
  BEFORE INSERT OR UPDATE ON exercises
  FOR EACH ROW
  EXECUTE FUNCTION validate_exercise_themes();

-- Commentaires pour documentation
COMMENT ON INDEX idx_exercises_themes IS 'Index GIN pour recherche rapide par thèmes d''exercices';
COMMENT ON FUNCTION validate_exercise_themes() IS 'Valide que les thèmes sont dans la liste autorisée';

-- Note: Les exercices existants devront être mis à jour avec un script de migration
-- pour ajouter le champ themes basé sur leurs muscles_targeted
