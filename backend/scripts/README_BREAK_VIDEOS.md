# Migration des vidéos de break vers Supabase

Ce guide explique comment générer et uploader les vidéos de break vers Supabase Storage.

## 📋 Prérequis

1. **Variables d'environnement** dans `.env` :
   ```bash
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key  # ⚠️ Pas l'anon key !
   SUPABASE_PROJECT_ID=your-project-id
   ```
   
   **Important :** Utilisez la **`service_role_key`** (pas l'anon key) pour uploader des fichiers.
   Vous la trouverez dans : Supabase Dashboard → Settings → API → `service_role` key

2. **FFmpeg installé** sur votre machine
3. **Image `sport_room.png`** à la racine du projet

## 🚀 Étapes de migration

### Étape 1 : Générer les vidéos de break localement

```bash
python backend/scripts/generate_break_videos.py
```

**Ce script va :**
- Créer le dossier `backend/break_videos/`
- Générer 8 vidéos de break (5s, 10s, 15s, 20s, 25s, 30s, 35s, 40s)
- Format : 1280x720 (720p), H.264, 30fps, sans audio
- Durée : ~2 minutes pour générer toutes les vidéos

**Résultat attendu :**
```
backend/break_videos/
  ├── break_5s.mp4
  ├── break_10s.mp4
  ├── break_15s.mp4
  ├── break_20s.mp4
  ├── break_25s.mp4
  ├── break_30s.mp4
  ├── break_35s.mp4
  └── break_40s.mp4
```

### Étape 2 : Uploader vers Supabase Storage

```bash
python backend/scripts/upload_breaks_to_supabase.py
```

**Ce script va :**
- Se connecter à Supabase avec vos credentials
- Uploader chaque vidéo dans `exercise-videos/breaks/`
- Afficher les URLs publiques générées
- Durée : ~30 secondes

**Résultat attendu :**
```
✅ Toutes les vidéos ont été uploadées avec succès!

📋 URLs générées:
  5s: https://[PROJECT_ID].supabase.co/storage/v1/object/public/exercise-videos/breaks/break_5s.mp4
  10s: https://[PROJECT_ID].supabase.co/storage/v1/object/public/exercise-videos/breaks/break_10s.mp4
  ...
```

### Étape 3 : Vérification

Les URLs sont automatiquement construites via `SUPABASE_PROJECT_ID` dans [`backend/app/config/break_videos.py`](../app/config/break_videos.py).

**Vérifiez que :**
1. ✅ La variable `SUPABASE_PROJECT_ID` est définie dans `.env`
2. ✅ Les vidéos sont accessibles publiquement sur Supabase
3. ✅ Le backend démarre sans erreur

## 🎯 Avantages de cette architecture

- ✅ **Démarrage instantané** : Plus de génération au démarrage (0s au lieu de 1m30s)
- ✅ **Cache efficace** : Téléchargement une seule fois par instance
- ✅ **Architecture cohérente** : Toutes les vidéos sur Supabase
- ✅ **CDN global** : Performance mondiale via Supabase CDN
- ✅ **Pas de régénération** : Les breaks ne sont générés qu'une seule fois

## 🔧 Maintenance

### Régénérer les vidéos de break

Si vous devez modifier les vidéos de break (changement d'image, de format, etc.) :

1. Modifiez le code dans [`video_service.py`](../app/services/video_service.py) si nécessaire
2. Relancez l'étape 1 (génération)
3. Relancez l'étape 2 (upload avec `upsert: true` pour écraser)

### Ajouter une nouvelle durée de break

1. Ajoutez la durée dans [`break_videos.py`](../app/config/break_videos.py)
2. Générez la nouvelle vidéo localement
3. Uploadez-la sur Supabase

## 📊 Tailles des fichiers

Chaque vidéo de break fait environ **50-150 KB** :
- Total : ~800 KB pour les 8 vidéos
- Téléchargement : < 5 secondes sur une connexion normale

## ⚠️ Troubleshooting

### Erreur : "SUPABASE_PROJECT_ID non définie"
→ Ajoutez `SUPABASE_PROJECT_ID=your-project-id` dans votre `.env`

### Erreur : "FFmpeg introuvable"
→ Installez FFmpeg : `brew install ffmpeg` (macOS) ou `apt-get install ffmpeg` (Linux)

### Erreur : "Image sport_room.png introuvable"
→ Assurez-vous que `sport_room.png` est à la racine du projet

### Les vidéos ne se téléchargent pas
→ Vérifiez que le bucket `exercise-videos` existe et est public sur Supabase