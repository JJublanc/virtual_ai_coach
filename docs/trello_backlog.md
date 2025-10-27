
# Backlog Trello - Virtual AI Coach

Cette backlog est organisée en colonnes Trello suivant la progression : **Local → Dev → Prod**

---

### 🎯 PHASE 0 : Configuration Environnement Local

#### ENV-001 : Setup environnement de développement
**Description :** Installer et configurer tous les outils nécessaires au développement local

**Tâches :**
- [x] Installer Python 3.11+ avec pyenv
- [x] Installer Node.js 20+ avec nvm
- [x] Installer Docker Desktop
- [x] Installer FFmpeg (brew/apt/chocolatey)
- [x] Configurer VSCode avec extensions (Python, ESLint, Prettier)
- [x] Installer uv et créer un .venv
- [x] Installer PostgreSQL local (ou via Docker)


**Critères d'acceptation :**
- ✅ `python --version` retourne 3.11+
- ✅ `node --version` retourne 20+
- ✅ `ffmpeg -version` fonctionne
- ✅ Docker Desktop démarre correctement
- ✅ Postgre est installé

**Labels :** `setup`, `local`, `p0-critical`

---

#### ENV-002 : Initialiser repository Git
**Description :** Créer la structure Git et configurer les branches

**Tâches :**
- [x] Créer repository GitHub `virtual-ai-coach`
- [x] Configurer `.gitignore` (Python, Node, env files)
- [x] Créer branches : `main`, `dev`, `feat/*`
- [x] Configurer protection branche `main`
- [x] Ajouter README.md avec instructions setup
- [ ] Installer et configurer les précommit


**Critères d'acceptation :**
- ✅ Repository accessible sur GitHub
- ✅ Branches configurées correctement
- ✅ `.gitignore` empêche commit de fichiers sensibles

**Labels :** `setup`, `git`, `p0-critical`

---

### 🎯 PHASE 1 : MVP Local - Backend

#### BACK-001 : Initialiser projet FastAPI
**Description :** Créer la structure backend Python avec FastAPI

**Tâches :**
- [x] Créer dossier `backend/`
- [x] Initialiser virtual environment Python
- [x] Ajouter les modules utiles à uv :
  - fastapi
  - uvicorn
  - ffmpeg-python
  - python-multipart
  - pydantic
- [x] Créer structure de dossiers :
  ```
  backend/
  ├── app/
  │   ├── __init__.py
  │   ├── main.py
  │   ├── models/
  │   ├── services/
  │   ├── api/
  │   └── config.py
  ├── tests/
  ```
- [ ] Créer `main.py` avec route `/health` de test
- [ ] Lancer serveur : `uvicorn app.main:app --reload`

**Critères d'acceptation :**
- ✅ `http://localhost:8000/health` retourne 200 OK
- ✅ Documentation auto disponible sur `/docs`

**Labels :** `backend`, `fastapi`, `p0-critical`

---

#### BACK-002 : Créer modèles de données
**Description :** Définir les modèles Pydantic pour les exercices et workouts

**Tâches :**
- [ ] Créer `models/exercise.py` avec modèle Exercise
- [ ] Créer `models/workout.py` avec modèle WorkoutSession
- [ ] Créer `models/config.py` avec WorkoutConfig
- [ ] Ajouter validation Pydantic sur tous les champs
- [ ] Créer fichier JSON mock avec 3-5 exercices de test

**Critères d'acceptation :**
- ✅ Modèles valident correctement les données
- ✅ Fichier mock `exercises.json` chargeable

**Labels :** `backend`, `models`, `p1-high`

---

#### BACK-003 : API GET /api/exercises
**Description :** Créer endpoint pour lister les exercices disponibles

**Tâches :**
- [ ] Créer `api/exercises.py` avec router FastAPI
- [ ] Implémenter GET `/api/exercises`
- [ ] Charger données depuis `exercises.json`
- [ ] Ajouter tests unitaires
- [ ] Ajouter CORS middleware pour frontend

**Critères d'acceptation :**
- ✅ Endpoint retourne liste d'exercices en JSON
- ✅ Tests passent avec `pytest`

**Labels :** `backend`, `api`, `p1-high`

---

#### BACK-004 : Service de traitement vidéo FFmpeg
**Description :** Créer le service de génération vidéo avec FFmpeg

**Tâches :**
- [ ] Créer `services/video_service.py`
- [ ] Implémenter `build_ffmpeg_command()` pour concaténation
- [ ] Implémenter `apply_speed_adjustment()` selon intensité
- [ ] Tester avec 2 vidéos MOV du dossier `exercices_generation/outputs/`
- [ ] Ajouter logs détaillés pour debugging

**Critères d'acceptation :**
- ✅ Concaténation de 2 vidéos fonctionne
- ✅ Ajustement vitesse appliqué correctement
- ✅ Vidéo de sortie lisible

**Labels :** `backend`, `video`, `ffmpeg`, `p0-critical`

---

#### BACK-005 : API POST /api/generate-workout-video
**Description :** Créer endpoint de génération vidéo en streaming

**Tâches :**
- [ ] Créer route POST `/api/generate-workout-video`
- [ ] Recevoir configuration workout en JSON
- [ ] Appeler video_service pour générer vidéo
- [ ] Streamer la sortie FFmpeg via StreamingResponse
- [ ] Gérer les erreurs (timeout, fichiers manquants)
- [ ] Tester avec Postman/curl

**Critères d'acceptation :**
- ✅ Endpoint retourne vidéo MP4 streamée
- ✅ Timeout configuré à 5 minutes max
- ✅ Erreurs gérées avec codes HTTP appropriés

**Labels :** `backend`, `api`, `video`, `p0-critical`

---

### 🎯 PHASE 1 : MVP Local - Frontend

#### FRONT-001 : Initialiser projet Next.js
**Description :** Créer l'application frontend avec Next.js 14+

**Tâches :**
- [ ] Créer projet : `npx create-next-app@latest frontend`
- [ ] Choisir : TypeScript, App Router, Tailwind CSS
- [ ] Installer dépendances :
  - @shadcn/ui
  - zustand
  - @tanstack/react-query
  - react-player
- [ ] Configurer structure de dossiers selon `frontend_nextjs_plan.md`
- [ ] Lancer dev server : `npm run dev`

**Critères d'acceptation :**
- ✅ `http://localhost:3000` accessible
- ✅ Hot reload fonctionne

**Labels :** `frontend`, `nextjs`, `p0-critical`

---

#### FRONT-002 : Créer composants de layout
**Description :** Implémenter le header et la structure principale

**Tâches :**
- [ ] Créer `components/layout/Header.tsx`
- [ ] Créer navigation : Goals, Plan, Train
- [ ] Créer `components/layout/MainLayout.tsx` (2 colonnes)
- [ ] Implémenter design selon mockup
- [ ] Rendre responsive (mobile, tablet, desktop)

**Critères d'acceptation :**
- ✅ Header visible avec navigation
- ✅ Layout 2 colonnes sur desktop
- ✅ Responsive sur mobile

**Labels :** `frontend`, `ui`, `layout`, `p1-high`

---

#### FRONT-003 : Page Train - Sélection exercices
**Description :** Créer interface de sélection d'exercices

**Tâches :**
- [ ] Créer page `app/train/page.tsx`
- [ ] Créer `components/exercises/ExerciseList.tsx`
- [ ] Implémenter drag & drop avec @dnd-kit
- [ ] Appeler API `/api/exercises` avec React Query
- [ ] Afficher liste d'exercices sélectionnables

**Critères d'acceptation :**
- ✅ Exercices chargés depuis backend
- ✅ Drag & drop fonctionne
- ✅ Liste mise à jour en temps réel

**Labels :** `frontend`, `train-page`, `p0-critical`

---

#### FRONT-004 : Panneau de configuration workout
**Description :** Créer le panneau de configuration avec intensité et paramètres

**Tâches :**
- [ ] Créer `components/controls/QuickSetup.tsx`
- [ ] Créer `components/controls/ParameterizedSetup.tsx`
- [ ] Implémenter toggles : No repeat, No jump
- [ ] Implémenter sliders : Work/Rest time
- [ ] Implémenter checkboxes : Intensity levels
- [ ] Gérer state avec Zustand

**Critères d'acceptation :**
- ✅ Tous les contrôles fonctionnels
- ✅ State partagé via Zustand
- ✅ UI correspond au design

**Labels :** `frontend`, `ui`, `controls`, `p1-high`

---

#### FRONT-005 : Player vidéo avec overlays
**Description :** Créer le composant video player

**Tâches :**
- [ ] Créer `components/video/VideoPlayer.tsx`
- [ ] Intégrer React Player ou HTML5 video
- [ ] Créer `components/video/TimerCircle.tsx`
- [ ] Créer `components/video/ProgressBar.tsx`
- [ ] Créer `components/video/RoundIndicator.tsx`
- [ ] Tester lecture vidéo streamée depuis backend

**Critères d'acceptation :**
- ✅ Vidéo joue correctement
- ✅ Overlays affichés
- ✅ Timer et progression fonctionnent

**Labels :** `frontend`, `video`, `ui`, `p0-critical`

---

#### FRONT-006 : Intégration génération vidéo
**Description :** Connecter frontend au backend pour générer et lire vidéos

**Tâches :**
- [ ] Créer bouton "Generate Training"
- [ ] Appeler POST `/api/generate-workout-video` avec config
- [ ] Gérer loading state pendant génération
- [ ] Afficher vidéo dans player dès réception
- [ ] Gérer erreurs réseau

**Critères d'acceptation :**
- ✅ Vidéo générée et jouée end-to-end
- ✅ Loading spinner pendant génération
- ✅ Erreurs affichées à l'utilisateur

**Labels :** `frontend`, `integration`, `p0-critical`

---

### 🎯 PHASE 1 : MVP Local - Tests & Optimisation

#### TEST-001 : Tests end-to-end MVP
**Description :** Valider le parcours complet utilisateur en local

**Tâches :**
- [ ] Sélectionner 3 exercices
- [ ] Configurer intensité "Medium"
- [ ] Générer vidéo
- [ ] Vérifier lecture complète
- [ ] Tester différentes configurations
- [ ] Documenter bugs trouvés

**Critères d'acceptation :**
- ✅ Parcours complet fonctionne sans erreur
- ✅ Vidéo générée est correcte
- ✅ Temps de génération < 30 secondes

**Labels :** `testing`, `e2e`, `p0-critical`

---

#### OPT-001 : Optimisation performances locales
**Description :** Améliorer les performances de génération vidéo

**Tâches :**
- [ ] Profiler temps FFmpeg
- [ ] Optimiser preset FFmpeg (ultrafast)
- [ ] Réduire taille chunks streaming
- [ ] Ajouter cache pour exercices fréquents
- [ ] Documenter métriques (temps génération, taille sortie)

**Critères d'acceptation :**
- ✅ Temps génération réduit de 20%
- ✅ Streaming fluide sans buffering

**Labels :** `optimization`, `performance`, `p2-medium`

---

### 🎯 PHASE 2 : Infrastructure Dev

#### INFRA-DEV-001 : Créer compte Supabase
**Description :** Setup compte et projet Supabase pour environnement dev

**Tâches :**
- [ ] Créer compte sur supabase.com
- [ ] Créer projet "virtual-ai-coach-dev"
- [ ] Noter credentials (URL, anon key, service key)
- [ ] Créer fichier `.env.dev` avec credentials
- [ ] Tester connexion depuis backend local

**Critères d'acceptation :**
- ✅ Projet Supabase créé
- ✅ Connexion DB réussie

**Labels :** `infra`, `database`, `dev`, `p0-critical`

---

#### INFRA-DEV-002 : Créer schéma DB Supabase
**Description :** Implémenter le schéma PostgreSQL complet

**Tâches :**
- [ ] Copier schéma SQL depuis `database_strategy.md`
- [ ] Exécuter dans SQL Editor Supabase
- [ ] Créer tables : exercises, categories, workouts, workout_exercises
- [ ] Créer index pour performances
- [ ] Vérifier tables créées via dashboard

**Critères d'acceptation :**
- ✅ Toutes les tables créées
- ✅ Relations foreign keys fonctionnelles
- ✅ Index créés

**Labels :** `database`, `schema`, `dev`, `p0-critical`

---

#### INFRA-DEV-003 : Populate DB avec exercices
**Description :** Insérer les exercices existants dans Supabase

**Tâches :**
- [ ] Créer script `backend/scripts/seed_exercises.py`
- [ ] Lire métadonnées depuis dossier `exercices_generation/outputs/`
- [ ] Insérer exercices via Supabase client Python
- [ ] Vérifier données via dashboard Supabase
- [ ] Ajouter 10-15 exercices minimum

**Critères d'acceptation :**
- ✅ Script d'insertion fonctionne
- ✅ Exercices visibles dans Supabase
- ✅ Métadonnées correctes

**Labels :** `database`, `data`, `dev`, `p1-high`

---

#### INFRA-DEV-004 : Upload vidéos vers Supabase Storage
**Description :** Migrer vidéos MOV vers Supabase Storage

**Tâches :**
- [ ] Créer bucket "exercise-videos" dans Supabase Storage
- [ ] Configurer bucket en public (ou avec signed URLs)
- [ ] Créer script `backend/scripts/upload_videos.py`
- [ ] Uploader toutes les vidéos MOV
- [ ] Mettre à jour table exercises avec URLs Supabase

**Critères d'acceptation :**
- ✅ Bucket créé et configuré
- ✅ Vidéos uploadées (vérifier via dashboard)
- ✅ URLs accessibles

**Labels :** `storage`, `videos`, `dev`, `p0-critical`

---

#### INFRA-DEV-005 : Modifier backend pour utiliser Supabase
**Description :** Adapter le backend pour interroger Supabase au lieu de JSON local

**Tâches :**
- [ ] Installer `pip install supabase`
- [ ] Créer `backend/app/db/supabase_client.py`
- [ ] Modifier `/api/exercises` pour query Supabase
- [ ] Modifier video_service pour charger vidéos depuis Storage
- [ ] Tester end-to-end avec nouvelles sources

**Critères d'acceptation :**
- ✅ Exercices chargés depuis Supabase
- ✅ Vidéos streamées depuis Supabase Storage
- ✅ Pas de régression fonctionnelle

**Labels :** `backend`, `database`, `integration`, `p0-critical`

---

#### INFRA-DEV-006 : Déployer backend sur Railway (Dev)
**Description :** Déployer le backend FastAPI sur Railway environnement dev

**Tâches :**
- [ ] Créer compte Railway
- [ ] Créer nouveau projet "virtual-ai-coach-backend-dev"
- [ ] Connecter repository GitHub
- [ ] Configurer Dockerfile pour FastAPI
- [ ] Configurer variables d'environnement (Supabase credentials)
- [ ] Déclencher premier déploiement
- [ ] Vérifier `/health` endpoint accessible

**Critères d'acceptation :**
- ✅ Backend déployé et accessible
- ✅ URL publique fonctionne
- ✅ Logs visibles dans Railway dashboard

**Labels :** `infra`, `backend`, `railway`, `dev`, `p0-critical`

---

#### INFRA-DEV-007 : Déployer frontend sur Vercel (Dev)
**Description :** Déployer le frontend Next.js sur Vercel environnement dev

**Tâches :**
- [ ] Créer compte Vercel
- [ ] Connecter repository GitHub
- [ ] Créer projet "virtual-ai-coach-dev"
- [ ] Configurer variable d'environnement `NEXT_PUBLIC_API_URL` (Railway URL)
- [ ] Configurer branche de déploiement : `develop`
- [ ] Déclencher déploiement
- [ ] Tester app déployée

**Critères d'acceptation :**
- ✅ Frontend déployé sur Vercel
- ✅ App accessible via URL Vercel
- ✅ Connexion au backend Railway fonctionne

**Labels :** `infra`, `frontend`, `vercel`, `dev`, `p0-critical`

---

#### INFRA-DEV-008 : Tests environnement Dev complet
**Description :** Valider le stack complet en environnement dev

**Tâches :**
- [ ] Tester génération vidéo end-to-end sur dev
- [ ] Vérifier performances (latence, streaming)
- [ ] Tester depuis différents appareils
- [ ] Documenter URLs dev (frontend, backend, DB)
- [ ] Créer guide de déploiement dans README

**Critères d'acceptation :**
- ✅ Parcours utilisateur complet fonctionne
- ✅ Pas d'erreurs 500
- ✅ Documentation à jour

**Labels :** `testing`, `dev`, `integration`, `p1-high`

---

### 🎯 PHASE 3 : Infrastructure Production

#### INFRA-PROD-001 : Acheter nom de domaine
**Description :** Acquérir le nom de domaine via OVH

**Tâches :**
- [ ] Rechercher disponibilité domaine souhaité sur ovh.com
- [ ] Acheter domaine .com ou .fr (~10-12€/an)
- [ ] Configurer protection WhoisGuard
- [ ] Noter credentials compte OVH
- [ ] Accéder au panel DNS OVH

**Critères d'acceptation :**
- ✅ Domaine acheté et actif
- ✅ Accès panel DNS configuré

**Labels :** `infra`, `domain`, `prod`, `p0-critical`

---

#### INFRA-PROD-002 : Créer projet Supabase Production
**Description :** Setup projet Supabase séparé pour production

**Tâches :**
- [ ] Créer nouveau projet "virtual-ai-coach-prod"
- [ ] Choisir région EU (Paris ou Frankfurt)
- [ ] Souscrire plan Pro si nécessaire (25$/mois)
- [ ] Copier schéma DB depuis dev → prod
- [ ] Configurer backups automatiques
- [ ] Noter nouveaux credentials prod

**Critères d'acceptation :**
- ✅ Projet prod créé et isolé de dev
- ✅ Schéma DB identique
- ✅ Backups configurés

**Labels :** `infra`, `database`, `prod`, `p0-critical`

---

#### INFRA-PROD-003 : Migrer données vers Supabase Prod
**Description :** Copier exercices et vidéos vers environnement prod

**Tâches :**
- [ ] Exporter données depuis Supabase Dev
- [ ] Créer bucket Storage "exercise-videos" en prod
- [ ] Uploader toutes les vidéos vers bucket prod
- [ ] Importer données exercices en prod
- [ ] Vérifier intégrité des données

**Critères d'acceptation :**
- ✅ Toutes les données migrées
- ✅ Vidéos accessibles
- ✅ Aucune perte de données

**Labels :** `infra`, `data`, `migration`, `prod`, `p0-critical`

---

#### INFRA-PROD-004 : Déployer backend sur Railway (Prod)
**Description :** Créer déploiement production du backend

**Tâches :**
- [ ] Créer nouveau projet Railway "virtual-ai-coach-backend-prod"
- [ ] Configurer branche `main` pour auto-deploy
- [ ] Configurer variables d'environnement Supabase Prod
- [ ] Upgrader vers Railway Hobby plan si nécessaire (10€/mois)
- [ ] Configurer health checks
- [ ] Activer auto-scaling

**Critères d'acceptation :**
- ✅ Backend prod déployé
- ✅ Variables d'environnement correctes
- ✅ Health checks passent

**Labels :** `infra`, `backend`, `railway`, `prod`, `p0-critical`

---

#### INFRA-PROD-005 : Configurer DNS pour backend
**Description :** Pointer api.votredomaine.com vers Railway

**Tâches :**
- [ ] Aller dans panel DNS OVH
- [ ] Créer enregistrement CNAME : `api` → `[railway-url]`
- [ ] Attendre propagation DNS (jusqu'à 24h)
- [ ] Ajouter domaine custom dans Railway dashboard
- [ ] Vérifier SSL automatique activé
- [ ] Tester `https://api.votredomaine.com/health`

**Critères d'acceptation :**
- ✅ DNS pointe vers Railway
- ✅ SSL actif (cadenas vert)
- ✅ API accessible via domaine custom

**Labels :** `infra`, `dns`, `backend`, `prod`, `p0-critical`

---

#### INFRA-PROD-006 : Déployer frontend sur Vercel (Prod)
**Description :** Créer déploiement production du frontend

**Tâches :**
- [ ] Créer nouveau projet Vercel "virtual-ai-coach-prod"
- [ ] Configurer branche `main` pour auto-deploy
- [ ] Configurer variable `NEXT_PUBLIC_API_URL=https://api.votredomaine.com`
- [ ] Upgrader vers Vercel Pro si nécessaire (20$/mois - optionnel)
- [ ] Déclencher déploiement production

**Critères d'acceptation :**
- ✅ Frontend prod déployé
- ✅ Variables d'environnement correctes
- ✅ App accessible via URL Vercel

**Labels :** `infra`, `frontend`, `vercel`, `prod`, `p0-critical`

---

#### INFRA-PROD-007 : Configurer DNS pour frontend
**Description :** Pointer votredomaine.com et www vers Vercel

**Tâches :**
- [ ] Dans panel DNS OVH, créer :
  - Enregistrement A : `@` → `76.76.21.21` (Vercel IP)
  - Enregistrement CNAME : `www` → `cname.vercel-dns.com`
- [ ] Ajouter domaine custom dans Vercel dashboard
- [ ] Configurer redirection www → apex (ou inverse)
- [ ] Vérifier SSL automatique activé
- [ ] Tester `https://votredomaine.com`

**Critères d'acceptation :**
- ✅ DNS configuré correctement
- ✅ SSL actif sur les deux domaines
- ✅ Frontend accessible via domaine custom

**Labels :** `infra`, `dns`, `frontend`, `prod`, `p0-critical`

---

#### INFRA-PROD-008 : Configurer monitoring et alertes
**Description :** Setup monitoring pour détecter problèmes en production

**Tâches :**
- [ ] Créer compte Sentry (free tier)
- [ ] Intégrer Sentry SDK dans backend FastAPI
- [ ] Intégrer Sentry SDK dans frontend Next.js
- [ ] Configurer alertes email pour erreurs critiques
- [ ] Tester capture d'erreurs
- [ ] Configurer Uptime monitoring (UptimeRobot free)

**Critères d'acceptation :**
- ✅ Erreurs remontées dans Sentry
- ✅ Alertes email fonctionnelles
- ✅ Uptime monitoring actif

**Labels :** `infra`, `monitoring`, `sentry`, `prod`, `p1-high`

---

#### INFRA-PROD-009 : Tests de charge production
**Description :** Valider la performance sous charge réelle

**Tâches :**
- [ ] Créer script de test de charge (Locust ou k6)
- [ ] Simuler 10-50 utilisateurs simultanés
- [ ] Mesurer temps de réponse API
- [ ] Mesurer temps génération vidéo
- [ ] Identifier bottlenecks
- [ ] Documenter résultats et limites

**Critères d'acceptation :**
- ✅ Tests de charge exécutés
- ✅ Métriques documentées
- ✅ Pas d'erreurs sous charge normale

**Labels :** `testing`, `performance`, `prod`, `p2-medium`

---

#### INFRA-PROD-010 : Documentation production
**Description :** Documenter l'infrastructure production complète

**Tâches :**
- [ ] Créer `docs/production_setup.md`
- [ ] Documenter toutes les URLs (frontend, backend, DB)
- [ ] Documenter credentials et où les trouver
- [ ] Créer runbook pour incidents courants
- [ ] Documenter procédure de rollback
- [ ] Créer guide de mise à jour production

**Critères d'acceptation :**
- ✅ Documentation complète et à jour
- ✅ Quelqu'un d'autre peut déployer en suivant la doc

**Labels :** `documentation`, `prod`, `p1-high`

---

## 📋 COLONNE : REVIEW

_(Tâches en cours de validation)_

---

## 📋 COLONNE : DONE

_(Tâches terminées et validées)_

---

## 🏷️ Labels Trello recommandés

**Par domaine :**
- `frontend` - Tâches frontend Next.js
- `backend` - Tâches backend FastAPI
- `database` - Tâches base de données
- `infra` - Tâches infrastructure
- `video` - Traitement vidéo FFmpeg
- `api` - Endpoints API
- `ui` - Interface utilisateur
- `testing` - Tests

**Par environnement :**
- `local` - Développement local
- `dev` - Environnement dev
- `prod` - Production

**Par priorité :**
- `p0-critical` - Bloquant, doit être fait en premier
- `p1-high` - Haute priorité
- `p2-medium` - Priorité moyenne
- `p3-low` - Peut attendre

**Par phase :**
- `phase-0` - Setup environnement
- `phase-1` - MVP local
- `phase-2` - Infrastructure dev
- `phase-3` - Infrastructure prod

---

## 📊 Estimation de temps

### Phase 0 : Configuration (2-3 jours)
- Setup environnement : 1 jour
- Configuration Git et tooling : 0.5 jour

### Phase 1 : MVP Local (2-3 semaines)
- Backend : 1 semaine
- Frontend : 1 semaine
- Tests et optimisation : 0.5 semaine

### Phase 2 : Infrastructure Dev (1 semaine)
- Setup Supabase : 1 jour
- Migration données : 1 jour
- Déploiement Railway/Vercel : 2 jours
- Tests intégration : 1 jour

### Phase 3 : Infrastructure Prod (1 semaine)
- Setup infrastructure prod : 2 jours
- Configuration DNS : 1 jour
- Migration données prod : 1 jour
- Monitoring et tests : 2 jours
- Documentation : 1 jour

**TOTAL : 5-7 semaines** pour un MVP production-ready

---

## 🎯 Jalons clés

1. **MVP Local Ready** : Génération vidéo fonctionne en local
2. **Dev Environment Ready** : Stack complète déployée sur dev
3. **Production Launch** : Application accessible publiquement
4. **Production Stable** : Monitoring actif, documentation complète

---

## 💡 Notes importantes

- Commencer par **Phase 0 et 1** pour valider le concept
- Ne pas passer à **Phase 2** avant d'avoir un MVP local fonctionnel
- **Phase 3** peut être faite rapidement une fois Phase 2 validée (même infrastructure)
- Prévoir budget : ~35-50€/mois en production (Supabase Pro + Railway Hobby)

---

## 🔄 Process de travail recommandé

1. **Créer une carte Trello** pour chaque tâche
2. **Assigner des labels** appropriés
3. **Estimer le temps** nécessaire (S/M/L/XL)
4. **Déplacer dans "En cours"** quand vous commencez
5. **Créer une branche Git** : `
