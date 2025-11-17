/**
 * Script pour uploader les vidéos d'exercices vers Supabase Storage
 *
 * Usage:
 *   node backend/scripts/upload_videos_to_supabase.js
 *
 * Prérequis:
 *   - Variables d'environnement configurées dans backend/.env
 *   - Vidéos présentes dans /Users/jjublanc/projets_perso/virtual_ai_coach/videos/
 *   - Bucket 'exercise-videos' créé dans Supabase (via migration)
 */

const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../.env') });

// Configuration
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const BUCKET_NAME = 'exercise-videos';
const VIDEOS_DIR = '/Users/jjublanc/projets_perso/virtual_ai_coach/videos';

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
 * Upload une vidéo vers Supabase Storage
 */
async function uploadVideo(localPath, remotePath) {
  try {
    console.log(`📤 Upload: ${path.basename(localPath)} -> ${remotePath}`);

    // Lire le fichier
    const fileBuffer = fs.readFileSync(localPath);
    const stats = fs.statSync(localPath);
    const fileSizeMB = (stats.size / (1024 * 1024)).toFixed(2);

    console.log(`   Taille: ${fileSizeMB} MB`);

    // Déterminer le content-type
    const ext = path.extname(localPath).toLowerCase();
    const contentTypeMap = {
      '.mov': 'video/quicktime',
      '.mp4': 'video/mp4',
      '.webm': 'video/webm',
      '.avi': 'video/x-msvideo'
    };
    const contentType = contentTypeMap[ext] || 'video/mp4';

    // Upload vers Supabase Storage
    const { data, error } = await supabase.storage
      .from(BUCKET_NAME)
      .upload(remotePath, fileBuffer, {
        contentType: contentType,
        upsert: true  // Remplacer si existe déjà
      });

    if (error) {
      console.error(`   ❌ Erreur: ${error.message}`);
      return null;
    }

    // Obtenir l'URL publique
    const { data: publicUrlData } = supabase.storage
      .from(BUCKET_NAME)
      .getPublicUrl(remotePath);

    console.log(`   ✅ URL: ${publicUrlData.publicUrl}`);

    return publicUrlData.publicUrl;

  } catch (error) {
    console.error(`   ❌ Exception: ${error.message}`);
    return null;
  }
}

/**
 * Fonction principale
 */
async function main() {
  console.log('🚀 Upload des vidéos vers Supabase Storage\n');
  console.log(`📁 Dossier local: ${VIDEOS_DIR}`);
  console.log(`🪣 Bucket: ${BUCKET_NAME}\n`);

  // Vérifier que le dossier existe
  if (!fs.existsSync(VIDEOS_DIR)) {
    console.error(`❌ Erreur: Dossier ${VIDEOS_DIR} introuvable`);
    process.exit(1);
  }

  // Lister les fichiers vidéo
  const videoFiles = fs.readdirSync(VIDEOS_DIR)
    .filter(file => /\.(mov|mp4|webm|avi)$/i.test(file));

  if (videoFiles.length === 0) {
    console.error('❌ Aucune vidéo trouvée dans le dossier');
    process.exit(1);
  }

  console.log(`📹 ${videoFiles.length} vidéo(s) trouvée(s):\n`);

  // Mapper les vidéos uploadées
  const uploadResults = {};

  // Upload chaque vidéo
  for (const filename of videoFiles) {
    const localPath = path.join(VIDEOS_DIR, filename);
    const remotePath = filename;  // Garder le même nom

    const publicUrl = await uploadVideo(localPath, remotePath);

    if (publicUrl) {
      uploadResults[filename] = publicUrl;
    }

    console.log('');  // Ligne vide pour lisibilité
  }

  // Résumé
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log(`✅ Upload terminé: ${Object.keys(uploadResults).length}/${videoFiles.length} succès\n`);

  // Afficher le mapping pour le script de seed
  console.log('📋 Mapping pour seed_exercises.js:');
  console.log(JSON.stringify(uploadResults, null, 2));

  // Sauvegarder le mapping dans un fichier
  const mappingPath = path.join(__dirname, 'video_urls_mapping.json');
  fs.writeFileSync(mappingPath, JSON.stringify(uploadResults, null, 2));
  console.log(`\n💾 Mapping sauvegardé dans: ${mappingPath}`);
}

// Exécuter
main().catch(error => {
  console.error('❌ Erreur fatale:', error);
  process.exit(1);
});
