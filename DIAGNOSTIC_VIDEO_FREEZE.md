# 🔍 Guide de Diagnostic - Vidéos Figées

Ce guide vous aide à diagnostiquer et résoudre les problèmes de vidéos qui freeze pendant la lecture.

## 🎯 Problème Identifié

**Cause principale**: Le gestionnaire d'événement `onWaiting` ne faisait rien, donc l'utilisateur ne voyait aucune indication visuelle pendant le buffering de la vidéo.

## ✅ Corrections Apportées

### 1. Indicateur de Buffering Visuel ✨

Ajout d'un spinner qui s'affiche quand la vidéo bufferise :
- Un loader circulaire apparaît au centre de la vidéo
- L'utilisateur sait maintenant que la vidéo charge et n'est pas bloquée

### 2. Gestionnaires d'Événements Vidéo Complets 📊

Ajout de tous les événements manquants :

| Événement | Description | Action |
|-----------|-------------|--------|
| `onWaiting` | Vidéo attend des données | Affiche l'indicateur de buffering + log |
| `onPlaying` | Vidéo reprend la lecture | Cache l'indicateur + mesure durée buffering |
| `onStalled` | Navigateur ne reçoit pas de données | Affiche l'indicateur + log d'alerte |
| `onSuspend` | Navigateur suspend le chargement | Log d'information |
| `onError` | Erreur de lecture | Log détaillé avec code d'erreur |
| `onProgress` | Progression du buffering | Log du pourcentage bufferisé |

### 3. Logging Détaillé 🔎

Tous les événements vidéo sont maintenant loggés dans la console :
```
[VideoPlayer] 🔄 WAITING - Video is buffering
[VideoPlayer] ▶️ PLAYING - Video is playing
[VideoPlayer] ✅ Buffering ended after 1234ms
[VideoPlayer] 📊 PROGRESS - Buffered: 45.2% (120.5s / 266.0s)
```

## 🛠️ Comment Diagnostiquer

### Étape 1 : Vérifier les Logs du Navigateur

1. Ouvrez la console développeur (F12)
2. Lancez une vidéo d'entraînement
3. Observez les logs `[VideoPlayer]`

**Si vous voyez des `WAITING` répétés** :
- Le backend envoie les données trop lentement
- La vidéo est trop lourde pour votre connexion
- FFmpeg prend du temps à encoder certains segments

**Si vous voyez des `STALLED`** :
- Le backend ne répond plus
- FFmpeg a planté ou est bloqué
- Problème réseau

**Si vous voyez des `VIDEO ERROR`** :
- Format vidéo incompatible
- Corruption de données
- Problème de codec

### Étape 2 : Analyser les Vidéos Sources

Utilisez le script de diagnostic pour vérifier la qualité des vidéos :

```bash
# Analyser toutes les vidéos téléchargées
python backend/scripts/diagnose_video_issues.py --check-sources

# Analyser un répertoire spécifique
python backend/scripts/diagnose_video_issues.py --video-dir /path/to/videos

# Analyser des vidéos spécifiques
python backend/scripts/diagnose_video_issues.py video1.mp4 video2.mp4
```

**Le script détecte** :
- ❌ Résolutions différentes entre les vidéos
- ❌ FPS (framerate) différents
- ❌ Codecs incompatibles
- ❌ Formats de pixels différents
- ❌ Absence de keyframes au début des vidéos
- ❌ Intervals trop grands entre les keyframes

### Étape 3 : Vérifier les Logs Backend

```bash
# Logs en temps réel
tail -f backend/logs/logs_backend.log

# Rechercher les erreurs
grep -i "error\|warning\|failed" backend/logs/logs_backend.log
```

Cherchez :
- Timeouts FFmpeg
- Erreurs de téléchargement Supabase
- Erreurs de concaténation
- Warnings sur les segments

## 🔧 Solutions par Type de Problème

### Problème 1 : Buffering Fréquent (WAITING répétés)

**Symptômes** :
- L'indicateur de buffering apparaît souvent
- Logs montrent `WAITING` toutes les 10-30 secondes

**Causes Possibles** :
1. FFmpeg encode trop lentement (preset `ultrafast` pas assez rapide)
2. Vidéo trop lourde (bitrate trop élevé)
3. Réencodage complet au lieu de stream copy

**Solutions** :

#### Option A : Activer Stream Copy (si vidéos compatibles)
```python
# Dans backend/video_studio/generators/workout_video_generator.py ligne 167
# Changer:
use_stream_copy=False
# En:
use_stream_copy=True
```

⚠️ **Attention** : Cela ne fonctionne que si toutes les vidéos ont exactement le même format. Vérifiez d'abord avec le script de diagnostic.

#### Option B : Réduire le Bitrate
```python
# Dans backend/video_studio/core/ffmpeg_wrapper.py
# Ajouter un paramètre -b:v pour limiter le bitrate
command.extend(['-b:v', '2M'])  # 2 Mbps max
```

#### Option C : Pré-générer et Cacher les Vidéos de Break
Les overlays de break sont complexes (6 filtres). Pré-générez-les :

```python
# Créer un cache de breaks de différentes durées
BREAK_DURATIONS = [20, 30, 45, 60]  # secondes
for duration in BREAK_DURATIONS:
    generate_break_video(duration)
    cache_video(f"break_{duration}s.mp4")
```

### Problème 2 : Vidéo Bloquée Définitivement (STALLED)

**Symptômes** :
- Vidéo ne reprend jamais
- Logs montrent `STALLED` sans `PLAYING` après

**Causes Possibles** :
1. FFmpeg a planté
2. Problème de keyframes (vidéo ne peut pas être décodée)
3. Corruption de données

**Solutions** :

#### Vérifier les Keyframes
```bash
# Analyser les vidéos sources
python backend/scripts/diagnose_video_issues.py --check-sources
```

Si le script détecte `no_initial_keyframe`, normalisez les vidéos :

```bash
# Pour chaque vidéo source
ffmpeg -i input.mp4 \
  -c:v libx264 \
  -g 30 \           # Keyframe tous les 30 frames (1s à 30fps)
  -keyint_min 30 \  # Minimum keyframe interval
  -sc_threshold 0 \ # Désactiver détection automatique
  -pix_fmt yuv420p \
  -r 30 \
  output.mp4
```

#### Ajouter un Timeout Détection
```python
# Dans VideoPlayer.tsx, détecter les stallings trop longs
useEffect(() => {
  let stallTimeout: NodeJS.Timeout

  if (isBuffering) {
    stallTimeout = setTimeout(() => {
      console.error('[VideoPlayer] ⚠️ Buffering trop long (>10s), possible stalling')
      // Optionnel: proposer de recharger la vidéo
    }, 10000)
  }

  return () => clearTimeout(stallTimeout)
}, [isBuffering])
```

### Problème 3 : Erreurs de Lecture (VIDEO ERROR)

**Symptômes** :
- Logs montrent `VIDEO ERROR` avec un code
- Vidéo ne se charge pas du tout

**Codes d'Erreur HTML5** :
- `1` - MEDIA_ERR_ABORTED : Chargement abandonné
- `2` - MEDIA_ERR_NETWORK : Erreur réseau
- `3` - MEDIA_ERR_DECODE : Erreur de décodage (format incompatible)
- `4` - MEDIA_ERR_SRC_NOT_SUPPORTED : Format non supporté

**Solutions** :

#### Pour erreur 3 ou 4 (décodage/format)
Vérifiez la compatibilité des codecs :
```bash
# Vérifier le codec navigateur
# Dans la console navigateur:
const video = document.createElement('video')
console.log(video.canPlayType('video/mp4; codecs="avc1.42E01E"'))
// Doit retourner "probably" ou "maybe"
```

Normalisez toutes les vidéos au format H.264 baseline :
```bash
ffmpeg -i input.mp4 \
  -c:v libx264 \
  -profile:v baseline \
  -level 3.0 \
  -pix_fmt yuv420p \
  output.mp4
```

### Problème 4 : Freezes aux Transitions (entre exercices/breaks)

**Symptômes** :
- Vidéo freeze uniquement lors du passage d'un exercice à un break
- Logs normaux mais image figée 1-2 secondes

**Cause** :
Problème de synchronisation des timestamps lors de la concaténation

**Solution** :

#### Forcer la Régénération des Timestamps
```python
# Dans backend/app/api/workouts.py
# Modifier la commande FFmpeg pour ajouter -fflags +genpts
command = [
    "ffmpeg",
    "-fflags", "+genpts",  # Régénérer les timestamps
    "-f", "concat",
    "-safe", "0",
    "-i", concat_file,
    # ... reste de la commande
]
```

## 🎨 Améliorations Futures Recommandées

### 1. Adaptive Bitrate Streaming (ABR)

Générer plusieurs qualités de vidéo :
- 720p @ 2 Mbps (haute qualité)
- 480p @ 1 Mbps (qualité moyenne)
- 360p @ 500 Kbps (basse qualité)

Le player choisit automatiquement selon la bande passante.

### 2. Segmentation HLS/DASH

Au lieu d'un gros MP4, générer des segments de 2-10 secondes :
- Permet de streamer progressivement
- Réduit le temps de buffering initial
- Permet le seeking instantané

```bash
# Générer des segments HLS
ffmpeg -i input.mp4 \
  -c:v libx264 \
  -hls_time 6 \
  -hls_playlist_type vod \
  output.m3u8
```

### 3. Pre-rendering des Overlays

Au lieu d'appliquer les overlays en temps réel avec FFmpeg, pré-générez-les :
- Plus rapide (pas de filtrage en temps réel)
- Cache les breaks communs
- Réduit la charge CPU

### 4. Monitoring en Temps Réel

Ajouter des métriques :
- Durée moyenne de buffering par session
- Taux d'erreurs de lecture
- Temps de génération par vidéo
- Débit réseau effectif

## 📝 Checklist de Déploiement

Avant de déployer en production :

- [ ] Tester avec le script de diagnostic sur toutes les vidéos sources
- [ ] Vérifier que toutes les vidéos ont des keyframes réguliers
- [ ] Normaliser les vidéos au même format si nécessaire
- [ ] Tester sur différents navigateurs (Chrome, Firefox, Safari)
- [ ] Tester sur différentes connexions (4G, WiFi lent, fibre)
- [ ] Monitorer les logs pendant 1 semaine
- [ ] Analyser les durées de buffering moyennes
- [ ] Optimiser les segments qui prennent >5s à encoder

## 🆘 Support

Si le problème persiste après toutes ces vérifications :

1. Récupérez les logs complets :
```bash
# Logs frontend (console navigateur)
# Copier tous les logs [VideoPlayer]

# Logs backend
tail -n 500 backend/logs/logs_backend.log > debug.log
```

2. Exécutez le diagnostic :
```bash
python backend/scripts/diagnose_video_issues.py --check-sources > diagnostic.txt
```

3. Testez avec ffprobe sur une vidéo générée :
```bash
# Sauvegarder une vidéo générée
curl http://localhost:8080/api/stream-workout/WORKOUT_ID > test_workout.mp4

# Analyser
ffprobe -v error -show_format -show_streams test_workout.mp4
```

4. Partagez ces 3 fichiers pour analyse approfondie

---

**Résumé** : Les corrections apportées devraient résoudre la majorité des cas de "freeze" en rendant le buffering visible et en loggant tous les événements. Le script de diagnostic permet d'identifier les problèmes au niveau des vidéos sources.
