# Guide - Ajouter un Nouvel Exercice

Ce guide explique comment ajouter un nouvel exercice à votre application après la migration vers Supabase.

## 📋 Prérequis

- [x] Vidéo de l'exercice prête (format MOV, MP4 ou WEBM)
- [x] Variables d'environnement configurées dans `backend/.env`
- [x] Migrations Supabase appliquées
- [x] Bucket `exercise-videos` créé

## 🎯 Vue d'ensemble

Pour ajouter un exercice, vous devez :

1. **Uploader la vidéo** dans Supabase Storage
2. **Insérer les métadonnées** dans la table PostgreSQL `exercises`
3. **Vérifier** que l'exercice apparaît dans l'API

## 📹 Étape 1 : Préparer la vidéo

### 1.1 Vérifier le format

Votre vidéo doit être :
- **Format** : MOV, MP4, WEBM ou AVI
- **Taille max** : 200 MB (configuré dans le bucket)
- **Résolution** : 1920x1080 recommandée
- **Codec** : H.264 recommandé

### 1.2 Optimiser la vidéo (optionnel)

Pour réduire la taille :

```bash
ffmpeg -i input.mov -vcodec h264 -crf 28 -preset fast output.mp4
```

Cela peut réduire la taille de ~80MB à ~20-30MB sans perte de qualité notable.

### 1.3 Nommer le fichier

Convention recommandée :
- **Minuscules** : `exercise_name.mov`
- **Underscores** : `mountain_climbers.mov`
- **Pas d'espaces** : ✅ `push_ups.mov` ❌ `Push Ups.mov`

## 📤 Étape 2 : Uploader la vidéo vers Supabase Storage

### Option A : Via le Dashboard Supabase (recommandé pour un seul exercice)

1. Allez sur [votre projet Supabase](https://app.supabase.com)
2. Cliquez sur **Storage** dans le menu
3. Sélectionnez le bucket **`exercise-videos`**
4. Cliquez sur **Upload** ou glissez-déposez votre vidéo
5. Notez l'URL publique générée (ex: `https://xxx.supabase.co/storage/v1/object/public/exercise-videos/mountain_climbers.mov`)

### Option B : Via script Node.js (pour plusieurs exercices)

Créez un script `backend/scripts/upload_single_video.js` :

```javascript
const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../.env') });

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);

async function uploadVideo(localPath, remoteName) {
  const fileBuffer = fs.readFileSync(localPath);
  const ext = path.extname(localPath).toLowerCase();

  const contentType = {
    '.mov': 'video/quicktime',
    '.mp4': 'video/mp4',
    '.webm': 'video/webm',
  }[ext] || 'video/mp4';

  const { data, error } = await supabase.storage
    .from('exercise-videos')
    .upload(remoteName, fileBuffer, {
      contentType,
      upsert: true
    });

  if (error) {
    console.error('❌ Erreur:', error.message);
    return null;
  }

  const { data: urlData } = supabase.storage
    .from('exercise-videos')
    .getPublicUrl(remoteName);

  console.log('✅ Vidéo uploadée:', urlData.publicUrl);
  return urlData.publicUrl;
}

// Usage
const videoPath = process.argv[2];
const remoteName = process.argv[3] || path.basename(videoPath);

if (!videoPath) {
  console.error('Usage: node upload_single_video.js <chemin_video> [nom_distant]');
  process.exit(1);
}

uploadVideo(videoPath, remoteName);
```

**Utilisation** :

```bash
cd backend
node scripts/upload_single_video.js /path/to/mountain_climbers.mov
```

## 🗄️ Étape 3 : Insérer les métadonnées dans PostgreSQL

### 3.1 Préparer les données

Vous avez besoin de :

| Champ | Type | Description | Exemple |
|-------|------|-------------|---------|
| `id` | UUID | Identifiant unique | `gen_random_uuid()` |
| `name` | string | Nom de l'exercice | `"Mountain Climbers"` |
| `description` | string | Description détaillée | `"Position planche, genoux vers poitrine..."` |
| `icon` | string | Emoji représentatif | `"🏔️"` |
| `video_url` | string | URL Supabase Storage | `"https://...supabase.co/.../mountain_climbers.mov"` |
| `default_duration` | int | Durée par défaut (secondes) | `60` |
| `difficulty` | enum | `easy`, `medium`, `hard` | `"medium"` |
| `has_jump` | boolean | Contient des sauts ? | `true` |
| `access_tier` | enum | `free`, `premium`, `pro` | `"free"` |
| `metadata` | JSONB | Métadonnées (voir ci-dessous) | `{ ... }` |

**Structure du champ `metadata`** :

```json
{
  "muscles_targeted": ["core", "shoulders", "legs"],
  "equipment_needed": [],
  "calories_per_min": 8.0
}
```

### 3.2 Option A : Via le Dashboard Supabase

1. Allez dans **Database** > **Table Editor** > `exercises`
2. Cliquez sur **Insert row**
3. Remplissez les champs :
   - Laissez `id` vide (auto-généré)
   - Remplissez `name`, `description`, `icon`, etc.
   - Pour `metadata`, cliquez sur l'icône JSON et collez :
     ```json
     {
       "muscles_targeted": ["core", "shoulders"],
       "equipment_needed": [],
       "calories_per_min": 8.0
     }
     ```
4. Cliquez sur **Save**

### 3.3 Option B : Via SQL Query

Dans **SQL Editor** de Supabase :

```sql
INSERT INTO exercises (
  name,
  description,
  icon,
  video_url,
  default_duration,
  difficulty,
  has_jump,
  access_tier,
  metadata
) VALUES (
  'Mountain Climbers',
  'Position planche, amenez alternativement les genoux vers la poitrine de manière rapide et contrôlée. Gardez le dos droit et le core engagé.',
  '🏔️',
  'https://votre-projet.supabase.co/storage/v1/object/public/exercise-videos/mountain_climbers.mov',
  60,
  'medium',
  false,
  'free',
  '{
    "muscles_targeted": ["core", "shoulders", "legs"],
    "equipment_needed": [],
    "calories_per_min": 8.0
  }'::jsonb
);
```

### 3.4 Option C : Via script Node.js

Créez `backend/scripts/add_exercise.js` :

```javascript
const { createClient } = require('@supabase/supabase-js');
const { v4: uuidv4 } = require('uuid');
require('dotenv').config({ path: require('path').join(__dirname, '../.env') });

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY
);

async function addExercise(exerciseData) {
  const { data, error } = await supabase
    .from('exercises')
    .insert([{
      id: uuidv4(),
      ...exerciseData
    }])
    .select();

  if (error) {
    console.error('❌ Erreur:', error.message);
    return null;
  }

  console.log('✅ Exercice ajouté:', data[0]);
  return data[0];
}

// Exemple d'utilisation
const newExercise = {
  name: 'Mountain Climbers',
  description: 'Position planche, amenez alternativement les genoux vers la poitrine...',
  icon: '🏔️',
  video_url: 'https://xxx.supabase.co/storage/v1/object/public/exercise-videos/mountain_climbers.mov',
  default_duration: 60,
  difficulty: 'medium',
  has_jump: false,
  access_tier: 'free',
  metadata: {
    muscles_targeted: ['core', 'shoulders', 'legs'],
    equipment_needed: [],
    calories_per_min: 8.0
  }
};

addExercise(newExercise);
```

**Utilisation** :

```bash
cd backend
node scripts/add_exercise.js
```

## ✅ Étape 4 : Vérifier l'ajout

### 4.1 Vérifier dans le dashboard Supabase

1. **Database** > **Table Editor** > `exercises`
2. Cherchez votre exercice par nom
3. Vérifiez tous les champs

### 4.2 Tester via l'API

```bash
curl http://localhost:8000/api/exercises
```

Vous devriez voir votre nouvel exercice dans la liste JSON retournée.

### 4.3 Tester la vidéo

Copiez l'URL de la vidéo et ouvrez-la dans un navigateur :

```
https://xxx.supabase.co/storage/v1/object/public/exercise-videos/mountain_climbers.mov
```

La vidéo doit se charger et être lisible.

## 🎬 Étape 5 : Tester dans un workout

### 5.1 Créer un workout de test

```bash
curl -X POST http://localhost:8000/api/workouts/generate \
  -H "Content-Type: application/json" \
  -d '{
    "total_duration": 120,
    "config": {
      "intensity": "medium_intensity",
      "intervals": {"work_time": 40, "rest_time": 20},
      "no_jump": false,
      "exercice_intensity_levels": ["easy", "medium"]
    }
  }'
```

### 5.2 Vérifier que votre exercice peut être sélectionné

Le backend devrait pouvoir inclure votre nouvel exercice dans les workouts générés aléatoirement.

## 📝 Template d'exercice

Voici un template complet pour vous aider :

```json
{
  "name": "Nom de l'Exercice",
  "description": "Description détaillée de l'exercice avec instructions de forme...",
  "icon": "💪",
  "video_url": "https://xxx.supabase.co/storage/v1/object/public/exercise-videos/exercise_name.mov",
  "default_duration": 60,
  "difficulty": "medium",
  "has_jump": false,
  "access_tier": "free",
  "metadata": {
    "muscles_targeted": ["chest", "triceps", "core"],
    "equipment_needed": [],
    "calories_per_min": 7.0
  }
}
```

## 🔍 Exemples d'exercices

### Exemple 1 : Burpees (avec sauts)

```sql
INSERT INTO exercises (name, description, icon, video_url, default_duration, difficulty, has_jump, access_tier, metadata)
VALUES (
  'Burpees',
  'Position debout, descente en squat, mains au sol, saut en planche, pompe, retour squat, saut vertical.',
  '💥',
  'https://xxx.supabase.co/storage/v1/object/public/exercise-videos/burpees.mov',
  60,
  'hard',
  true,
  'free',
  '{"muscles_targeted": ["full_body"], "equipment_needed": [], "calories_per_min": 10.0}'::jsonb
);
```

### Exemple 2 : Plank (statique)

```sql
INSERT INTO exercises (name, description, icon, video_url, default_duration, difficulty, has_jump, access_tier, metadata)
VALUES (
  'Plank',
  'Position de planche sur les avant-bras, corps aligné de la tête aux pieds. Maintenez la position.',
  '🧘',
  'https://xxx.supabase.co/storage/v1/object/public/exercise-videos/plank.mov',
  60,
  'easy',
  false,
  'free',
  '{"muscles_targeted": ["core", "shoulders"], "equipment_needed": [], "calories_per_min": 5.0}'::jsonb
);
```

## 🚨 Dépannage

### Problème : "File size exceeded"

**Solution** : Votre vidéo dépasse 200MB. Compressez-la :

```bash
ffmpeg -i input.mov -vcodec h264 -crf 28 output.mp4
```

### Problème : "Invalid JSON in metadata"

**Solution** : Vérifiez la syntaxe JSON. Utilisez un validateur comme [jsonlint.com](https://jsonlint.com)

### Problème : "Exercise not appearing in workouts"

**Solution** : Vérifiez que :
1. `difficulty` correspond aux niveaux demandés dans le workout
2. `has_jump` est compatible avec `no_jump` du workout
3. L'exercice est bien dans la table (requête SQL : `SELECT * FROM exercises WHERE name = 'Mountain Climbers'`)

### Problème : "Video not loading in workout"

**Solution** :
1. Testez l'URL directement dans le navigateur
2. Vérifiez que le bucket est bien **public**
3. Vérifiez les logs du backend : `logger.info` dans `video_service.py`

## 📊 Bonnes pratiques

### Nommage des fichiers

✅ **Bon** :
- `mountain_climbers.mov`
- `jumping_jacks.mp4`
- `high_knees.webm`

❌ **Mauvais** :
- `Mountain Climbers.mov` (espaces, majuscules)
- `Video Final V2.mov` (nom générique)
- `exercice-1.mov` (pas descriptif)

### Descriptions

Une bonne description doit :
- ✅ Expliquer la position de départ
- ✅ Décrire le mouvement étape par étape
- ✅ Mentionner les points de sécurité
- ✅ Faire 2-3 phrases maximum

### Métadonnées

**Muscles ciblés** - Utilisez ces valeurs standard :
- `core`, `chest`, `back`, `shoulders`, `arms`, `triceps`, `biceps`
- `quadriceps`, `glutes`, `hamstrings`, `calves`, `legs`
- `full_body` (pour exercices complets)

**Calories par minute** - Estimation :
- Exercices légers : 4-6 cal/min
- Exercices modérés : 6-8 cal/min
- Exercices intenses : 8-12 cal/min

## 🔗 Ressources

- [Documentation Supabase Storage](https://supabase.com/docs/guides/storage)
- [Guide de migration](./migration_guide_supabase_videos.md)
- [Plan de migration détaillé](./supabase_video_storage_migration_plan.md)

---

**Besoin d'aide ?** Consultez les logs du backend ou la documentation Supabase.
