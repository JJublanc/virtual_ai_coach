/**
 * Script pour insérer les exercices dans Supabase PostgreSQL
 *
 * Usage:
 *   node backend/scripts/seed_exercises.js
 *
 * Prérequis:
 *   - Variables d'environnement configurées dans backend/.env
 *   - Table 'exercises' créée (via migration)
 *   - Vidéos uploadées dans Supabase Storage
 *   - Fichier video_urls_mapping.json généré par upload_videos_to_supabase.js
 */

const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../.env') });

// Configuration
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

// Chemins des fichiers
const EXERCISES_JSON_PATH = path.join(__dirname, '../app/models/exercises.json');
const VIDEO_MAPPING_PATH = path.join(__dirname, 'video_urls_mapping.json');

// Validation des variables d'environnement
if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
  console.error('❌ Erreur: Variables d\'environnement manquantes');
  console.error('   SUPABASE_URL:', SUPABASE_URL ? '✓' : '✗');
  console.error('   SUPABASE_SERVICE_ROLE_KEY:', SUPABASE_SERVICE_ROLE_KEY ? '✓' : '✗');
  process.exit(1);
}

// Créer le client Supabase avec service role key
const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
  auth: {
    autoRefreshToken: false,
    persistSession: false
  }
});

/**
 * Charge le mapping des URLs vidéos
 */
function loadVideoMapping() {
  if (!fs.existsSync(VIDEO_MAPPING_PATH)) {
    console.warn('⚠️  Fichier video_urls_mapping.json introuvable');
    console.warn('   Exécutez d\'abord: node backend/scripts/upload_videos_to_supabase.js');
    return {};
  }

  const content = fs.readFileSync(VIDEO_MAPPING_PATH, 'utf-8');
  return JSON.parse(content);
}

/**
 * Charge les exercices depuis exercises.json
 */
function loadExercises() {
  if (!fs.existsSync(EXERCISES_JSON_PATH)) {
    console.error(`❌ Erreur: Fichier ${EXERCISES_JSON_PATH} introuvable`);
    process.exit(1);
  }

  const content = fs.readFileSync(EXERCISES_JSON_PATH, 'utf-8');
  return JSON.parse(content);
}

/**
 * Extrait le nom de fichier depuis un chemin local
 */
function extractFilename(videoPath) {
  if (!videoPath) return null;
  return path.basename(videoPath);
}

/**
 * Mappe un exercice JSON vers le format Supabase
 */
function mapExerciseToSupabase(exercise, videoMapping) {
  const filename = extractFilename(exercise.video_url);
  const supabaseUrl = videoMapping[filename];

  if (!supabaseUrl) {
    console.warn(`⚠️  URL Supabase introuvable pour: ${filename}`);
    console.warn(`   Utilisation du chemin local par défaut`);
  }

  return {
    id: exercise.id,
    name: exercise.name,
    description: exercise.description,
    icon: exercise.icon,
    video_url: supabaseUrl || exercise.video_url,  // Fallback sur chemin local
    default_duration: exercise.default_duration,
    difficulty: exercise.difficulty,
    has_jump: exercise.has_jump,
    access_tier: exercise.access_tier,
    metadata: exercise.metadata
  };
}

/**
 * Insère un exercice dans Supabase
 */
async function insertExercise(exercise) {
  try {
    console.log(`📝 Insertion: ${exercise.name}`);
    console.log(`   ID: ${exercise.id}`);
    console.log(`   Video: ${exercise.video_url.substring(0, 80)}...`);

    const { data, error } = await supabase
      .from('exercises')
      .upsert(exercise, {
        onConflict: 'id',
        ignoreDuplicates: false
      })
      .select();

    if (error) {
      console.error(`   ❌ Erreur: ${error.message}`);
      return false;
    }

    console.log(`   ✅ Succès`);
    return true;

  } catch (error) {
    console.error(`   ❌ Exception: ${error.message}`);
    return false;
  }
}

/**
 * Fonction principale
 */
async function main() {
  console.log('🚀 Seed des exercices dans Supabase PostgreSQL\n');

  // Charger le mapping des URLs vidéos
  console.log('📹 Chargement du mapping vidéos...');
  const videoMapping = loadVideoMapping();
  console.log(`   ${Object.keys(videoMapping).length} vidéo(s) mappée(s)\n`);

  // Charger les exercices depuis JSON
  console.log('📂 Chargement des exercices depuis exercises.json...');
  const exercises = loadExercises();
  console.log(`   ${exercises.length} exercice(s) trouvé(s)\n`);

  // Mapper et insérer chaque exercice
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  let successCount = 0;
  let failCount = 0;

  for (const exercise of exercises) {
    const mappedExercise = mapExerciseToSupabase(exercise, videoMapping);
    const success = await insertExercise(mappedExercise);

    if (success) {
      successCount++;
    } else {
      failCount++;
    }

    console.log('');  // Ligne vide pour lisibilité
  }

  // Résumé
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log(`✅ Seed terminé: ${successCount} succès, ${failCount} échecs\n`);

  // Vérifier le nombre d'exercices dans la base
  const { count, error } = await supabase
    .from('exercises')
    .select('*', { count: 'exact', head: true });

  if (!error) {
    console.log(`📊 Total dans la base: ${count} exercice(s)`);
  }
}

// Exécuter
main().catch(error => {
  console.error('❌ Erreur fatale:', error);
  process.exit(1);
});
