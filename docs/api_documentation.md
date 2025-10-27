# Documentation API - Virtual AI Coach Backend

## Endpoints disponibles

### 1. Health Check

**GET** `/health`

Vérifie l'état du serveur.

**Réponse :**
```json
{
  "status": "healthy",
  "message": "Virtual AI Coach Backend is running"
}
```

---

### 2. Liste des exercices

**GET** `/api/exercises`

Récupère la liste de tous les exercices disponibles.

**Réponse :**
```json
[
  {
    "name": "Push-ups",
    "description": "Pompes classiques...",
    "icon": "💪",
    "video_url": "/path/to/video.mov",
    "default_duration": 30,
    "difficulty": "medium",
    "has_jump": false,
    "access_tier": "free",
    "metadata": {
      "muscles_targeted": ["chest", "triceps", "shoulders"],
      "equipment_needed": [],
      "calories_per_min": 7.0
    }
  }
]
```

---

### 3. Génération de vidéo d'entraînement

**POST** `/api/generate-workout-video`

Génère et streame une vidéo d'entraînement personnalisée en concaténant plusieurs exercices avec ajustement de vitesse selon l'intensité.

#### Paramètres de la requête

**Body (JSON) :**

```json
{
  "exercise_names": ["Push-ups", "Air Squat", "Plank"],
  "config": {
    "intensity": "medium_intensity",
    "intervals": {
      "work_time": 40,
      "rest_time": 20
    },
    "no_jump": false,
    "no_repeat": false,
    "intensity_levels": ["easy", "medium", "hard"],
    "include_warm_up": true,
    "include_cool_down": true,
    "target_duration": 30,
    "show_timer": true,
    "show_progress_bar": true,
    "show_exercise_name": true
  }
}
```

**Champs requis :**
- `exercise_names` : Liste des noms d'exercices à inclure (minimum 1)

**Champs optionnels dans `config` :**
- `intensity` : Niveau d'intensité (`low_impact`, `medium_intensity`, `high_intensity`)
  - `low_impact` : Vitesse à 80% (plus lent)
  - `medium_intensity` : Vitesse normale (100%)
  - `high_intensity` : Vitesse à 120% (plus rapide)
- `intervals` : Temps de travail et de repos en secondes
- `no_jump` : Exclure les exercices avec sauts
- `no_repeat` : Ne pas répéter les exercices
- `intensity_levels` : Niveaux de difficulté à inclure
- `include_warm_up` : Inclure un échauffement
- `include_cool_down` : Inclure un retour au calme
- `target_duration` : Durée cible en minutes
- `show_timer` : Afficher le timer
- `show_progress_bar` : Afficher la barre de progression
- `show_exercise_name` : Afficher le nom de l'exercice

#### Réponse

**Headers :**
- `Content-Type: video/mp4`
- `Content-Disposition: inline; filename="workout.mp4"`
- `Cache-Control: no-cache`

**Body :** Stream de données vidéo MP4

#### Codes d'erreur

- `400 Bad Request` : Aucun exercice valide sélectionné
- `404 Not Found` : Un ou plusieurs exercices demandés n'existent pas
- `500 Internal Server Error` : Erreur lors de la génération vidéo
- `504 Gateway Timeout` : Le timeout de 5 minutes a été dépassé

#### Exemples d'utilisation

**Avec curl :**

```bash
curl -X POST "http://localhost:8000/api/generate-workout-video" \
     -H "Content-Type: application/json" \
     -d '{
           "exercise_names": ["Push-ups", "Air Squat", "Plank"],
           "config": {"intensity": "medium_intensity"}
         }' \
     --output workout.mp4
```

**Avec Python (requests) :**

```python
import requests

url = "http://localhost:8000/api/generate-workout-video"
payload = {
    "exercise_names": ["Push-ups", "Air Squat", "Plank"],
    "config": {
        "intensity": "medium_intensity",
        "target_duration": 30
    }
}

response = requests.post(url, json=payload, stream=True)

if response.status_code == 200:
    with open("workout.mp4", "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print("Vidéo téléchargée avec succès!")
else:
    print(f"Erreur: {response.status_code} - {response.text}")
```

**Avec JavaScript (fetch) :**

```javascript
const url = "http://localhost:8000/api/generate-workout-video";
const payload = {
  exercise_names: ["Push-ups", "Air Squat", "Plank"],
  config: {
    intensity: "medium_intensity"
  }
};

fetch(url, {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify(payload)
})
  .then(response => response.blob())
  .then(blob => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "workout.mp4";
    a.click();
  })
  .catch(error => console.error("Erreur:", error));
```

---

## Notes techniques

### Timeout
- Timeout maximum : **5 minutes** (300 secondes)
- Si la génération dépasse ce délai, l'endpoint retourne une erreur 504

### Streaming
- La vidéo est streamée en chunks de 64KB
- Le client peut commencer à recevoir la vidéo pendant sa génération
- Format de sortie : MP4 (H.264, yuv420p)

### Vitesse d'encodage
- Preset FFmpeg : `ultrafast` pour minimiser la latence
- Optimisations : `frag_keyframe+empty_moov` pour le streaming

### Fichiers temporaires
- Un fichier de concaténation temporaire est créé pendant la génération
- Il est automatiquement nettoyé après succès
- Emplacement : répertoire temporaire du système (`/tmp` ou équivalent)

---

## Modèles de données

### Exercise

```python
{
  "name": str,                    # Nom de l'exercice
  "description": str,             # Description détaillée
  "icon": str,                    # Emoji ou icône
  "video_url": str,               # URL ou chemin de la vidéo
  "default_duration": int,        # Durée par défaut en secondes
  "difficulty": str,              # "easy", "medium", "hard"
  "has_jump": bool,               # Contient des sauts
  "access_tier": str,             # "free", "premium"
  "metadata": dict                # Métadonnées additionnelles
}
```

### WorkoutConfig

```python
{
  "intensity": str,                          # "low_impact", "medium_intensity", "high_intensity"
  "intervals": {
    "work_time": int,                        # Temps de travail en secondes
    "rest_time": int                         # Temps de repos en secondes
  },
  "no_repeat": bool,                         # Ne pas répéter les exercices
  "no_jump": bool,                           # Exclure les exercices avec sauts
  "intensity_levels": List[str],             # Niveaux de difficulté à inclure
  "include_warm_up": bool,                   # Inclure échauffement
  "include_cool_down": bool,                 # Inclure retour au calme
  "target_duration": int,                    # Durée cible en minutes
  "show_timer": bool,                        # Afficher le timer
  "show_progress_bar": bool,                 # Afficher barre de progression
  "show_exercise_name": bool                 # Afficher nom de l'exercice
}
```

---

## Documentation interactive

La documentation interactive Swagger UI est disponible à l'adresse :
- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc
