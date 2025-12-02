"""
Service de traitement vidéo optimisé avec concaténation progressive
Implémente la Phase 2 du plan d'optimisation vidéo

Optimisations principales:
- Concaténation progressive par chunks (au lieu de tout d'un coup)
- Stream copy intelligent (détection du format source)
- Cache des breaks pré-générés par durée
- Nettoyage progressif des fichiers temporaires
- Téléchargement parallèle des vidéos Supabase
"""

import logging
import subprocess
import json
import tempfile
import os
import shutil
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..models.exercise import Exercise
from ..models.config import WorkoutConfig
from .video_service import VideoService

# Configuration du logger
logger = logging.getLogger(__name__)


@dataclass
class VideoFormat:
    """Informations sur le format d'une vidéo"""

    codec: str
    width: int
    height: int
    fps: float
    bitrate: Optional[int] = None

    @property
    def is_target_format(self) -> bool:
        """Vérifie si la vidéo est déjà au format cible (720p H.264)"""
        return (
            self.codec.lower() in ("h264", "libx264", "avc1")
            and self.width == 1280
            and self.height == 720
            and abs(self.fps - 30.0) < 1.0  # Tolérance de 1 fps
        )


class OptimizedVideoService(VideoService):
    """
    Service vidéo optimisé avec concaténation progressive

    Hérite de VideoService pour la compatibilité et ajoute:
    - Concaténation progressive par chunks
    - Détection automatique du format source
    - Cache intelligent des breaks par durée
    - Nettoyage progressif de la mémoire
    """

    # Durées de break communes à pré-générer
    COMMON_BREAK_DURATIONS = [5, 10, 15, 20, 25, 30, 35, 40]

    # Format cible pour la normalisation
    TARGET_FORMAT = {
        "width": 1280,
        "height": 720,
        "fps": 30,
        "codec": "libx264",
        "preset": "ultrafast",
        "crf": 23,
    }

    def __init__(
        self,
        project_root: Path,
        base_video_path: Optional[Path] = None,
        video_cache_dir: Optional[Path] = None,
        max_parallel_downloads: int = 4,
    ):
        """
        Initialise le service vidéo optimisé

        Args:
            project_root: Racine du projet
            base_video_path: Chemin de base pour les vidéos locales
            video_cache_dir: Dossier de cache pour les vidéos Supabase
            max_parallel_downloads: Nombre max de téléchargements parallèles
        """
        super().__init__(project_root, base_video_path, video_cache_dir)

        self.max_parallel_downloads = max_parallel_downloads

        # Cache des breaks pré-générés par durée
        self.break_cache_dir = self.video_cache_dir / "breaks_cache"
        self.break_cache_dir.mkdir(parents=True, exist_ok=True)

        # Pré-générer les breaks pour les durées communes
        self._ensure_break_cache()

        logger.info(
            f"OptimizedVideoService initialisé avec "
            f"max_parallel_downloads={max_parallel_downloads}, "
            f"break_cache_dir={self.break_cache_dir}"
        )

    def _ensure_break_cache(self) -> None:
        """
        Pré-génère les vidéos de break pour toutes les durées communes
        Utilise un cache persistant pour éviter la régénération
        Vérifie que les breaks sont au bon format (720p)
        """
        logger.info("=== INITIALISATION CACHE DES BREAKS ===")

        for duration in self.COMMON_BREAK_DURATIONS:
            break_path = self._get_cached_break_path(duration)

            needs_regeneration = False

            if break_path.exists():
                # Vérifier que le break est au bon format (720p)
                video_format = self.detect_video_format(break_path)
                if video_format:
                    if (
                        video_format.width == self.TARGET_FORMAT["width"]
                        and video_format.height == self.TARGET_FORMAT["height"]
                    ):
                        file_size = break_path.stat().st_size
                        logger.info(
                            f"✓ Break {duration}s en cache (720p): {file_size/1024:.1f}KB"
                        )
                    else:
                        logger.warning(
                            f"⚠️ Break {duration}s au mauvais format "
                            f"({video_format.width}x{video_format.height}), régénération..."
                        )
                        break_path.unlink()  # Supprimer l'ancien break
                        needs_regeneration = True
                else:
                    logger.warning(
                        f"⚠️ Impossible de vérifier le format du break {duration}s, régénération..."
                    )
                    break_path.unlink()
                    needs_regeneration = True
            else:
                needs_regeneration = True

            if needs_regeneration:
                logger.info(f"⏳ Génération break {duration}s @ 720p...")
                start_time = time.time()

                if self.generate_break_video(duration, break_path):
                    generation_time = (time.time() - start_time) * 1000
                    file_size = break_path.stat().st_size
                    logger.info(
                        f"✓ Break {duration}s généré en {generation_time:.0f}ms "
                        f"({file_size/1024:.1f}KB) @ 720p"
                    )
                else:
                    logger.error(f"✗ Échec génération break {duration}s")

    def _get_cached_break_path(self, duration: int) -> Path:
        """Retourne le chemin du break en cache pour une durée donnée"""
        return self.break_cache_dir / f"break_{duration}s.mp4"

    def _get_or_create_break(self, duration: int, temp_dir: Path) -> Optional[Path]:
        """
        Obtient une vidéo de break, depuis le cache ou en la générant

        Args:
            duration: Durée du break en secondes
            temp_dir: Répertoire temporaire pour les breaks non-standards

        Returns:
            Chemin vers la vidéo de break ou None si erreur
        """
        # Vérifier d'abord le cache des durées communes
        cached_path = self._get_cached_break_path(duration)
        if cached_path.exists():
            logger.debug(f"Break {duration}s trouvé en cache")
            return cached_path

        # Si pas en cache, générer dans le répertoire temporaire
        logger.info(f"Break {duration}s non en cache, génération...")
        temp_break_path = temp_dir / f"break_{duration}s_{os.getpid()}.mp4"

        if self.generate_break_video(duration, temp_break_path):
            return temp_break_path

        return None

    def generate_break_video(self, duration: int, output_path: Path) -> bool:
        """
        Génère une vidéo de break (pause) à la résolution cible 720p.

        Override de la méthode parente pour générer les breaks à la même
        résolution que les vidéos d'exercices (1280x720) au lieu de 1920x1080.

        Args:
            duration: Durée de la pause en secondes
            output_path: Chemin du fichier de sortie

        Returns:
            True si succès, False sinon
        """
        total_start = time.time()

        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            logger.error("FFmpeg introuvable dans le PATH")
            return False

        # Rechercher l'image sport_room.png
        possible_paths = [
            Path("/app/sport_room.png"),  # Railway: racine app
            Path("/app/backend/sport_room.png"),  # Railway: dossier backend
            self.project_root / "sport_room.png",  # Chemin normal
            self.project_root / "backend" / "sport_room.png",  # Backend subfolder
            Path(__file__).parent.parent.parent.parent
            / "sport_room.png",  # Remontée explicite
        ]

        sport_room_image = None
        for path in possible_paths:
            if path.exists():
                sport_room_image = path
                break

        if sport_room_image is None:
            logger.error(
                f"Image sport_room.png introuvable dans: {[str(p) for p in possible_paths]}"
            )
            return False

        # Générer le break à la résolution cible (720p) pour correspondre aux exercices
        command = [
            ffmpeg_path,
            "-loop",
            "1",  # Boucler l'image
            "-i",
            str(sport_room_image),  # Image source
            "-t",
            str(duration),  # Durée en secondes
            "-vf",
            f"scale={self.TARGET_FORMAT['width']}:{self.TARGET_FORMAT['height']}",  # 1280x720
            "-c:v",
            self.TARGET_FORMAT["codec"],  # libx264
            "-preset",
            self.TARGET_FORMAT["preset"],  # ultrafast
            "-r",
            str(self.TARGET_FORMAT["fps"]),  # 30 fps
            "-pix_fmt",
            "yuv420p",
            "-an",  # Pas d'audio
            "-y",
            str(output_path),
        ]

        try:
            logger.debug(f"Génération vidéo break 720p: {' '.join(command)}")
            subprocess.run(command, check=True, capture_output=True, text=True)

            total_time = (time.time() - total_start) * 1000
            output_size = output_path.stat().st_size if output_path.exists() else 0
            logger.info(
                f"Break {duration}s généré en {total_time:.0f}ms ({output_size/1024:.1f}KB) @ 720p"
            )

            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Erreur génération break: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Erreur inattendue génération break: {e}")
            return False

    def detect_video_format(self, video_path: Path) -> Optional[VideoFormat]:
        """
        Analyse le format d'une vidéo avec ffprobe

        Args:
            video_path: Chemin de la vidéo à analyser

        Returns:
            VideoFormat avec les informations ou None si erreur
        """
        try:
            command = [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_streams",
                "-select_streams",
                "v:0",  # Premier flux vidéo uniquement
                str(video_path),
            ]

            result = subprocess.run(
                command, capture_output=True, text=True, check=True, timeout=10
            )

            data = json.loads(result.stdout)

            if not data.get("streams"):
                logger.warning(f"Aucun flux vidéo trouvé dans {video_path}")
                return None

            stream = data["streams"][0]

            # Extraire le FPS (peut être une fraction comme "30/1")
            fps_str = stream.get("r_frame_rate", "30/1")
            if "/" in fps_str:
                num, den = fps_str.split("/")
                fps = float(num) / float(den) if float(den) != 0 else 30.0
            else:
                fps = float(fps_str)

            video_format = VideoFormat(
                codec=stream.get("codec_name", "unknown"),
                width=int(stream.get("width", 0)),
                height=int(stream.get("height", 0)),
                fps=fps,
                bitrate=int(stream.get("bit_rate", 0))
                if stream.get("bit_rate")
                else None,
            )

            logger.debug(
                f"Format détecté pour {video_path.name}: "
                f"{video_format.codec} {video_format.width}x{video_format.height} @ {video_format.fps}fps"
            )

            return video_format

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout lors de l'analyse de {video_path}")
            return None
        except subprocess.CalledProcessError as e:
            logger.error(f"Erreur ffprobe pour {video_path}: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'analyse de {video_path}: {e}")
            return None

    def _concat_two_videos(
        self, video1: Path, video2: Path, output: Path, use_stream_copy: bool = False
    ) -> bool:
        """
        Concatène deux vidéos en une seule

        Args:
            video1: Première vidéo
            video2: Deuxième vidéo
            output: Fichier de sortie
            use_stream_copy: Si True, utilise -c copy (plus rapide mais formats doivent être identiques)

        Returns:
            True si succès, False sinon
        """
        temp_dir = Path(tempfile.gettempdir())
        concat_file = temp_dir / f"concat_{os.getpid()}_{time.time_ns()}.txt"

        try:
            # Créer le fichier de concaténation
            with open(concat_file, "w") as f:
                f.write(f"file '{video1.absolute()}'\n")
                f.write(f"file '{video2.absolute()}'\n")

            # Trouver ffmpeg
            ffmpeg_path = shutil.which("ffmpeg")
            if not ffmpeg_path:
                logger.error("FFmpeg introuvable")
                return False

            if use_stream_copy:
                # Mode stream copy - très rapide mais requiert formats identiques
                command = [
                    ffmpeg_path,
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(concat_file),
                    "-c",
                    "copy",  # Stream copy - pas de ré-encodage
                    "-y",
                    str(output),
                ]
            else:
                # Mode ré-encodage - plus lent mais gère tous les formats
                command = [
                    ffmpeg_path,
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(concat_file),
                    "-c:v",
                    self.TARGET_FORMAT["codec"],
                    "-preset",
                    self.TARGET_FORMAT["preset"],
                    "-crf",
                    str(self.TARGET_FORMAT["crf"]),
                    "-vf",
                    f"scale={self.TARGET_FORMAT['width']}:{self.TARGET_FORMAT['height']}",
                    "-r",
                    str(self.TARGET_FORMAT["fps"]),
                    "-pix_fmt",
                    "yuv420p",
                    "-an",  # Pas d'audio
                    "-y",
                    str(output),
                ]

            logger.debug(f"Commande concat: {' '.join(command)}")

            subprocess.run(command, capture_output=True, text=True, check=True)

            return output.exists()

        except subprocess.CalledProcessError as e:
            logger.error(f"Erreur FFmpeg concat: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Erreur inattendue concat: {e}")
            return False
        finally:
            # Nettoyage du fichier concat temporaire
            if concat_file.exists():
                concat_file.unlink()

    def _normalize_video(self, input_path: Path, output_path: Path) -> bool:
        """
        Normalise une vidéo au format cible (720p H.264 30fps)

        Args:
            input_path: Vidéo source
            output_path: Vidéo normalisée

        Returns:
            True si succès, False sinon
        """
        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            logger.error("FFmpeg introuvable")
            return False

        command = [
            ffmpeg_path,
            "-i",
            str(input_path),
            "-c:v",
            self.TARGET_FORMAT["codec"],
            "-preset",
            self.TARGET_FORMAT["preset"],
            "-crf",
            str(self.TARGET_FORMAT["crf"]),
            "-vf",
            f"scale={self.TARGET_FORMAT['width']}:{self.TARGET_FORMAT['height']}",
            "-r",
            str(self.TARGET_FORMAT["fps"]),
            "-pix_fmt",
            "yuv420p",
            "-an",
            "-y",
            str(output_path),
        ]

        try:
            subprocess.run(command, capture_output=True, text=True, check=True)
            return output_path.exists()
        except subprocess.CalledProcessError as e:
            logger.error(f"Erreur normalisation vidéo: {e.stderr}")
            return False

    def _download_videos_parallel(
        self, exercises: List[Exercise]
    ) -> Dict[str, Optional[Path]]:
        """
        Télécharge les vidéos des exercices en parallèle

        Args:
            exercises: Liste des exercices

        Returns:
            Dict mapping nom exercice -> chemin local
        """
        logger.info(
            f"=== DÉBUT TÉLÉCHARGEMENT PARALLÈLE: {len(exercises)} exercices ({self.max_parallel_downloads} threads) ==="
        )
        start_time = time.time()

        results = {}

        def download_single(exercise: Exercise) -> Tuple[str, Optional[Path]]:
            """Télécharge une seule vidéo"""
            download_start = time.time()
            logger.info(f"⏱️ Début résolution: {exercise.name}")
            path = self._resolve_video_path(exercise)
            download_time = (time.time() - download_start) * 1000
            logger.info(f"⏱️ Fin résolution: {exercise.name} en {download_time:.0f}ms")
            return (exercise.name, path)

        with ThreadPoolExecutor(max_workers=self.max_parallel_downloads) as executor:
            futures = {executor.submit(download_single, ex): ex for ex in exercises}

            completed_count = 0
            for future in as_completed(futures):
                exercise = futures[future]
                try:
                    name, path = future.result()
                    results[name] = path
                    completed_count += 1

                    if path and path.exists():
                        size_kb = path.stat().st_size / 1024
                        logger.info(
                            f"✓ [{completed_count}/{len(exercises)}] {name}: {size_kb:.1f}KB"
                        )
                    else:
                        logger.error(
                            f"✗ [{completed_count}/{len(exercises)}] {name}: téléchargement échoué"
                        )

                except Exception as e:
                    logger.error(f"✗ {exercise.name}: erreur - {e}")
                    results[exercise.name] = None

        total_time = (time.time() - start_time) * 1000
        success_count = sum(1 for p in results.values() if p is not None)
        logger.info(
            f"⏱️ TÉLÉCHARGEMENT PARALLÈLE TERMINÉ: {success_count}/{len(exercises)} "
            f"en {total_time:.0f}ms ({total_time/1000:.1f}s)"
        )

        return results

    def build_progressive_concat(
        self,
        video_paths: List[Path],
        break_paths: List[Optional[Path]],
        output_path: Path,
        cleanup_intermediates: bool = True,
    ) -> bool:
        """
        Construit la vidéo finale par concaténation progressive

        Logique:
        temp_0 = video_1
        temp_1 = concat(temp_0, break_1)
        temp_2 = concat(temp_1, video_2)
        temp_3 = concat(temp_2, break_2)
        ...

        Args:
            video_paths: Liste des chemins des vidéos d'exercices
            break_paths: Liste des chemins des breaks (peut contenir None pour dernier ex)
            output_path: Chemin du fichier final
            cleanup_intermediates: Si True, supprime les fichiers intermédiaires

        Returns:
            True si succès, False sinon
        """
        if not video_paths:
            logger.error("Aucune vidéo à concaténer")
            return False

        logger.info(f"=== CONCATÉNATION PROGRESSIVE ({len(video_paths)} exercices) ===")
        total_start = time.time()

        temp_dir = Path(tempfile.gettempdir())

        # Analyser les formats pour déterminer si on peut utiliser stream copy
        logger.info("Analyse des formats vidéo...")
        all_same_format = True
        reference_format = None

        for i, video_path in enumerate(video_paths):
            video_format = self.detect_video_format(video_path)
            if video_format:
                if reference_format is None:
                    reference_format = video_format
                elif (
                    video_format.codec != reference_format.codec
                    or video_format.width != reference_format.width
                    or video_format.height != reference_format.height
                ):
                    all_same_format = False
                    logger.info(f"Format différent détecté pour vidéo {i+1}")
                    break

        # Si un seul exercice, juste copier/normaliser
        if len(video_paths) == 1:
            logger.info("Un seul exercice, copie directe")
            if reference_format and reference_format.is_target_format:
                shutil.copy2(video_paths[0], output_path)
            else:
                self._normalize_video(video_paths[0], output_path)
            return output_path.exists()

        # Décider du mode de concaténation
        use_stream_copy = (
            all_same_format and reference_format and reference_format.is_target_format
        )

        if use_stream_copy:
            logger.info("✓ Stream copy activé - tous les fichiers sont au format cible")
        else:
            logger.info("⚠ Ré-encodage nécessaire - formats hétérogènes")

        # Normaliser la première vidéo si nécessaire
        current_temp = temp_dir / f"progressive_0_{os.getpid()}.mp4"

        if use_stream_copy:
            shutil.copy2(video_paths[0], current_temp)
        else:
            logger.info(f"Normalisation vidéo 1/{len(video_paths)}...")
            if not self._normalize_video(video_paths[0], current_temp):
                logger.error("Échec normalisation première vidéo")
                return False

        step_times = []
        previous_temp = None

        # Concaténation progressive
        for i in range(len(video_paths)):
            step_start = time.time()

            # Si pas la première vidéo, concaténer avec le résultat précédent
            if i > 0:
                # Normaliser la vidéo si nécessaire
                if use_stream_copy:
                    video_to_add = video_paths[i]
                else:
                    normalized_video = temp_dir / f"normalized_{i}_{os.getpid()}.mp4"
                    logger.info(f"Normalisation vidéo {i+1}/{len(video_paths)}...")
                    if not self._normalize_video(video_paths[i], normalized_video):
                        logger.error(f"Échec normalisation vidéo {i+1}")
                        return False
                    video_to_add = normalized_video

                # Concaténer
                next_temp = temp_dir / f"progressive_{i*2}_{os.getpid()}.mp4"
                logger.info(f"Concat vidéo {i+1}...")

                if not self._concat_two_videos(
                    current_temp,
                    video_to_add,
                    next_temp,
                    use_stream_copy=use_stream_copy,
                ):
                    logger.error(f"Échec concat vidéo {i+1}")
                    return False

                # Nettoyage
                if cleanup_intermediates:
                    if previous_temp and previous_temp.exists():
                        previous_temp.unlink()
                    if not use_stream_copy and normalized_video.exists():
                        normalized_video.unlink()

                previous_temp = current_temp
                current_temp = next_temp

            # Ajouter le break si ce n'est pas le dernier exercice
            if i < len(video_paths) - 1 and break_paths[i] is not None:
                break_path = break_paths[i]

                next_temp = temp_dir / f"progressive_{i*2+1}_{os.getpid()}.mp4"
                logger.info(f"Concat break {i+1}...")

                if not self._concat_two_videos(
                    current_temp, break_path, next_temp, use_stream_copy=use_stream_copy
                ):
                    logger.error(f"Échec concat break {i+1}")
                    return False

                # Nettoyage
                if cleanup_intermediates and previous_temp and previous_temp.exists():
                    previous_temp.unlink()

                previous_temp = current_temp
                current_temp = next_temp

            step_time = (time.time() - step_start) * 1000
            step_times.append(step_time)
            logger.info(f"⏱️ Étape {i+1} terminée en {step_time:.0f}ms")

        # Déplacer le résultat final
        shutil.move(current_temp, output_path)

        # Nettoyage final
        if cleanup_intermediates and previous_temp and previous_temp.exists():
            previous_temp.unlink()

        total_time = (time.time() - total_start) * 1000
        avg_step_time = sum(step_times) / len(step_times) if step_times else 0

        logger.info("=== RÉSUMÉ CONCATÉNATION PROGRESSIVE ===")
        logger.info(f"⏱️ Temps total: {total_time:.0f}ms")
        logger.info(f"⏱️ Temps moyen par étape: {avg_step_time:.0f}ms")
        logger.info(
            f"📦 Fichier final: {output_path.stat().st_size / (1024*1024):.2f}MB"
        )

        return output_path.exists()

    def generate_workout_video_progressive(
        self,
        exercises: List[Exercise],
        config: WorkoutConfig,
        output_path: Path,
    ) -> bool:
        """
        Génère une vidéo d'entraînement avec concaténation progressive

        Cette méthode optimisée:
        1. Télécharge les vidéos en parallèle
        2. Utilise un cache de breaks pré-générés
        3. Concatène progressivement pour limiter la mémoire
        4. Nettoie les fichiers temporaires au fur et à mesure

        Args:
            exercises: Liste des exercices
            config: Configuration de l'entraînement
            output_path: Chemin du fichier de sortie

        Returns:
            True si succès, False sinon
        """
        logger.info("=" * 60)
        logger.info("=== GÉNÉRATION VIDÉO OPTIMISÉE (PROGRESSIVE) ===")
        logger.info(f"Exercices: {len(exercises)}")
        logger.info(f"Intensité: {config.intensity}")
        logger.info(f"Sortie: {output_path}")
        logger.info("=" * 60)

        total_start = time.time()

        try:
            # Récupérer les durées work/rest
            rest_time = config.intervals.get("rest_time", 20)
            logger.info(f"Durée des breaks: {rest_time}s")

            temp_dir = Path(tempfile.gettempdir())

            # Étape 1: Téléchargement parallèle des vidéos
            download_start = time.time()
            video_map = self._download_videos_parallel(exercises)
            download_time = (time.time() - download_start) * 1000

            # Vérifier que toutes les vidéos sont disponibles
            video_paths = []
            for exercise in exercises:
                path = video_map.get(exercise.name)
                if path and path.exists():
                    video_paths.append(path)
                else:
                    logger.error(f"Vidéo manquante pour {exercise.name}")
                    return False

            logger.info(f"⏱️ Téléchargement: {download_time:.0f}ms")

            # Étape 2: Préparer les breaks (depuis le cache)
            break_start = time.time()
            break_paths = []

            for i in range(len(exercises) - 1):
                break_path = self._get_or_create_break(rest_time, temp_dir)
                break_paths.append(break_path)

            # Ajouter None pour le dernier exercice (pas de break après)
            break_paths.append(None)

            break_time = (time.time() - break_start) * 1000
            logger.info(f"⏱️ Préparation breaks: {break_time:.0f}ms")

            # Étape 3: Concaténation progressive
            concat_start = time.time()
            success = self.build_progressive_concat(
                video_paths, break_paths, output_path, cleanup_intermediates=True
            )
            concat_time = (time.time() - concat_start) * 1000

            logger.info(f"⏱️ Concaténation: {concat_time:.0f}ms")

            # Résumé final
            total_time = (time.time() - total_start) * 1000

            logger.info("=" * 60)
            logger.info("=== RÉSUMÉ GÉNÉRATION OPTIMISÉE ===")
            logger.info(
                f"⏱️ Téléchargement: {download_time:.0f}ms ({download_time/total_time*100:.1f}%)"
            )
            logger.info(
                f"⏱️ Préparation breaks: {break_time:.0f}ms ({break_time/total_time*100:.1f}%)"
            )
            logger.info(
                f"⏱️ Concaténation: {concat_time:.0f}ms ({concat_time/total_time*100:.1f}%)"
            )
            logger.info(f"⏱️ TOTAL: {total_time:.0f}ms ({total_time/1000:.1f}s)")

            if success and output_path.exists():
                file_size = output_path.stat().st_size
                logger.info(f"📦 Fichier final: {file_size / (1024*1024):.2f}MB")
                logger.info("=" * 60)
                return True
            else:
                logger.error("Échec de la génération")
                return False

        except Exception as e:
            logger.error(f"Erreur lors de la génération optimisée: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return False

    def generate_workout_video(
        self,
        exercises: List[Exercise],
        config: WorkoutConfig,
        output_path: Path,
    ) -> bool:
        """
        Génère une vidéo d'entraînement avec fallback automatique

        Essaie d'abord la méthode optimisée, puis fallback sur l'ancienne
        méthode en cas d'erreur.

        Args:
            exercises: Liste des exercices
            config: Configuration de l'entraînement
            output_path: Chemin du fichier de sortie

        Returns:
            True si succès, False sinon
        """
        logger.info("Génération vidéo avec OptimizedVideoService...")

        try:
            # Essayer la méthode optimisée
            success = self.generate_workout_video_progressive(
                exercises, config, output_path
            )

            if success:
                logger.info("✓ Génération optimisée réussie")
                return True
            else:
                logger.warning("Génération optimisée échouée, fallback...")

        except Exception as e:
            logger.error(f"Erreur génération optimisée: {e}")
            logger.warning("Fallback sur méthode classique...")

        # Fallback sur la méthode classique
        logger.info("=== FALLBACK: Méthode classique ===")
        return super().generate_workout_video(exercises, config, output_path)

    def cleanup_cache(self, max_age_hours: int = 24) -> int:
        """
        Nettoie les fichiers du cache plus vieux que max_age_hours

        Args:
            max_age_hours: Âge maximum des fichiers en heures

        Returns:
            Nombre de fichiers supprimés
        """
        import time

        deleted_count = 0
        max_age_seconds = max_age_hours * 3600
        current_time = time.time()

        for cache_file in self.video_cache_dir.glob("*"):
            if cache_file.is_file():
                # Ne pas supprimer les breaks pré-générés
                if cache_file.parent == self.break_cache_dir:
                    continue

                file_age = current_time - cache_file.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        cache_file.unlink()
                        deleted_count += 1
                        logger.debug(f"Cache supprimé: {cache_file}")
                    except Exception as e:
                        logger.warning(f"Impossible de supprimer {cache_file}: {e}")

        logger.info(f"Cache nettoyé: {deleted_count} fichiers supprimés")
        return deleted_count

    def get_cache_stats(self) -> Dict:
        """
        Retourne des statistiques sur le cache

        Returns:
            Dict avec les statistiques du cache
        """
        video_count = 0
        video_size = 0
        break_count = 0
        break_size = 0

        for cache_file in self.video_cache_dir.glob("*"):
            if cache_file.is_file():
                size = cache_file.stat().st_size
                if cache_file.parent == self.break_cache_dir:
                    break_count += 1
                    break_size += size
                else:
                    video_count += 1
                    video_size += size

        return {
            "video_cache": {
                "count": video_count,
                "size_mb": video_size / (1024 * 1024),
            },
            "break_cache": {
                "count": break_count,
                "size_mb": break_size / (1024 * 1024),
                "durations": self.COMMON_BREAK_DURATIONS,
            },
            "cache_dir": str(self.video_cache_dir),
            "break_cache_dir": str(self.break_cache_dir),
        }
