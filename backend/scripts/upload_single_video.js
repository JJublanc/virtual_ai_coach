/**
 * Script pour uploader une seule vidéo vers Supabase Storage
 * avec conversion automatique en format 720p optimisé.
 *
 * Usage:
 *   node backend/scripts/upload_single_video.js <filename> [options]
 *
 * Exemple:
 *   node backend/scripts/upload_single_video.js commandos.mov
 *
 * Options:
 *   --no-convert    Skip la conversion et upload le fichier original
 *
 * Prérequis:
 *   - Variables d'environnement configurées dans backend/.env
 *   - Vidéo présente dans /Users/jjublanc/projets_perso/virtual_ai_coach/videos/
 *   - Bucket 'exercise-videos' créé dans Supabase
 *   - FFmpeg installé et accessible dans le PATH (pour conversion)
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
const VIDEOS_DIR = '/Users/jjublanc/projets_perso/virtual_ai_coach/videos';

// Configuration de conversion 720p
const CONVERSION_CONFIG = {
  enabled: !process.argv.includes('--no-convert'),
  tempDir: path.join(os.tmpdir(), 'video_conversion_single'),
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

// Validation des variables d'environnement
if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
  console.error('❌ Erreur: Variables d\'environnement manquantes');
  console.error('   SUPABASE_URL:', SUPABASE_URL ? '✓' : '✗');
  console.error('   SUPABASE_SERVICE_ROLE_KEY:', SUPABASE_SERVICE_ROLE_KEY ? '✓' : '✗');
  process.exit(1);
}

// Récupérer le nom du fichier depuis les arguments
const filename = process.argv[2];
if (!filename) {
  console.error('❌ Erreur: Nom de fichier manquant');
  console.error('   Usage: node upload_single_video.js <filename>');
  console.error('   Exemple: node upload_single_video.js commandos.mov');
  process.exit(1);
}

// Créer le client Supabase
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
 * Convertit une vidéo en format 720p MP4 optimisé
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
 */
async function uploadVideo(localPath) {
  const originalFilename = path.basename(localPath);
  const shouldConvert = CONVERSION_CONFIG.enabled;

  let fileToUpload = localPath;
  let uploadRemotePath = originalFilename;
  let conversionResult = null;

  try {
    console.log(`\n📤 Traitement: ${originalFilename}`);

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
    console.log(`   📦 Taille originale: ${originalSizeMB} MB`);

    // Conversion en 720p si activée
    if (shouldConvert) {
      if (!fs.existsSync(CONVERSION_CONFIG.tempDir)) {
        fs.mkdirSync(CONVERSION_CONFIG.tempDir, { recursive: true });
      }

      const baseName = path.basename(localPath, path.extname(localPath));
      const convertedFilename = `${baseName}_720p.mp4`;
      const convertedPath = path.join(CONVERSION_CONFIG.tempDir, convertedFilename);

      conversionResult = await convertVideoTo720p(localPath, convertedPath);

      if (conversionResult.success) {
        fileToUpload = convertedPath;
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

    // Déterminer le content-type
    const ext = path.extname(fileToUpload).toLowerCase();
    const contentTypeMap = {
      '.mov': 'video/quicktime',
      '.mp4': 'video/mp4',
      '.webm': 'video/webm',
      '.avi': 'video/x-msvideo'
    };
    const contentType = contentTypeMap[ext] || 'video/mp4';

    // Upload vers Supabase Storage
    console.log(`   ⬆️  Upload vers Supabase Storage...`);
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

    console.log(`   ✅ Upload réussi !`);
    console.log(`   🔗 URL: ${publicUrlData.publicUrl}`);

    // Nettoyer le fichier temporaire
    if (shouldConvert && conversionResult?.success) {
      try {
        fs.unlinkSync(fileToUpload);
        fs.rmdirSync(CONVERSION_CONFIG.tempDir, { recursive: true });
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
      converted: shouldConvert && conversionResult?.success
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
  console.log('🚀 Upload d\'une vidéo vers Supabase Storage');
  console.log(`🪣 Bucket: ${BUCKET_NAME}`);
  console.log(`🔄 Conversion 720p: ${CONVERSION_CONFIG.enabled ? 'Activée' : 'Désactivée'}`);

  // Vérifier FFmpeg si la conversion est activée
  if (CONVERSION_CONFIG.enabled) {
    if (!checkFFmpeg()) {
      console.error('\n❌ Erreur: FFmpeg n\'est pas installé ou pas dans le PATH');
      console.error('   Installer FFmpeg ou utiliser --no-convert pour désactiver la conversion');
      process.exit(1);
    }
    console.log('✅ FFmpeg détecté');
  }

  // Vérifier que le fichier existe
  const videoPath = path.join(VIDEOS_DIR, filename);
  if (!fs.existsSync(videoPath)) {
    console.error(`\n❌ Erreur: Fichier introuvable: ${videoPath}`);
    process.exit(1);
  }

  // Upload la vidéo
  const result = await uploadVideo(videoPath);

  if (result) {
    console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('📊 RÉSUMÉ');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log(`   ✅ Vidéo uploadée avec succès`);
    console.log(`   📁 Fichier original : ${result.originalFile}`);
    console.log(`   📦 Fichier uploadé  : ${result.uploadedFile}`);
    console.log(`   💾 Taille originale : ${(result.originalSize / 1024 / 1024).toFixed(2)} MB`);
    console.log(`   💾 Taille finale    : ${(result.uploadedSize / 1024 / 1024).toFixed(2)} MB`);
    if (result.converted) {
      const reduction = ((result.originalSize - result.uploadedSize) / result.originalSize * 100).toFixed(1);
      console.log(`   📉 Réduction        : ${reduction}%`);
    }
    console.log(`   🔗 URL publique     : ${result.publicUrl}`);
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  } else {
    console.error('\n❌ Échec de l\'upload');
    process.exit(1);
  }
}

// Exécuter
main().catch(error => {
  console.error('❌ Erreur fatale:', error);
  process.exit(1);
});
