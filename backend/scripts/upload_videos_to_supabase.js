/**
 * Script pour uploader les vidéos d'exercices vers Supabase Storage
 * avec conversion automatique en format 720p optimisé.
 *
 * Usage:
 *   node backend/scripts/upload_videos_to_supabase.js [options]
 *
 * Options:
 *   --no-convert    Skip la conversion et upload les fichiers originaux
 *   --keep-temp     Garde les fichiers temporaires après conversion
 *   --no-archive    Ne déplace pas les vidéos vers videos_archives après upload
 *
 * Prérequis:
 *   - Variables d'environnement configurées dans backend/.env
 *   - Vidéos présentes dans /Users/jjublanc/projets_perso/virtual_ai_coach/videos/
 *   - Bucket 'exercise-videos' créé dans Supabase (via migration)
 *   - FFmpeg installé et accessible dans le PATH
 *
 * Spécifications de conversion (Phase 1 du plan d'optimisation):
 *   - Format cible: MP4 H.264 720p (1280x720)
 *   - Paramètres FFmpeg: -c:v libx264 -preset medium -crf 23 -pix_fmt yuv420p -r 30 -g 30
 *   - Réduction de taille attendue: ~70% (de 10-15MB à 2-4MB par vidéo)
 */

const { createClient } = require('@supabase/supabase-js');
const { execSync, spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../.env') });

// Configuration
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const BUCKET_NAME = 'exercise-videos';
const PROJECT_ROOT = process.env.PROJECT_ROOT || path.join(__dirname, '../../videos');
const ARCHIVE_DIR = path.join(__dirname, '../../videos_archives');

// Configuration de conversion 720p
const CONVERSION_CONFIG = {
  enabled: !process.argv.includes('--no-convert'),
  keepTemp: process.argv.includes('--keep-temp'),
  tempDir: path.join(os.tmpdir(), 'video_conversion_720p'),
  // Paramètres FFmpeg optimisés selon le plan d'optimisation
  ffmpegParams: {
    codec: 'libx264',
    preset: 'medium',
    crf: '23',
    pixelFormat: 'yuv420p',
    framerate: '30',
    gopSize: '30',
    resolution: '1280:720',
  }
};

// Configuration d'archivage
const ARCHIVE_CONFIG = {
  enabled: !process.argv.includes('--no-archive')
};

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
 * Vérifie si FFmpeg est disponible
 */
function checkFFmpeg() {
  try {
    execSync('ffmpeg -version', { stdio: 'pipe' });
    return true;
  } catch (error) {
    return false;
  }
}

/**
 * Obtient les informations d'une vidéo avec ffprobe
 */
function getVideoInfo(videoPath) {
  try {
    const result = execSync(
      `ffprobe -v quiet -print_format json -show_format -show_streams "${videoPath}"`,
      { encoding: 'utf-8' }
    );
    return JSON.parse(result);
  } catch (error) {
    console.error(`   ⚠️  Impossible d'obtenir les infos vidéo: ${error.message}`);
    return null;
  }
}

/**
 * Déplace un fichier vidéo vers le dossier d'archives
 */
function moveToArchive(sourcePath, archiveDir) {
  try {
    // Créer le dossier d'archives s'il n'existe pas
    if (!fs.existsSync(archiveDir)) {
      fs.mkdirSync(archiveDir, { recursive: true });
    }

    const filename = path.basename(sourcePath);
    const destinationPath = path.join(archiveDir, filename);

    // Déplacer le fichier
    fs.renameSync(sourcePath, destinationPath);
    console.log(`   📦 Archivé: ${filename} -> videos_archives/`);
    return true;
  } catch (error) {
    console.error(`   ⚠️  Erreur lors de l'archivage: ${error.message}`);
    return false;
  }
}

/**
 * Convertit une vidéo en format 720p MP4 optimisé
 *
 * @param {string} inputPath - Chemin de la vidéo source
 * @param {string} outputPath - Chemin de sortie pour la vidéo convertie
 * @returns {Promise<{success: boolean, originalSize: number, convertedSize: number, error?: string}>}
 */
async function convertVideoTo720p(inputPath, outputPath) {
  const params = CONVERSION_CONFIG.ffmpegParams;
  const originalSize = fs.statSync(inputPath).size;

  // Construction de la commande FFmpeg
  const ffmpegArgs = [
    '-i', inputPath,
    '-c:v', params.codec,
    '-preset', params.preset,
    '-crf', params.crf,
    '-pix_fmt', params.pixelFormat,
    '-vf', `scale=${params.resolution}:force_original_aspect_ratio=decrease,pad=${params.resolution}:-1:-1:color=black`,
    '-r', params.framerate,
    '-g', params.gopSize,
    '-an',  // Pas d'audio
    '-movflags', '+faststart',  // Optimisé pour le streaming web
    '-y',  // Écraser si existe
    outputPath
  ];

  return new Promise((resolve) => {
    console.log(`   🔄 Conversion en 720p...`);

    const ffmpeg = spawn('ffmpeg', ffmpegArgs, { stdio: 'pipe' });
    let stderr = '';

    ffmpeg.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    ffmpeg.on('close', (code) => {
      if (code === 0 && fs.existsSync(outputPath)) {
        const convertedSize = fs.statSync(outputPath).size;
        const reduction = ((originalSize - convertedSize) / originalSize * 100).toFixed(1);
        console.log(`   ✅ Conversion réussie: ${(originalSize / 1024 / 1024).toFixed(2)} MB -> ${(convertedSize / 1024 / 1024).toFixed(2)} MB (-${reduction}%)`);
        resolve({ success: true, originalSize, convertedSize });
      } else {
        console.error(`   ❌ Erreur FFmpeg (code ${code})`);
        // Log les dernières lignes de stderr pour le debug
        const lastLines = stderr.split('\n').slice(-5).join('\n');
        console.error(`   Détails: ${lastLines}`);
        resolve({ success: false, originalSize, convertedSize: 0, error: `FFmpeg exit code ${code}` });
      }
    });

    ffmpeg.on('error', (error) => {
      console.error(`   ❌ Erreur spawn FFmpeg: ${error.message}`);
      resolve({ success: false, originalSize, convertedSize: 0, error: error.message });
    });
  });
}

/**
 * Upload une vidéo vers Supabase Storage
 * (avec conversion optionnelle en 720p)
 */
async function uploadVideo(localPath, remotePath, skipConversion = false) {
  const originalFilename = path.basename(localPath);
  const shouldConvert = CONVERSION_CONFIG.enabled && !skipConversion;

  let fileToUpload = localPath;
  let uploadRemotePath = remotePath;
  let conversionResult = null;

  try {
    console.log(`📤 Traitement: ${originalFilename}`);

    // Afficher les infos de la vidéo source
    const videoInfo = getVideoInfo(localPath);
    if (videoInfo && videoInfo.streams) {
      const videoStream = videoInfo.streams.find(s => s.codec_type === 'video');
      if (videoStream) {
        console.log(`   📊 Source: ${videoStream.width}x${videoStream.height}, ${videoStream.codec_name}`);
      }
    }

    const originalStats = fs.statSync(localPath);
    const originalSizeMB = (originalStats.size / (1024 * 1024)).toFixed(2);
    console.log(`   Taille originale: ${originalSizeMB} MB`);

    // Conversion en 720p si activée
    if (shouldConvert) {
      // Créer le dossier temporaire si nécessaire
      if (!fs.existsSync(CONVERSION_CONFIG.tempDir)) {
        fs.mkdirSync(CONVERSION_CONFIG.tempDir, { recursive: true });
      }

      // Nom du fichier converti (toujours en .mp4)
      const baseName = path.basename(localPath, path.extname(localPath));
      const convertedFilename = `${baseName}_720p.mp4`;
      const convertedPath = path.join(CONVERSION_CONFIG.tempDir, convertedFilename);

      conversionResult = await convertVideoTo720p(localPath, convertedPath);

      if (conversionResult.success) {
        fileToUpload = convertedPath;
        // Mettre à jour le nom du fichier distant pour refléter le format 720p
        uploadRemotePath = convertedFilename;
      } else {
        console.log(`   ⚠️  Conversion échouée, upload du fichier original`);
      }
    }

    // Lire le fichier à uploader
    const fileBuffer = fs.readFileSync(fileToUpload);
    const stats = fs.statSync(fileToUpload);
    const fileSizeMB = (stats.size / (1024 * 1024)).toFixed(2);

    console.log(`   📦 Fichier à uploader: ${path.basename(fileToUpload)} (${fileSizeMB} MB)`);

    // Le content-type est toujours video/mp4 après conversion
    const ext = path.extname(fileToUpload).toLowerCase();
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
      .upload(uploadRemotePath, fileBuffer, {
        contentType: contentType,
        upsert: true  // Remplacer si existe déjà
      });

    if (error) {
      console.error(`   ❌ Erreur upload: ${error.message}`);
      return null;
    }

    // Obtenir l'URL publique
    const { data: publicUrlData } = supabase.storage
      .from(BUCKET_NAME)
      .getPublicUrl(uploadRemotePath);

    console.log(`   ✅ URL: ${publicUrlData.publicUrl}`);

    // Nettoyer le fichier temporaire si demandé
    if (shouldConvert && conversionResult?.success && !CONVERSION_CONFIG.keepTemp) {
      try {
        fs.unlinkSync(fileToUpload);
      } catch (e) {
        // Ignorer les erreurs de suppression
      }
    }

    return {
      publicUrl: publicUrlData.publicUrl,
      originalFile: originalFilename,
      uploadedFile: path.basename(fileToUpload),
      originalSize: originalStats.size,
      uploadedSize: stats.size,
      converted: shouldConvert && conversionResult?.success,
      localPath: localPath
    };

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
  console.log(`📁 Dossier local: ${PROJECT_ROOT}`);
  console.log(`🪣 Bucket: ${BUCKET_NAME}`);
  console.log(`🔄 Conversion 720p: ${CONVERSION_CONFIG.enabled ? 'Activée' : 'Désactivée'}`);
  console.log(`📦 Archivage auto: ${ARCHIVE_CONFIG.enabled ? 'Activé (videos -> videos_archives)' : 'Désactivé'}\n`);

  // Vérifier FFmpeg si la conversion est activée
  if (CONVERSION_CONFIG.enabled) {
    if (!checkFFmpeg()) {
      console.error('❌ Erreur: FFmpeg n\'est pas installé ou pas dans le PATH');
      console.error('   Installer FFmpeg ou utiliser --no-convert pour désactiver la conversion');
      process.exit(1);
    }
    console.log('✅ FFmpeg détecté\n');

    // Créer le dossier temporaire
    if (!fs.existsSync(CONVERSION_CONFIG.tempDir)) {
      fs.mkdirSync(CONVERSION_CONFIG.tempDir, { recursive: true });
    }
    console.log(`📂 Dossier temporaire: ${CONVERSION_CONFIG.tempDir}\n`);
  }

  // Vérifier que le dossier existe
  if (!fs.existsSync(PROJECT_ROOT)) {
    console.error(`❌ Erreur: Dossier ${PROJECT_ROOT} introuvable`);
    process.exit(1);
  }

  // Lister les fichiers vidéo
  const videoFiles = fs.readdirSync(PROJECT_ROOT)
    .filter(file => /\.(mov|mp4|webm|avi)$/i.test(file));

  if (videoFiles.length === 0) {
    console.error('❌ Aucune vidéo trouvée dans le dossier');
    process.exit(1);
  }

  console.log(`📹 ${videoFiles.length} vidéo(s) trouvée(s):\n`);

  // Mapper les vidéos uploadées (ancien nom -> nouvelle URL)
  const uploadResults = {};
  // Statistiques de conversion
  let totalOriginalSize = 0;
  let totalUploadedSize = 0;
  let convertedCount = 0;

  // Upload chaque vidéo
  for (const filename of videoFiles) {
    const localPath = path.join(PROJECT_ROOT, filename);
    const remotePath = filename;  // Sera modifié si converti

    const result = await uploadVideo(localPath, remotePath);

    if (result) {
      // Mapping: ancien nom de fichier -> nouvelle URL
      uploadResults[filename] = result.publicUrl;
      totalOriginalSize += result.originalSize;
      totalUploadedSize += result.uploadedSize;
      if (result.converted) {
        convertedCount++;
      }

      // Déplacer le fichier vers archives après upload réussi (si activé)
      if (ARCHIVE_CONFIG.enabled) {
        moveToArchive(result.localPath, ARCHIVE_DIR);
      }
    }

    console.log('');  // Ligne vide pour lisibilité
  }

  // Résumé
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('📊 RÉSUMÉ');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log(`   Vidéos traitées : ${Object.keys(uploadResults).length}/${videoFiles.length}`);

  if (CONVERSION_CONFIG.enabled) {
    console.log(`   Vidéos converties: ${convertedCount}`);
    const originalMB = (totalOriginalSize / 1024 / 1024).toFixed(2);
    const uploadedMB = (totalUploadedSize / 1024 / 1024).toFixed(2);
    const reduction = totalOriginalSize > 0
      ? ((totalOriginalSize - totalUploadedSize) / totalOriginalSize * 100).toFixed(1)
      : 0;
    console.log(`   Taille originale : ${originalMB} MB`);
    console.log(`   Taille finale    : ${uploadedMB} MB`);
    console.log(`   Réduction totale : ${reduction}%`);
  }
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  // Afficher le mapping pour le script de seed
  console.log('📋 Mapping pour seed_exercises.js:');
  console.log(JSON.stringify(uploadResults, null, 2));

  // Sauvegarder le mapping dans un fichier
  const mappingPath = path.join(__dirname, 'video_urls_mapping.json');
  fs.writeFileSync(mappingPath, JSON.stringify(uploadResults, null, 2));
  console.log(`\n💾 Mapping sauvegardé dans: ${mappingPath}`);

  // Nettoyer le dossier temporaire si demandé
  if (CONVERSION_CONFIG.enabled && !CONVERSION_CONFIG.keepTemp) {
    try {
      fs.rmSync(CONVERSION_CONFIG.tempDir, { recursive: true, force: true });
      console.log(`🧹 Dossier temporaire nettoyé`);
    } catch (e) {
      // Ignorer les erreurs de suppression
    }
  }
}

// Exécuter
main().catch(error => {
  console.error('❌ Erreur fatale:', error);
  process.exit(1);
});
