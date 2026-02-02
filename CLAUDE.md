# Virtual AI Coach - Contexte Claude

> **Documentation condensée pour assistants IA**
> Pour la documentation technique complète : voir [ARCHITECTURE.md](./ARCHITECTURE.md)

---

## 🎯 Résumé Exécutif

**Virtual AI Coach** est une application web gratuite de fitness qui génère des vidéos de workout personnalisées en temps réel. L'utilisateur configure ses préférences (intensité, durée, types d'exercices) et l'application crée dynamiquement une vidéo en concaténant des clips d'exercices pré-enregistrés avec des overlays intelligents (timer, progression, noms).

**Technologies Principales** :
- **Frontend** : Next.js 16 + React 19 + TypeScript + Tailwind CSS
- **Backend** : FastAPI (Python 3.13+) + FFmpeg
- **Database** : Supabase PostgreSQL
- **Storage** : Supabase Storage + CDN
- **Deployment** : Vercel (frontend) + Railway (backend)

**Performance Actuelle** : 30-40 secondes pour générer un workout de 10 exercices (vs 5-7 minutes initialement)

---

## 🏗️ Architecture Simplifiée

```
User → Next.js (Vercel) → FastAPI (Railway) → FFmpeg → Video Stream (MP4)
                              ↓
                        Supabase PostgreSQL + Storage
```

### Flux de Génération
1. User sélectionne préférences (intensité, durée, no-jump, etc.)
2. Backend filtre exercices selon critères
3. Génération par **blocs thématiques** (Upper Body, Legs, Cardio, Abs, Finisher)
4. FFmpeg concatène vidéos + overlays dynamiques
5. Streaming progressif 64KB chunks vers frontend

---

## 📂 Structure Projet

```
virtual-ai-coach/
├── backend/
│   ├── app/
│   │   ├── main.py                              # Entry point FastAPI
│   │   ├── api/
│   │   │   ├── exercises.py                     # GET /api/exercises
│   │   │   └── workouts.py                      # POST /api/generate-auto-workout-video
│   │   ├── services/
│   │   │   ├── video_service_optimized.py       # FFmpeg streaming + cache
│   │   │   └── workout_generator.py             # Logique sélection exercices
│   │   ├── models/
│   │   │   ├── exercise.py                      # Exercise, ExerciseMetadata
│   │   │   ├── workout.py                       # Workout, WorkoutSession
│   │   │   └── config.py                        # WorkoutConfig, BlockConfig
│   │   └── config/
│   │       └── break_videos.py                  # URLs breaks pré-générés
│   └── video_studio/                            # Système overlays V2
│       ├── generators/workout_video_generator_v2.py
│       └── renderers/                           # Timer, Progress, Description
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx                             # Landing page
│   │   ├── (routes)/train/page.tsx              # Workout generator UI
│   │   └── layout.tsx                           # Root layout + providers
│   ├── components/video/VideoPlayer.tsx         # Player avec overlays
│   ├── lib/
│   │   ├── api.ts                               # API client
│   │   └── types.ts                             # TypeScript types
│   └── store/                                   # Zustand state management
│
├── docs/                                        # Documentation technique
│   ├── workout_block_generation.md              # Système de blocs
│   ├── workout_video_optimization_guide.md      # Optimisations perf
│   └── workout_video_pregenerated_overlays_strategy.md
│
├── ARCHITECTURE.md                              # Documentation complète (1555 lignes)
└── CLAUDE.md                                    # Ce fichier
```

---

## 🔑 Principes Clés de Fonctionnement

### 1. Système de Blocs Thématiques (Janvier 2026)

**Fichiers** : `backend/app/models/config.py` (BlockConfig), `backend/app/services/workout_generator.py`

Les workouts sont générés par **blocs** de 2 minutes minimum :
- **Upper Body** : Pompes, dips, burpees
- **Legs** : Squats, lunges, jump squats
- **Cardio** : High knees, mountain climbers
- **Abs** : Crunches, planches, russian twists
- **Finisher** : Exercice intense de fin (burpees, jump squats)

**Raison** : Évite les workouts incohérents avec sélection aléatoire pure. Garantit progression logique et distribution équilibrée.

### 2. Pipeline Vidéo FFmpeg Optimisée

**Fichier** : `backend/app/services/video_service_optimized.py`

**Optimisations Clés** :
- ✅ **Stream Copy** : Pas de ré-encodage si format compatible → Gain 40-50%
- ✅ **Téléchargements Parallèles** : ThreadPoolExecutor (4 workers) → Gain 60-80%
- ✅ **Breaks Pré-générés** : Cache Supabase Storage → Gain 2-3s/pause
- ✅ **Preset Ultrafast** : Encodage H.264 rapide (CRF 23, 1280x720, 30fps)
- ✅ **Streaming Progressif** : Chunks 64KB pour playback immédiat

**Paramètres FFmpeg** :
```python
TARGET_FORMAT = {
    "preset": "ultrafast",
    "crf": 23,
    "pix_fmt": "yuv420p",
    "movflags": "frag_keyframe+empty_moov"  # Streaming
}
```

### 3. Overlays Dynamiques V2 (Janvier 2026)

**Fichiers** : `backend/video_studio/renderers/*`

**Architecture** :
- **TimerRenderer** : Compte à rebours par exercice (FFmpeg drawtext)
- **ProgressRenderer** : Barre progression "X/Y exercices"
- **DescriptionRenderer** : Nom exercice en overlay
- **BreakRenderer** : Countdown sur pauses

**Synchronisation** : Overlays alignés sur timeline FFmpeg avec calcul temps cumulé.

### 4. Cache Multi-Niveaux

**Vidéos Exercices** :
- Cache local : `/tmp/exercise_videos` (hash MD5 URL)
- Source : Supabase Storage + CDN global
- Hit rate : ~70%

**Breaks** :
- Pré-générés : 5s, 10s, 15s, 20s, 25s, 30s, 35s, 40s
- Stockés : Supabase Storage public
- Config : `backend/app/config/break_videos.py`

### 5. Filtrage Intelligent Exercices

**Fichier** : `backend/app/services/workout_generator.py`

**Critères** :
- `no_jump: bool` → Exclut exercices avec sauts
- `exercice_intensity_levels: List[Difficulty]` → Filtre par difficulté (easy, medium, hard)
- `exercise_type: str` → Filtre par type (strength, cardio, flexibility)
- `no_repeat: bool` → Évite doublons dans workout

**Logique** : Sélection aléatoire pondérée dans pool filtré, avec distribution équilibrée des thèmes.

---

## 🚀 Événements Majeurs Récents

### **02 Février 2026 - Décision Critique : Abandon Ré-encodage**

**Commit** : `f9d6cb2`
**Fichier** : `backend/app/services/video_service_optimized.py`

**Problème** : Ajustement vitesse vidéo selon intensité (80% low, 100% medium, 120% high) via `setpts='X*PTS'` causait :
- Temps génération doublé (ré-encodage obligatoire)
- Problèmes synchronisation audio/vidéo
- Complexité FFmpeg excessive

**Solution** : Retrait complet feature ajustement vitesse, priorité au `stream copy`

**Impact** :
- ✅ **Gain 40-50%** temps génération
- ✅ Élimination problèmes audio
- ✅ Simplification pipeline

**Philosophie** : Simplicité > Complexité

### **18 Janvier 2026 - Overlays Dynamiques V2**

**Commit** : `e42d760`
**Fichiers** : `backend/video_studio/generators/workout_video_generator_v2.py`, `backend/video_studio/renderers/`

**Innovation** : Système overlays synchronisé avec timeline vidéo
- Génération overlays PNG via Pillow
- Overlay FFmpeg avec filtergraph complexe
- Timer, progress, descriptions dynamiques

**Impact** : UX professionnelle comparable à apps commerciales

### **03 Janvier 2026 - Système de Blocs**

**Commit** : `32ab95b`
**Fichier** : `backend/app/models/config.py` (BlockConfig)

**Innovation** : Structure par blocs thématiques répétables (minimum 10 minutes)

**Impact** : Workouts cohérents et pédagogiques vs sélection aléatoire

---

## 📊 Métriques Performance

| Métrique | Initial (Déc 2025) | Actuel (Fév 2026) | Objectif Phase 2 |
|----------|-------------------|-------------------|------------------|
| **Temps génération (10 ex)** | 5-7 min | 30-40s | 15-20s |
| **Catalogue exercices** | 50 | 100+ | 200+ |
| **Cache hit rate** | 0% | 70% | 90% |
| **Temps premier byte** | 8-12s | 3-5s | <3s |

---

## 🔧 Commandes Utiles

### Développement Local

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload      # Port 8000

# Frontend
cd frontend
npm install
npm run dev                        # Port 3000
```

### Variables d'Environnement

**Backend** (`backend/.env`) :
```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
SUPABASE_SERVICE_ROLE_KEY=xxx
USE_SUPABASE=true
VIDEO_CACHE_DIR=/tmp/exercise_videos
```

**Frontend** (`frontend/.env.local`) :
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Git Workflow

```bash
# Branch actuelle
git status  # dev branch

# Workflow
git checkout -b feature/nom-feature
git commit -m "feat: description"
git push origin feature/nom-feature
# PR → dev → main (production)
```

---

## 🎯 API Endpoints Principaux

### GET /api/exercises
Liste tous les exercices disponibles (cache 1h)

**Response** :
```json
[
  {
    "id": "uuid",
    "name": "Push-ups",
    "video_url": "https://xxx.supabase.co/storage/.../push_ups.mov",
    "difficulty": "medium",
    "has_jump": false,
    "default_duration": 40,
    "metadata": {
      "muscles_targeted": ["chest", "triceps"],
      "calories_per_min": 8,
      "theme": "upper_body"
    }
  }
]
```

### POST /api/generate-auto-workout-video
Génère et stream un workout personnalisé

**Request** :
```json
{
  "config": {
    "intensity": "medium_intensity",
    "intervals": {
      "work_time": 40,
      "rest_time": 20
    },
    "no_jump": false,
    "no_repeat": true,
    "exercice_intensity_levels": ["medium", "hard"],
    "use_block_structure": true,
    "show_timer": true,
    "show_progress_bar": true,
    "show_exercise_name": true
  },
  "total_duration": 600  // secondes
}
```

**Response** : `StreamingResponse` (video/mp4)

**Headers** :
- `X-Workout-ID` : UUID du workout créé
- `X-Exercise-Count` : Nombre d'exercices

---

## 🐛 Problèmes Connus

### ⚠️ Freeze Vidéo sur Workouts Longs (>20 exercices)
**Détecté** : Janvier 2026
**Cause** : Mémoire FFmpeg saturée lors concaténation progressive
**Solution Actuelle** : Gestion logs FFmpeg + cleanup progressif
**Solution Future** : Split en segments + concat finale
**Fichier** : `backend/app/services/video_service_optimized.py:487-549`

### ✅ Synchronisation Audio/Vidéo (RÉSOLU)
**Détecté** : Février 2026
**Cause** : Ajustement vitesse avec `setpts`
**Solution** : Abandon feature, utilisation stream copy
**Commit** : `f9d6cb2`

---

## 📚 Documentation Complète

Pour des informations détaillées, consultez :

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Documentation complète (1555 lignes)
  - System architecture détaillée
  - Database schema SQL
  - Deployment infrastructure
  - Development workflow

- **[docs/workout_block_generation.md](./docs/workout_block_generation.md)** - Système de blocs thématiques

- **[docs/workout_video_optimization_guide.md](./docs/workout_video_optimization_guide.md)** - Optimisations performance

- **[docs/workout_video_pregenerated_overlays_strategy.md](./docs/workout_video_pregenerated_overlays_strategy.md)** - Stratégie overlays (future)

---

## 🗺️ Roadmap

### **Q1 2026 (En cours)**
- ✅ Élimination ré-encodage (Complété - 02/02/26)
- 🔄 Cache overlays pré-générés (En cours)
- 📋 Parallélisation traitement exercices (Planifié)

### **Q2 2026**
- Authentication Supabase (OAuth Google, GitHub, Email)
- Subscription Stripe (Freemium → Premium)
- Workout history tracking
- Advanced analytics

### **Q3 2026**
- Mobile app (React Native)
- Offline workout downloads
- AI-powered recommendations
- Community features (social sharing)

---

## 💡 Contexte Important pour IA

### Philosophie de Développement

1. **Performance First** : Streaming, caching, lazy loading
2. **Simplicité > Complexité** : L'abandon du ré-encodage a amélioré l'app
3. **Cache Early, Cache Often** : Breaks pré-générés = ROI immédiat
4. **Measure Before Optimize** : Logs profilage révèlent vrais goulots
5. **Documentation Continue** : Facilite décisions futures

### Points d'Attention

⚠️ **Ne PAS réintroduire** :
- Ajustement vitesse vidéo (problèmes audio/perf)
- Ré-encodage systématique (utiliser stream copy)
- Génération breaks à la volée (utiliser cache)

✅ **À favoriser** :
- Stream copy autant que possible
- Téléchargements parallèles
- Cache multi-niveaux
- Overlays dynamiques synchronisés

### Fichiers Critiques

**Backend** :
- `app/services/video_service_optimized.py` - Cœur pipeline vidéo
- `app/services/workout_generator.py` - Logique sélection exercices
- `app/api/workouts.py` - Streaming endpoint

**Frontend** :
- `components/video/VideoPlayer.tsx` - Player avec overlays
- `app/(routes)/train/page.tsx` - Interface génération
- `lib/api.ts` - Client API

---

**Dernière mise à jour** : 2026-02-02
**Version** : 1.0.0
**Branche courante** : `dev`

Pour toute question, référez-vous à [ARCHITECTURE.md](./ARCHITECTURE.md) ou au code source avec les commentaires inline.
