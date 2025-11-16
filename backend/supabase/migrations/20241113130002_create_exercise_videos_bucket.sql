-- Migration: Création du bucket Supabase Storage pour les vidéos d'exercices

-- Créer le bucket exercise-videos avec limite de 200MB
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'exercise-videos',
  'exercise-videos',
  true,  -- Bucket public
  209715200,  -- 200MB max par fichier (82MB x 3 vidéos)
  ARRAY['video/quicktime', 'video/mp4', 'video/webm', 'video/x-msvideo']
)
ON CONFLICT (id) DO NOTHING;

-- Politique RLS: Lecture publique pour tous
CREATE POLICY "Public read access on exercise-videos"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'exercise-videos');

-- Politique RLS: Upload authentifié uniquement
CREATE POLICY "Authenticated upload on exercise-videos"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'exercise-videos');

-- Politique RLS: Update authentifié uniquement
CREATE POLICY "Authenticated update on exercise-videos"
ON storage.objects FOR UPDATE
TO authenticated
USING (bucket_id = 'exercise-videos');

-- Politique RLS: Delete authentifié uniquement
CREATE POLICY "Authenticated delete on exercise-videos"
ON storage.objects FOR DELETE
TO authenticated
USING (bucket_id = 'exercise-videos');
