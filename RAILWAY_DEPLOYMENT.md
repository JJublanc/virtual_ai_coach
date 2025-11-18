# Déploiement Railway - Virtual AI Coach Backend

## Vue d'ensemble

Ce guide décrit le déploiement du backend FastAPI sur Railway. Le backend utilise Supabase pour la base de données et le stockage vidéo, et FFmpeg pour le traitement vidéo.

## Prérequis

- Compte Railway (https://railway.app)
- Projet Supabase configuré avec :
  - Table `exercises` créée
  - Bucket de stockage `exercise-videos` configuré
  - Vidéos d'exercices uploadées

## Variables d'environnement requises

Configurez les variables suivantes dans Railway Dashboard > Variables :

### 🔴 Variables obligatoires

```bash
# Supabase Configuration (REQUIRED)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=XXX
SUPABASE_SERVICE_ROLE_KEY=XXX

# Feature Flag - Utiliser Supabase pour les exercices
USE_SUPABASE=true
```

### 🟡 Variables optionnelles (avec valeurs par défaut)

```bash
# Video Cache Configuration
VIDEO_CACHE_DIR=/tmp/exercise_videos
VIDEO_CACHE_MAX_SIZE_GB=5

# API Configuration (ne pas définir PORT - Railway l'injecte automatiquement)
API_HOST=0.0.0.0
```

## Étapes de déploiement

### 1. Créer un nouveau projet Railway

1. Connectez-vous à Railway (https://railway.app)
2. Cliquez sur "New Project"
3. **Sélectionnez "Deploy from GitHub repo"** (c'est l'option recommandée pour ce projet)
4. Autorisez Railway à accéder à votre repository GitHub
5. Sélectionnez le repository `virtual_ai_coach`
6. Railway détectera automatiquement que c'est une application Python

**Note** : Les autres options disponibles sont :
- **Database** : Pour créer uniquement une base de données (non applicable ici, nous utilisons Supabase)
- **Template** : Pour déployer depuis un template préconfigué (non applicable)
- **Docker Image** : Pour déployer une image Docker personnalisée (non nécessaire, Railway build automatiquement)
- **Function** : Pour des serverless functions (non applicable pour FastAPI)
- **Empty Project** : Pour un projet vide à configurer manuellement (non recommandé)

→ **Utilisez "Deploy from GitHub repo"** pour ce projet

### 2. Configurer les variables d'environnement

1. Dans le dashboard Railway, allez dans l'onglet "Variables"
2. Ajoutez les variables d'environnement listées ci-dessus
3. **Important** : Ne définissez PAS la variable `PORT` - Railway l'injecte automatiquement

### 3. Vérifier la configuration

Railway détectera automatiquement :
- `railway.json` pour la configuration de build/deploy
- `Procfile` comme commande de démarrage alternative
- `requirements.txt` pour les dépendances Python

### 4. Déployer

1. Railway lancera automatiquement le déploiement
2. Surveillez les logs dans l'onglet "Deployments"
3. Une fois déployé, notez l'URL fournie par Railway

## Configuration du frontend

Mettez à jour votre frontend Next.js local pour pointer vers le backend Railway :

```typescript
// frontend/lib/api.ts ou votre fichier de configuration API
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://your-app.railway.app';
```

Ou dans `.env.local` :
```bash
NEXT_PUBLIC_API_URL=https://your-app.railway.app
```

## Architecture

```
┌─────────────────┐         ┌──────────────────┐
│  Frontend       │         │  Backend         │
│  Next.js        │────────▶│  FastAPI         │
│  (Local)        │  HTTP   │  (Railway)       │
└─────────────────┘         └──────────────────┘
                                     │
                                     │
                            ┌────────┴────────┐
                            │                 │
                            ▼                 ▼
                    ┌──────────────┐  ┌──────────────┐
                    │  Supabase    │  │  FFmpeg      │
                    │  PostgreSQL  │  │  (Railway)   │
                    │  + Storage   │  │              │
                    └──────────────┘  └──────────────┘
```

## Points importants

### ✅ Avantages de cette configuration

- **FFmpeg préinstallé** : Railway installe automatiquement FFmpeg via Nixpacks
- **Python 3.13** : Support natif de la dernière version de Python
- **Health checks** : Endpoint `/health` configuré pour les vérifications
- **Restart automatique** : En cas d'échec (max 10 tentatives)
- **CORS configuré** : Pour le frontend local (`localhost:3000`)

### ⚠️ Limitations connues

- **Cache éphémère** : `/tmp` est vidé à chaque redémarrage - acceptable pour le développement
- **Timeout vidéo** : Pour les workouts très longs (>40min), considérer l'augmentation du timeout
- **Stockage** : Les vidéos doivent être dans Supabase Storage (pas de stockage local permanent)

## Endpoints disponibles

Après déploiement, testez ces endpoints :

- `GET /` - Redirige vers `/docs`
- `GET /health` - Health check
- `GET /docs` - Documentation Swagger
- `GET /exercises` - Liste des exercices
- `POST /workouts/generate` - Génération de workout

## Dépannage

### Problème : Application ne démarre pas

**Solution** : Vérifiez les logs Railway et assurez-vous que toutes les variables d'environnement obligatoires sont définies.

### Problème : Erreur "uv: command not found"

**Cause** : L'outil `uv` n'est pas disponible dans l'environnement Nixpacks de Railway.

**Solution** :
- Modifiez `buildCommand` dans [`railway.json`](railway.json:5) pour utiliser `pip` au lieu de `uv pip`
- Remplacez `uv pip install -r requirements.txt` par `pip install -r requirements.txt`
- Nixpacks inclut `pip` par défaut, donc cette commande fonctionnera sans problème

**Note** : Le fichier `requirements.txt` généré par `uv pip compile` est compatible avec `pip` standard car il utilise la syntaxe standard `package==version`.

### Problème : Erreur CORS

**Solution** : Vérifiez que votre frontend utilise bien `http://localhost:3000` (pas `127.0.0.1`).

### Problème : Vidéos non trouvées

**Solution** :
- Vérifiez que `USE_SUPABASE=true`
- Vérifiez les clés Supabase
- Vérifiez que les vidéos sont bien dans le bucket `exercise-videos`

### Problème : Timeout lors de la génération

**Solution** : Augmentez `healthcheckTimeout` dans `railway.json` ou réduisez la durée du workout.

## Commandes utiles

### Tester localement avec la config Railway

```bash
# Installer les dépendances (avec pip standard)
pip install -r requirements.txt

# Ou avec uv si disponible localement
uv pip install -r requirements.txt

# Démarrer le serveur (avec PORT simulé)
PORT=8000 uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

# Tester le health check
curl http://localhost:8000/health
```

### Logs Railway

```bash
# Via CLI Railway
railway logs

# Ou via le dashboard web
# Railway Dashboard > Deployments > View Logs
```

## Mise en production

Pour passer en production :

1. **CORS** : Ajoutez le domaine de production dans [`backend/app/main.py`](backend/app/main.py:18)
2. **Variables** : Créez un environnement de production séparé sur Railway
3. **Supabase** : Utilisez un projet Supabase de production dédié
4. **Monitoring** : Configurez les alertes Railway
5. **Backup** : Assurez-vous que Supabase est configuré avec des backups automatiques

## Support

- Documentation Railway : https://docs.railway.app
- Documentation FastAPI : https://fastapi.tiangolo.com
- Documentation Supabase : https://supabase.com/docs
