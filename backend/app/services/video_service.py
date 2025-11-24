"""
Service de traitement vidéo - Classe de base
Fournit les utilitaires de base pour la manipulation de vidéos
"""

import logging
import subprocess
from pathlib import Path
from typing import Dict, Optional
import hashlib
import requests
import shutil

from ..models.exercise import Exercise
from ..models.enums import Intensity

# Configuration du logger
logger = logging.getLogger(__name__)


class VideoService:
    """Service de base pour la manipulation de vidéos d'entraînement"""

    # Multiplicateurs de vitesse selon l'intensité
    SPEED_MULTIPLIERS = {
        Intensity.LOW_IMPACT: 0.8,  # 80% vitesse normale (plus lent)
        Intensity.MEDIUM_INTENSITY: 1.0,  # Vitesse normale
        Intensity.HIGH_INTENSITY: 1.2,  # 120% vitesse normale (plus rapide)
    }

    def __init__(
        self,
        project_root: Path,
        base_video_path: Optional[Path] = None,
        video_cache_dir: Optional[Path] = None,
    ):
        """
        Initialise le service vidéo

        Args:
            project_root: Racine du projet
            base_video_path: Chemin de base pour les vidéos locales (par défaut: exercices_generation/outputs/)
            video_cache_dir: Dossier de cache pour les vidéos Supabase (par défaut: /tmp/exercise_videos)
        """
        self.project_root = project_root
        if base_video_path is None:
            # Chemin par défaut vers les vidéos d'exercices
            self.base_video_path = self.project_root / "exercices_generation/outputs"
        else:
            self.base_video_path = project_root / base_video_path

        # Cache pour les vidéos téléchargées depuis Supabase
        if video_cache_dir is None:
            self.video_cache_dir = Path("/tmp/exercise_videos")
        else:
            self.video_cache_dir = video_cache_dir

        # Créer le dossier de cache s'il n'existe pas
        self.video_cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"VideoService initialisé avec project_root: {self.project_root}, "
            f"base_path: {self.base_video_path}, cache_dir: {self.video_cache_dir}"
        )

    def get_speed_multiplier(self, intensity: Intensity) -> float:
        """
        Obtient le multiplicateur de vitesse selon l'intensité

        Args:
            intensity: Niveau d'intensité de l'entraînement

        Returns:
            float: Multiplicateur de vitesse (0.8 = plus lent, 1.2 = plus rapide)
        """
        multiplier = 1  # self.SPEED_MULTIPLIERS.get(intensity, 1.0)
        logger.debug(f"Multiplicateur de vitesse pour {intensity}: {multiplier}")
        return multiplier

    def _trim_video(self, input_path: Path, output_path: Path, duration: int) -> bool:
        """
        Trimme une vidéo à une durée spécifique.

        Args:
            input_path: Chemin de la vidéo source
            output_path: Chemin de la vidéo de sortie
            duration: Durée maximale en secondes

        Returns:
            bool: True si succès, False sinon
        """
        try:
            ffmpeg_path = shutil.which("ffmpeg")
            if not ffmpeg_path:
                logger.error("FFmpeg introuvable")
                return False

            command = [
                ffmpeg_path,
                "-i",
                str(input_path),
                "-t",
                str(duration),  # Durée maximale
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-crf",
                "23",
                "-pix_fmt",
                "yuv420p",
                "-r",
                "30",
                "-an",  # Pas d'audio
                "-y",
                str(output_path),
            ]

            subprocess.run(command, capture_output=True, text=True, check=True)

            if output_path.exists():
                logger.debug(f"Vidéo trimée à {duration}s: {output_path}")
                return True
            return False

        except subprocess.CalledProcessError as e:
            logger.error(f"Erreur trim vidéo: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Erreur inattendue trim vidéo: {e}")
            return False

    def generate_break_video(self, duration: int, output_path: Path) -> bool:
        """
        Génère une vidéo statique de break avec l'image sport_room.png

        Args:
            duration: Durée du break en secondes
            output_path: Chemin de sortie de la vidéo

        Returns:
            bool: True si succès, False sinon
        """
        import time

        total_start = time.time()
        logger.info(f"=== GÉNÉRATION BREAK {duration}s ===")

        # Recherche FFmpeg
        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            logger.error("FFmpeg introuvable dans le PATH")
            return False

        # Recherche image sport_room.png
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

        command = [
            ffmpeg_path,
            "-loop",
            "1",  # Boucler l'image
            "-i",
            str(sport_room_image),  # Image source
            "-t",
            str(duration),  # Durée en secondes
            "-vf",
            "scale=1920:1080",  # Résolution standard
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            "-an",  # Pas d'audio
            "-y",
            str(output_path),
        ]

        try:
            logger.debug(f"Génération vidéo break: {' '.join(command)}")
            subprocess.run(command, check=True, capture_output=True, text=True)

            total_time = (time.time() - total_start) * 1000
            output_size = output_path.stat().st_size if output_path.exists() else 0
            logger.info(
                f"✓ Break {duration}s généré en {total_time:.0f}ms ({output_size/1024:.1f}KB)"
            )

            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Erreur génération break: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Erreur inattendue génération break: {e}")
            return False

    def _download_video_from_supabase(
        self, video_url: str, exercise_name: str
    ) -> Optional[Path]:
        """
        Télécharge une vidéo depuis Supabase Storage et la met en cache localement

        Args:
            video_url: URL de la vidéo dans Supabase Storage
            exercise_name: Nom de l'exercice (pour le nom du fichier)

        Returns:
            Optional[Path]: Chemin local de la vidéo en cache ou None si erreur
        """
        import time

        download_start = time.time()

        try:
            # Créer un hash de l'URL pour un nom de fichier unique
            url_hash = hashlib.md5(video_url.encode()).hexdigest()[:8]

            # Extraire l'extension du fichier depuis l'URL
            ext = Path(video_url).suffix or ".mov"

            # Nettoyer le nom de l'exercice pour le système de fichiers
            safe_name = "".join(
                c for c in exercise_name if c.isalnum() or c in (" ", "-", "_")
            ).strip()
            safe_name = safe_name.replace(" ", "_").lower()

            # Chemin du fichier en cache
            cache_file = self.video_cache_dir / f"{url_hash}_{safe_name}{ext}"

            # Si déjà en cache, retourner directement
            if cache_file.exists():
                cache_size = cache_file.stat().st_size
                cache_time = (time.time() - download_start) * 1000
                logger.info(
                    f"⏱️ Vidéo CACHE HIT: {exercise_name} ({cache_size/1024:.1f}KB) en {cache_time:.0f}ms"
                )
                return cache_file

            # Téléchargement depuis Supabase
            logger.info(f"⏱️ Téléchargement vidéo CACHE MISS: {exercise_name}")
            logger.info(f"   URL: {video_url[:80]}...")

            # Timeout augmenté et chunks plus gros pour téléchargement plus rapide
            response = requests.get(video_url, stream=True, timeout=120)
            response.raise_for_status()

            # Sauvegarder dans le cache avec chunks de 64KB
            bytes_downloaded = 0
            with open(cache_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=65536):  # 64KB chunks
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
                        bytes_downloaded += len(chunk)

            download_time = (time.time() - download_start) * 1000
            file_size_mb = cache_file.stat().st_size / (1024 * 1024)
            speed_mbps = (
                (file_size_mb / (download_time / 1000)) if download_time > 0 else 0
            )

            logger.info(
                f"⏱️ Vidéo téléchargée: {exercise_name} ({file_size_mb:.2f}MB) en {download_time:.0f}ms ({speed_mbps:.1f}MB/s)"
            )

            return cache_file

        except requests.RequestException as e:
            download_time = (time.time() - download_start) * 1000
            logger.error(f"⏱️ Erreur téléchargement après {download_time:.0f}ms: {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur inattendue lors du téléchargement: {e}")
            return None

    def _resolve_video_path(self, exercise: Exercise) -> Optional[Path]:
        """
        Résout le chemin de la vidéo d'un exercice
        Gère à la fois les URLs Supabase Storage et les chemins locaux

        Args:
            exercise: Exercice pour lequel résoudre le chemin

        Returns:
            Optional[Path]: Chemin vers la vidéo ou None si non trouvé
        """
        logger.debug(f"Résolution du chemin pour {exercise.name}")
        logger.debug(f"  video_url: {exercise.video_url}")

        # Si c'est une URL Supabase (commence par http), télécharger et cacher
        if exercise.is_supabase_url():
            logger.debug("  URL Supabase détectée, téléchargement...")
            return self._download_video_from_supabase(exercise.video_url, exercise.name)

        # Sinon, traiter comme un chemin local
        logger.debug(f"  Chemin local, project_root: {self.project_root}")

        video_path = Path(exercise.video_url)
        logger.debug(f"  video_path initial: {video_path}")
        logger.debug(f"  is_absolute: {video_path.is_absolute()}")

        # Vérifier si c'est un chemin absolu ou relatif
        if video_path.is_absolute():
            logger.debug(
                f"  Chemin absolu, vérification existence: {video_path.exists()}"
            )
            if video_path.exists():
                logger.debug(f"  Chemin absolu trouvé: {video_path}")
                return video_path
        else:
            # Chemin relatif, essayer plusieurs options
            # 1. Relatif au répertoire racine du projet
            full_path = self.project_root / video_path
            logger.debug(
                f"  Test chemin racine: {full_path}, existe: {full_path.exists()}"
            )
            if full_path.exists():
                logger.debug(f"  Chemin racine trouvé: {full_path}")
                return full_path

            # 2. Relatif au base_video_path (pour les vidéos générées si besoin)
            full_path = self.base_video_path / video_path
            logger.debug(
                f"  Test chemin base: {full_path}, existe: {full_path.exists()}"
            )
            if full_path.exists():
                logger.debug(f"  Chemin base trouvé: {full_path}")
                return full_path

        # Fallback
        logger.warning(
            f"Impossible de résoudre le chemin vidéo pour {exercise.name}, video_url: {exercise.video_url}"
        )
        return None

    def get_video_info(self, video_path: Path) -> Dict:
        """
        Obtient les informations d'une vidéo avec ffprobe

        Args:
            video_path: Chemin de la vidéo

        Returns:
            Dict: Informations de la vidéo (durée, résolution, codec, etc.)
        """
        try:
            command = [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                str(video_path),
            ]

            result = subprocess.run(command, capture_output=True, text=True, check=True)

            import json

            info = json.loads(result.stdout)
            logger.debug(f"Informations vidéo pour {video_path}: {info}")
            return info

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos vidéo: {e}")
            return {}
