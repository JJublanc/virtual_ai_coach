# Guide de Gestion des Exercices

Ce guide explique comment ajouter de nouveaux exercices ou modifier des exercices existants dans le système Virtual AI Coach.

## Table des matières

1. [Vue d'ensemble du workflow](#vue-densemble-du-workflow)
2. [Ajouter un nouvel exercice](#ajouter-un-nouvel-exercice)
3. [Modifier un exercice existant](#modifier-un-exercice-existant)
4. [Structure des données](#structure-des-données)
5. [Commandes de référence](#commandes-de-référence)

---

## Vue d'ensemble du workflow

Le système de gestion des exercices fonctionne en 3 étapes :

```
1. Vidéos brutes         2. Upload Storage      3. Sync Base de données
   (videos_raw/)    →    (Supabase)        →    (PostgreSQL)

   fichier.mov           script upload          script seed
                         + conversion 720p      + mapping URLs
```

### Fichiers et dossiers clés

- **`videos_raw/`** : Vidéos sources (formats variés, haute qualité)
- **`videos/`** : Dossier de travail pour les uploads
- **`videos_archives/`** : Vidéos déjà uploadées (archivage automatique)
- **`backend/scripts/exercises.json`** : Configuration de tous les exercices
- **`backend/scripts/video_urls_mapping.json`** : Mapping généré automatiquement

---

## Ajouter un nouvel exercice

### Étape 1 : Préparer la vidéo

1. **Filmer l'exercice** et sauvegarder dans `videos_raw/`
   ```bash
   # Format recommandé : {nom_exercice}_raw.mov
   # Exemple : jumping_jacks_raw.mov
   ```

2. **Copier la vidéo** dans le dossier de travail `videos/`
   ```bash
   cp videos_raw/mon_exercice_raw.mov videos/mon_exercice.mov
   ```

### Étape 2 : Générer un UUID pour l'exercice

```bash
# Sur macOS/Linux
uuidgen | tr '[:upper:]' '[:lower:]'

# Ou en Node.js
node -e "console.log(require('crypto').randomUUID())"
```

### Étape 3 : Ajouter l'exercice dans exercises.json

Ouvrir `backend/scripts/exercises.json` et ajouter une entrée :

```json
{
    "id": "VOTRE-UUID-GENERE",
    "name": "Nom de l'Exercice",
    "description": "Description détaillée de l'exercice avec instructions de mouvement.",
    "icon": "🏃",
    "video_url": "/Users/jjublanc/projets_perso/virtual_ai_coach/videos/mon_exercice.mov",
    "default_duration": 60,
    "difficulty": "medium",
    "has_jump": false,
    "access_tier": "free",
    "metadata": {
        "muscles_targeted": ["quadriceps", "glutes", "core"],
        "equipment_needed": [],
        "calories_per_min": 8.0,
        "laterality": "bilateral"
    }
}
```

### Étape 4 : Uploader la vidéo vers Supabase

```bash
# Depuis la racine du projet
node backend/scripts/upload_videos_to_supabase.js
```

Ce script va :
- ✅ Convertir la vidéo en format 720p MP4 optimisé (~70% de réduction)
- ✅ Uploader vers Supabase Storage (bucket `exercise-videos`)
- ✅ Générer le fichier `video_urls_mapping.json`
- ✅ Déplacer automatiquement la vidéo vers `videos_archives/`

**Options disponibles :**
```bash
# Sans conversion (upload fichier original)
node backend/scripts/upload_videos_to_supabase.js --no-convert

# Garder les fichiers temporaires de conversion
node backend/scripts/upload_videos_to_supabase.js --keep-temp
```

### Étape 5 : Synchroniser avec la base de données

```bash
# Depuis la racine du projet
node backend/scripts/seed_exercises.js
```

Ce script va :
- ✅ Lire `exercises.json`
- ✅ Utiliser les URLs du `video_urls_mapping.json`
- ✅ Insérer ou mettre à jour l'exercice dans PostgreSQL (upsert)

---

## Modifier un exercice existant

### Cas 1 : Modifier uniquement les métadonnées (sans changer la vidéo)

1. **Éditer `backend/scripts/exercises.json`**
   - Modifier les champs souhaités (name, description, difficulty, etc.)
   - ⚠️ **Ne pas modifier l'ID** de l'exercice

2. **Synchroniser avec la base de données**
   ```bash
   node backend/scripts/seed_exercises.js
   ```

### Cas 2 : Remplacer la vidéo d'un exercice existant

1. **Préparer la nouvelle vidéo**
   ```bash
   # Placer la nouvelle vidéo dans videos/
   cp videos_raw/mon_exercice_v2_raw.mov videos/mon_exercice.mov
   ```

2. **Uploader la nouvelle vidéo**
   ```bash
   node backend/scripts/upload_videos_to_supabase.js
   ```
   - La vidéo sera remplacée dans Supabase (upsert activé)
   - Le mapping sera mis à jour

3. **Synchroniser la base de données**
   ```bash
   node backend/scripts/seed_exercises.js
   ```

### Cas 3 : Modification complète (vidéo + métadonnées)

Combiner les étapes des cas 1 et 2 :

```bash
# 1. Copier la nouvelle vidéo
cp videos_raw/mon_exercice_v2_raw.mov videos/mon_exercice.mov

# 2. Éditer exercises.json (sans changer l'ID)

# 3. Uploader la vidéo
node backend/scripts/upload_videos_to_supabase.js

# 4. Synchroniser la base
node backend/scripts/seed_exercises.js
```

---

## Structure des données

### Format de exercises.json

```json
{
    "id": "UUID v4 (obligatoire, ne jamais modifier après création)",
    "name": "Nom affiché (string, obligatoire)",
    "description": "Instructions détaillées (string, obligatoire)",
    "icon": "Emoji représentatif (string, obligatoire)",
    "video_url": "Chemin local vers la vidéo (string, obligatoire)",
    "default_duration": 60,  // En secondes (number, obligatoire)
    "difficulty": "easy|medium|hard (string, obligatoire)",
    "has_jump": true|false,  // Boolean pour filtrage (obligatoire)
    "access_tier": "free|premium (string, obligatoire)",
    "metadata": {
        "muscles_targeted": ["array", "de", "muscles"],
        "equipment_needed": ["array", "optionnel"],
        "calories_per_min": 8.5,  // Nombre décimal
        "laterality": "bilateral|unilateral"
    }
}
```

### Valeurs possibles

**Difficulty :**
- `"easy"` : Débutant
- `"medium"` : Intermédiaire
- `"hard"` : Avancé

**Muscles targeted (exemples) :**
- `"quadriceps"`, `"glutes"`, `"hamstrings"`
- `"core"`, `"abs"`, `"obliques"`
- `"shoulders"`, `"chest"`, `"triceps"`, `"biceps"`
- `"calves"`, `"hip_flexors"`

**Laterality :**
- `"bilateral"` : Les deux côtés simultanément
- `"unilateral"` : Un côté à la fois (alterné)

---

## Commandes de référence

### Workflow complet pour un nouvel exercice

```bash
# 1. Générer UUID
uuidgen | tr '[:upper:]' '[:lower:]'

# 2. Copier vidéo brute
cp videos_raw/mon_exercice_raw.mov videos/mon_exercice.mov

# 3. Éditer exercises.json
# (ajouter l'entrée avec l'UUID généré)

# 4. Upload + conversion
node backend/scripts/upload_videos_to_supabase.js

# 5. Sync base de données
node backend/scripts/seed_exercises.js
```

### Uploader une seule vidéo spécifique

```bash
# Si vous voulez uploader une seule vidéo sans traiter tout le dossier
node backend/scripts/upload_single_video.js <fichier.mov>
```

### Vérifier l'état du Storage et de la base

```bash
# Lister les exercices en base (nécessite psql ou accès Supabase Dashboard)
# Dans le Dashboard Supabase : Table Editor → exercises

# Vérifier le mapping des URLs
cat backend/scripts/video_urls_mapping.json | jq
```

### Nettoyage et maintenance

```bash
# Archiver manuellement une vidéo
mv videos/mon_exercice.mov videos_archives/

# Voir les vidéos en attente d'upload
ls -lh videos/

# Voir les vidéos brutes disponibles
ls -lh videos_raw/
```

---

## Comportement du système

### Upload de vidéos (upload_videos_to_supabase.js)

- ✅ **Conversion automatique** en 720p MP4 (réduction ~70%)
- ✅ **Archivage automatique** vers `videos_archives/` après upload réussi
- ✅ **Upsert activé** : remplace la vidéo si le nom existe déjà sur le Storage
- ✅ **Génération du mapping** pour lier exercices.json aux URLs Supabase

#### ⚠️ Comportement avec fichiers existants sur le Storage

Si une vidéo du **même nom** existe déjà dans Supabase Storage :
- Elle est **automatiquement remplacée** par la nouvelle version (upsert: true)
- L'URL publique reste identique (même chemin dans le bucket)
- Aucun message d'erreur n'est affiché
- La version précédente est écrasée définitivement (pas de versioning)

**Exemple :**
- 1er upload de `jumping_jacks.mov` → crée `jumping_jacks_720p.mp4` sur Storage
- 2ème upload de `jumping_jacks.mov` → **remplace** `jumping_jacks_720p.mp4` sur Storage
- L'ancienne version est perdue et non récupérable

💡 **Conseil** : Si vous voulez garder plusieurs versions d'une vidéo, renommez-les avant l'upload (ex: `jumping_jacks_v1.mov`, `jumping_jacks_v2.mov`)

### Seed de la base (seed_exercises.js)

- ✅ **Upsert sur l'ID** : met à jour si l'exercice existe, sinon insère
- ✅ **Pas de suppression** : les exercices en base non présents dans le JSON restent intacts
- ✅ **Remplacement complet** : toutes les données de l'exercice sont remplacées lors de la mise à jour

### Structure de stockage

```
videos_raw/              # Vidéos sources (gardées indéfiniment)
videos/                  # Dossier de travail (vidéos à uploader)
videos_archives/         # Vidéos déjà uploadées (automatique)
videos_generated/        # Workouts générés (non concerné par ce workflow)
```

---

## Troubleshooting

### La vidéo n'apparaît pas après seed

1. Vérifier que `video_urls_mapping.json` contient l'URL
2. Vérifier que le nom du fichier dans `exercises.json` correspond
3. Re-lancer le seed : `node backend/scripts/seed_exercises.js`

### La conversion échoue

1. Vérifier que FFmpeg est installé : `ffmpeg -version`
2. Vérifier le format de la vidéo source
3. Utiliser `--no-convert` pour uploader sans conversion

### L'exercice existe en double

- Les exercices sont identifiés par **ID unique**
- Si vous voulez fusionner, gardez un seul ID et supprimez l'autre de `exercises.json`

### Permissions Storage refusées

- Vérifier que `SUPABASE_SERVICE_ROLE_KEY` est configurée dans `backend/.env`
- Vérifier que le bucket `exercise-videos` existe dans Supabase

---

## Notes importantes

⚠️ **Ne jamais modifier l'ID d'un exercice existant** : cela créerait un doublon

✅ **Toujours partir de `videos_raw/`** : gardez vos sources intactes

📦 **L'archivage est automatique** : les vidéos uploadées vont dans `videos_archives/`

🔄 **Le workflow est idempotent** : relancer les scripts n'a pas d'effets indésirables

---

## Support

Pour plus d'informations :
- Architecture globale : `docs/architecture_globale.md`
- Vidéos de pause : `backend/scripts/README_BREAK_VIDEOS.md`
- Génération workouts : `backend/scripts/README_GENERATE_VIDEO_LOCAL.md`
