# Stratégie Base de Données - Virtual AI Coach

## Analyse des besoins

### Données à stocker

1. **Exercices** (quasi-statiques, peu de writes, beaucoup de reads)
   - ~50-200 exercices au total
   - Métadonnées : nom, description, vidéo, difficulté, etc.
   - Relations : catégories, muscles ciblés

2. **Séances/Workouts** (dynamiques, créées par utilisateurs)
   - Compositions d'exercices
   - Configurations personnalisées
   - Historique si utilisateur authentifié

3. **Utilisateurs** (si authentification implémentée)
   - Profil, préférences
   - Historique séances
   - Goals, progression

4. **Fichiers** (vidéos, thumbnails)
   - Stockage séparé (Supabase Storage ou Backblaze B2)
   - Références dans DB

### Patterns d'accès

- **Lectures** : 90% du trafic (listing exercices, récupération séances)
- **Écritures** : 10% (création séances, logs utilisateur)
- **Pics** : Génération séance = multiple reads rapides
- **Latence critique** : Listing exercices doit être <100ms
- **Concurrence** : Faible au départ (MVP), modérée à terme

## Comparaison des options

### 1. Supabase ⭐ RECOMMANDÉ Phase 1-2

**Description :** PostgreSQL as a Service + Auth + Storage + Realtime

**Avantages :**
- ✅ **All-in-one** : Database + Auth + Storage dans un seul service
- ✅ **PostgreSQL** : Robuste, relationnel, performant
- ✅ **Auth gratuite** : JWT, OAuth, Row Level Security intégrés
- ✅ **Realtime** : WebSocket pour updates temps réel (optionnel)
- ✅ **Storage** : Alternative à S3 pour vidéos (gratuit 1GB)
- ✅ **Client auto-généré** : SDK TypeScript/Python
- ✅ **Dashboard** : UI pour gérer données
- ✅ **Edge Functions** : Serverless functions si besoin
- ✅ **Open source** : Peut être auto-hébergé plus tard

**Inconvénients :**
- ⚠️ Latence depuis certaines régions (EU ouest OK)
- ⚠️ Limits Free tier : 500MB DB, 1GB storage, 2GB bandwidth/mois
- ⚠️ Pas de scaling horizontal automatique

**Coût :**
- Free : 500MB DB + 1GB Storage + 2GB bandwidth
- Pro (25$/mois) : 8GB DB + 100GB Storage + 250GB bandwidth
- **Idéal pour :** MVP et Growth (0-1000 users)

**Intégration :**
```python
# Backend FastAPI
from supabase import create_client, Client

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Query exercices
exercises = supabase.table('exercises').select('*').execute()

# Auth (si implémenté)
user = supabase.auth.sign_up({
    'email': email,
    'password': password
})
```

---

### 2. Railway PostgreSQL

**Description :** PostgreSQL managé inclus dans Railway (si backend hébergé là)

**Avantages :**
- ✅ **Gratuit** dans Railway Free tier
- ✅ **Co-localisé** avec backend = latence minimale
- ✅ **PostgreSQL standard** : Toutes fonctionnalités
- ✅ **Backups automatiques**
- ✅ **Scaling vertical facile**

**Inconvénients :**
- ❌ Pas d'Auth intégrée (à implémenter)
- ❌ Pas de Storage intégré
- ❌ Pas de Realtime natif
- ❌ Limité au provider Railway

**Coût :**
- Free : 1GB DB (inclus dans Railway Free)
- Hobby (10€/mois) : 8GB DB inclus
- **Idéal pour :** MVP simple sans auth

---

### 3. Neon (PostgreSQL Serverless)

**Description :** PostgreSQL serverless avec autoscaling et branching

**Avantages :**
- ✅ **Serverless** : Pay per use, auto-sleep
- ✅ **Branching** : Git-like pour DB (staging/prod)
- ✅ **Auto-scaling** : Scale to zero quand inactif
- ✅ **Faible latence** : Edge network global
- ✅ **PostgreSQL standard**

**Inconvénients :**
- ⚠️ Pas d'Auth intégrée
- ⚠️ Pas de Storage
- ⚠️ Jeune (2022) mais stable

**Coût :**
- Free : 0.5GB storage, 10GB bandwidth/mois
- Pro (19$/mois) : 100GB storage, autoscaling
- **Idéal pour :** Production avec traffic variable

---

### 4. PlanetScale (MySQL Serverless)

**Description :** MySQL serverless avec branching et scaling horizontal

**Avantages :**
- ✅ **Scaling horizontal** : Sharding automatique
- ✅ **Branching** : Dev/staging/prod branches
- ✅ **Serverless** : Pay per use
- ✅ **Très performant** : Basé sur Vitess (YouTube scale)

**Inconvénients :**
- ❌ **MySQL** : Moins de fonctionnalités que PostgreSQL
- ❌ Pas d'Auth/Storage intégrés
- ⚠️ Pas de foreign keys (limité)

**Coût :**
- Hobby (0€) : 5GB storage, 1 milliard rows reads/mois
- Scaler (29$/mois) : 10GB storage, autoscaling
- **Idéal pour :** Scale importante (>10K users)

---

### 5. MongoDB Atlas

**Description :** MongoDB as a Service (NoSQL)

**Avantages :**
- ✅ **Flexible schema** : Bon pour itérations rapides
- ✅ **Free tier généreux** : 512MB gratuit
- ✅ **Scaling horizontal** : Sharding natif
- ✅ **Aggregation puissante**

**Inconvénients :**
- ⚠️ **NoSQL** : Pas de relations strictes
- ⚠️ Requêtes complexes plus difficiles
- ⚠️ Pas d'Auth/Storage intégrés
- ⚠️ Python driver moins naturel que SQL

**Coût :**
- Free : 512MB
- Shared (9$/mois) : 2GB
- **Idéal pour :** Apps avec schéma très variable

---

### 6. Firebase/Firestore

**Description :** NoSQL Google avec Auth et Hosting

**Avantages :**
- ✅ **All-in-one** : DB + Auth + Hosting + Storage
- ✅ **Realtime** : Synchro temps réel native
- ✅ **Offline first** : Cache local automatique
- ✅ **Free tier** : Gratuit jusqu'à 1GB + 10K writes/jour

**Inconvénients :**
- ❌ **NoSQL limité** : Pas de requêtes complexes
- ❌ **Coûts imprévisibles** : Facturé par opération
- ❌ **Lock-in Google** : Difficile à migrer
- ❌ **Pas optimal pour Python backend**

**Coût :**
- Spark (Free) : 1GB storage, 10GB bandwidth
- Blaze (Pay as you go) : Variable
- **Idéal pour :** Apps mobile-first avec Next.js only

---

## Recommandation par phase

### Phase 1 : MVP (0-100 users) - **Supabase Free**

**Pourquoi :**
- Tout-en-un : DB + Auth future + Storage vidéos possiblement
- Gratuit jusqu'à 500MB DB (largement suffisant pour 200 exercices + 1000 séances)
- Setup rapide, zero ops
- Python SDK officiel

**Stack complète :**
```
Frontend: Next.js (Vercel Free)
Backend: FastAPI (Railway Free ou local dev)
Database: Supabase Free
Storage Vidéos: Supabase Storage (1GB gratuit)
Auth: Supabase Auth (quand implémenté)
```

**Migration :**
Si Supabase devient limitant → Neon ou Railway PostgreSQL (dump/restore PostgreSQL standard)

---

### Phase 2 : Growth (100-1000 users) - **Supabase Pro OU Neon**

**Option A : Supabase Pro (25$/mois)**
- Si vous utilisez Auth + Storage ensemble
- Si vous voulez Realtime (live updates séances)
- 8GB DB largement suffisant

**Option B : Neon Pro (19$/mois)**
- Si Auth géré autrement (ex: Clerk, Auth0)
- Si Storage sur service séparé (Backblaze B2, AWS S3)
- Branching DB utile pour staging/prod
- Meilleure performance scaling

**Décision :** Dépend si vous utilisez les features Supabase ou juste la DB

---

### Phase 3 : Scale (1000+ users) - **Neon ou PlanetScale**

**Neon :**
- Si PostgreSQL features requises (JSON, full-text search, etc.)
- Autoscaling automatique
- Read replicas pour performances

**PlanetScale :**
- Si besoin scaling horizontal massif
- Sharding automatique
- Très haute performance
- Trade-off : MySQL limitations

---

## Schéma de données révisé (PostgreSQL)

### Tables principales

```sql
-- EXERCICES (quasi-statique)
CREATE TABLE exercises (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(50), -- Nom icône ou emoji
    video_url TEXT NOT NULL, -- URL Supabase Storage ou S3
    thumbnail_url TEXT,
    default_duration INTEGER NOT NULL, -- en secondes
    difficulty VARCHAR(20) CHECK (difficulty IN ('easy', 'medium', 'hard')),
    has_jump BOOLEAN DEFAULT false,
    metadata JSONB, -- {muscles_targeted: [], equipment: []}
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Index pour recherche rapide
CREATE INDEX idx_exercises_difficulty ON exercises(difficulty);
CREATE INDEX idx_exercises_metadata ON exercises USING gin(metadata);

-- CATÉGORIES D'EXERCICES (many-to-many)
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL, -- 'cardio', 'strength', 'flexibility'
    description TEXT
);

CREATE TABLE exercise_categories (
    exercise_id UUID REFERENCES exercises(id) ON DELETE CASCADE,
    category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (exercise_id, category_id)
);

-- SÉANCES/WORKOUTS
CREATE TABLE workouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID, -- NULL si non authentifié, sinon REFERENCES users(id)
    name VARCHAR(100),
    config JSONB NOT NULL, -- Configuration complète (voir type WorkoutConfig)
    total_duration INTEGER, -- Calculé en secondes
    rounds INTEGER,
    ai_generated BOOLEAN DEFAULT false,
    ai_prompt TEXT, -- Si généré par IA
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'ready', 'in_progress', 'completed')),
    video_url TEXT, -- URL si pré-rendu
    created_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);

-- Index pour queries fréquentes
CREATE INDEX idx_workouts_user_id ON workouts(user_id);
CREATE INDEX idx_workouts_status ON workouts(status);
CREATE INDEX idx_workouts_created_at ON workouts(created_at DESC);

-- EXERCICES DANS SÉANCE (many-to-many avec ordre)
CREATE TABLE workout_exercises (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workout_id UUID REFERENCES workouts(id) ON DELETE CASCADE,
    exercise_id UUID REFERENCES exercises(id) ON DELETE RESTRICT,
    order_index INTEGER NOT NULL,
    custom_duration INTEGER, -- Override du default_duration si nécessaire
    UNIQUE(workout_id, order_index)
);

CREATE INDEX idx_workout_exercises_workout ON workout_exercises(workout_id);

-- UTILISATEURS (Phase 2, avec Supabase Auth)
-- Note: Supabase gère auth.users, on étend juste le profil
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name VARCHAR(100),
    avatar_url TEXT,
    fitness_level VARCHAR(20) CHECK (fitness_level IN ('beginner', 'intermediate', 'advanced')),
    preferences JSONB, -- {favorite_exercises: [], excluded_exercises: []}
    goals TEXT[],
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- HISTORIQUE ACTIVITÉ (optionnel, analytics)
CREATE TABLE workout_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workout_id UUID REFERENCES workouts(id),
    user_id UUID REFERENCES auth.users(id),
    started_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER, -- Temps réel passé
    exercises_completed INTEGER,
    feedback JSONB -- {difficulty: 'too_easy', enjoyed: true, etc.}
);
```

### Exemple de données JSONB

```sql
-- Config d'une séance
{
  "intensity": "medium_intensity",
  "intervals": {
    "work_time": 40,
    "rest_time": 20
  },
  "no_repeat": false,
  "no_jump": false,
  "intensity_levels": ["easy", "medium", "hard"],
  "include_warm_up": true,
  "include_cool_down": true,
  "target_duration": 30
}

-- Metadata exercice
{
  "muscles_targeted": ["quadriceps", "glutes", "core"],
  "equipment_needed": [],
  "calories_per_min": 8.5,
  "alternative_exercises": ["uuid1", "uuid2"]
}

-- Préférences utilisateur
{
  "favorite_exercises": ["uuid1", "uuid2"],
  "excluded_exercises": ["uuid3"],
  "preferred_intensity": "medium_intensity",
  "typical_duration_min": 30,
  "training_days": ["monday", "wednesday", "friday"]
}
```

## Queries fréquentes optimisées

```sql
-- 1. Lister tous les exercices avec catégories
SELECT 
    e.*,
    array_agg(c.name) as categories
FROM exercises e
LEFT JOIN exercise_categories ec ON e.id = ec.exercise_id
LEFT JOIN categories c ON ec.category_id = c.id
GROUP BY e.id;

-- 2. Récupérer une séance complète avec exercices
SELECT 
    w.*,
    json_agg(
        json_build_object(
            'exercise', e.*,
            'order', we.order_index,
            'custom_duration', we.custom_duration
        ) ORDER BY we.order_index
    ) as exercises
FROM workouts w
JOIN workout_exercises we ON w.id = we.workout_id
JOIN exercises e ON we.exercise_id = e.id
WHERE w.id = $1
GROUP BY w.id;

-- 3. Recherche exercices par difficulté et catégorie
SELECT e.*
FROM exercises e
JOIN exercise_categories ec ON e.id = ec.exercise_id
JOIN categories c ON ec.category_id = c.id
WHERE 
    e.difficulty = 'medium'
    AND c.name = 'cardio'
    AND (NOT e.has_jump OR e.has_jump = false); -- Si no_jump activé

-- 4. Historique séances utilisateur
SELECT 
    w.*,
    ws.started_at,
    ws.completed_at,
    ws.duration_seconds
FROM workouts w
JOIN workout_sessions ws ON w.id = ws.workout_id
WHERE ws.user_id = $1
ORDER BY ws.started_at DESC
LIMIT 10;
```

## Gestion du cache

Pour optimiser les reads (90% du traffic) :

```python
# Backend FastAPI avec Redis cache
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

@app.get("/api/exercises")
@cache(expire=3600)  # 1h cache
async def get_exercises():
    # Query Supabase
    exercises = supabase.table('exercises').select('*').execute()
    return exercises.data
```

**Cache strategy :**
- Exercices : Cache 1h (rarement changent)
- Workouts user : Pas de cache (personnalisé)
- Catégories : Cache infini (quasi-statique)

## Migration strategy

**MVP → Growth :**
```bash
# Dump PostgreSQL standard
pg_dump $SUPABASE_URL > backup.sql

# Restore vers Neon/Railway
psql $NEW_DB_URL < backup.sql
```

**NoSQL → SQL :**
- Éviter MongoDB/Firestore au départ
- Migration complexe et risquée
- Préférer PostgreSQL dès le début

## Décision finale recommandée

### **Supabase pour MVP et Growth**

**Raisons :**
1. All-in-one = moins de services à gérer
2. Auth gratuite future-proof
3. Storage 1GB gratuit peut stocker thumbnails
4. PostgreSQL standard = migration facile si besoin
5. Free tier généreux pour démarrer
6. Dashboard UI pour debug/admin

**Setup :**
```bash
# 1. Créer projet Supabase (supabase.com)
# 2. Créer tables via SQL Editor
# 3. Configurer .env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key

# 4. Installer SDK Python
pip install supabase

# 5. Utiliser Supabase Storage pour vidéos (recommandé pour MVP)
# Upload vers Supabase Storage au lieu de services externes
```

**Migration si croissance forte :**
- Supabase Pro (25$/mois) jusqu'à 5K users
- Puis Neon + Auth séparé (Clerk/Auth0) si >10K users
- Puis PlanetScale si >100K users

## Prochaines étapes

1. Créer compte Supabase
2. Initialiser schéma DB via SQL Editor
3. Seed données exercices initiales
4. Connecter FastAPI avec Supabase client
5. Tester queries de base