# Générateur de Vidéos d'Entraînement Local

Ce script permet de générer et sauvegarder localement des vidéos d'entraînement, similaires à celles générées par l'application, mais stockées dans un dossier dédié sur votre machine.

## 📋 Prérequis

- Python 3.8+
- FFmpeg installé et disponible dans le PATH
- Dépendances Python installées (`pip install -r requirements.txt`)
- Accès à Supabase (pour télécharger les vidéos d'exercices)

## 🚀 Utilisation

### Mode Automatique (Génération basée sur des critères)

Génère automatiquement un workout en sélectionnant aléatoirement des exercices selon vos critères :

```bash
# Workout de 10 minutes, sans sauts, intensité facile/moyenne
python backend/scripts/generate_workout_video_local.py \
  --auto \
  --duration 600 \
  --no-jump \
  --intensity easy medium

# Workout de 5 minutes, haute intensité
python backend/scripts/generate_workout_video_local.py \
  --auto \
  --duration 300 \
  --intensity hard \
  --name "Workout Intense"

# Workout personnalisé avec intervalles spécifiques
python backend/scripts/generate_workout_video_local.py \
  --auto \
  --duration 900 \
  --work-time 45 \
  --rest-time 15 \
  --intensity medium hard \
  --output-dir ./mes_workouts
```

### Mode Manuel (Liste d'exercices spécifique)

Génère un workout avec une liste précise d'exercices :

```bash
# Workout avec exercices spécifiques
python backend/scripts/generate_workout_video_local.py \
  --exercises "Push-ups" "Air Squat" "Plank" "Jumping Jacks"

# Avec nom personnalisé
python backend/scripts/generate_workout_video_local.py \
  --exercises "Burpees" "Mountain Climbers" "High Knees" \
  --name "Cardio Killer" \
  --output-name "cardio_workout.mp4"
```

## ⚙️ Options Disponibles

### Modes de Génération

| Option | Description |
|--------|-------------|
| `--auto` | Mode automatique : génère les exercices selon des critères |
| `--exercises [NOMS...]` | Mode manuel : liste d'exercices à inclure |

### Configuration du Workout (Mode Auto)

| Option | Valeur par défaut | Description |
|--------|-------------------|-------------|
| `--duration SECONDS` | 600 (10 min) | Durée totale du workout en secondes |
| `--no-jump` | Non | Exclure les exercices avec sauts |
| `--intensity [LEVELS...]` | `easy medium` | Niveaux : `easy`, `medium`, `hard` |

### Intervalles de Travail/Repos

| Option | Valeur par défaut | Description |
|--------|-------------------|-------------|
| `--work-time SECONDS` | 40 | Durée de travail par exercice |
| `--rest-time SECONDS` | 20 | Durée de repos entre exercices |

### Sortie

| Option | Valeur par défaut | Description |
|--------|-------------------|-------------|
| `--output-dir PATH` | `./generated_videos` | Dossier de destination |
| `--output-name NAME` | `workout_<timestamp>.mp4` | Nom du fichier |
| `--name TEXT` | `Mon Workout` | Nom du workout |

### Avancé

| Option | Valeur par défaut | Description |
|--------|-------------------|-------------|
| `--speed LEVEL` | `medium_intensity` | `low_intensity`, `medium_intensity`, `high_intensity` |
| `--verbose`, `-v` | Non | Mode verbose (plus de logs) |

## 📝 Exemples Complets

### 1. Workout Matinal Doux (10 minutes)

```bash
python backend/scripts/generate_workout_video_local.py \
  --auto \
  --duration 600 \
  --no-jump \
  --intensity easy \
  --work-time 30 \
  --rest-time 20 \
  --name "Réveil en Douceur" \
  --output-name "matinal.mp4"
```

### 2. HIIT Intense (15 minutes)

```bash
python backend/scripts/generate_workout_video_local.py \
  --auto \
  --duration 900 \
  --intensity medium hard \
  --work-time 45 \
  --rest-time 15 \
  --name "HIIT Intense" \
  --speed high_intensity \
  --output-dir ./hiit_workouts
```

### 3. Circuit Personnalisé

```bash
python backend/scripts/generate_workout_video_local.py \
  --exercises "Push-ups" "Air Squat" "Plank" "Lunges" "Burpees" \
  --work-time 40 \
  --rest-time 20 \
  --name "Circuit Full Body" \
  --output-name "circuit_fullbody.mp4"
```

### 4. Workout Sans Sauts pour Appartement

```bash
python backend/scripts/generate_workout_video_local.py \
  --auto \
  --duration 1200 \
  --no-jump \
  --intensity easy medium \
  --name "Workout Silencieux" \
  --output-dir ~/Videos/workouts
```

## 📊 Sortie du Script

Le script affiche des informations détaillées pendant la génération :

```
============================================================
🏋️  GÉNÉRATEUR DE VIDÉOS D'ENTRAÎNEMENT
============================================================
📁 Dossier de sortie: /Users/vous/projets/generated_videos
🎲 Génération automatique du workout...
   Durée: 600s (10 minutes)
   No jump: True
   Intensités: ['easy', 'medium']
   Intervalles: 40s travail / 20s repos
✅ 10 exercices générés

📋 Résumé du workout:
   Nom: Mon Workout
   Exercices: 10
   Durée estimée: 600s

🎬 Génération de la vidéo: Mon Workout
   Sortie: /Users/vous/projets/generated_videos/workout_20231225_143022.mp4
📥 Téléchargement des vidéos d'exercices...
⏸️  Préparation des vidéos de pause...
🔧 Construction de la vidéo finale...
✅ Vidéo générée avec succès!
   Temps: 45.2s
   Taille: 25.3 MB
   Fichier: /Users/vous/projets/generated_videos/workout_20231225_143022.mp4

============================================================
✨ GÉNÉRATION TERMINÉE AVEC SUCCÈS!
============================================================
```

## 🔍 Logs

Les logs sont également sauvegardés dans `workout_generation.log` pour référence ultérieure.

## ❓ Dépannage

### "Exercice non trouvé"

Vérifiez que le nom de l'exercice correspond exactement à ceux disponibles dans la base de données. Utilisez l'API `/api/exercises` pour voir la liste complète.

### "FFmpeg introuvable"

Assurez-vous que FFmpeg est installé :
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Vérification
ffmpeg -version
```

### "Vidéo manquante pour un exercice"

Vérifiez que :
1. Vous avez accès à Supabase (fichier `.env` configuré)
2. Les vidéos sont bien uploadées sur Supabase
3. Votre connexion Internet fonctionne

### Mode verbose

Pour plus d'informations en cas de problème :
```bash
python backend/scripts/generate_workout_video_local.py --auto --duration 300 --verbose
```

## 🎯 Exercices Disponibles

Pour voir la liste complète des exercices disponibles, vous pouvez :

1. Utiliser l'API :
```bash
curl http://localhost:8000/api/exercises | jq
```

2. Consulter directement Supabase

3. Regarder le fichier `backend/app/models/exercises.json` (si présent)

## 💡 Astuces

### Créer un batch de workouts

Créez un script shell pour générer plusieurs workouts d'un coup :

```bash
#!/bin/bash
# generate_batch.sh

for i in {1..5}; do
  python backend/scripts/generate_workout_video_local.py \
    --auto \
    --duration 600 \
    --intensity easy medium \
    --output-name "workout_day_$i.mp4"
done
```

### Automatiser avec cron

Générez un nouveau workout chaque jour :

```bash
# Crontab : Chaque jour à 6h du matin
0 6 * * * cd /path/to/project && python backend/scripts/generate_workout_video_local.py --auto --duration 900 --output-name "daily_$(date +\%Y\%m\%d).mp4"
```

## 🤝 Contribution

Pour ajouter de nouvelles fonctionnalités ou améliorer le script, modifiez `backend/scripts/generate_workout_video_local.py`.

## 📄 Licence

Même licence que le projet principal.
