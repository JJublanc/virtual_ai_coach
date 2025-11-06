"""
Service de traitement vidéo avec FFmpeg
Gère la génération de vidéos d'entraînement en concaténant des exercices
avec ajustement de vitesse selon l'intensité
"""

import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
import tempfile
import os

from ..models.exercise import Exercise
from ..models.config import WorkoutConfig
from ..models.enums import Intensity

# Configuration du logger
logger = logging.getLogger(__name__)


class VideoService:
    """Service pour la génération et le traitement de vidéos d'entraînement"""

    # Multiplicateurs de vitesse selon l'intensité
    SPEED_MULTIPLIERS = {
        Intensity.LOW_IMPACT: 0.8,  # 80% vitesse normale (plus lent)
        Intensity.MEDIUM_INTENSITY: 1.0,  # Vitesse normale
        Intensity.HIGH_INTENSITY: 1.2,  # 120% vitesse normale (plus rapide)
    }

    def __init__(self, project_root: Path, base_video_path: Optional[Path] = None):
        """
        Initialise le service vidéo

        Args:
            base_video_path: Chemin de base pour les vidéos (par défaut: exercices_generation/outputs/)
        """
        self.project_root = project_root
        if base_video_path is None:
            # Chemin par défaut vers les vidéos d'exercices
            self.base_video_path = self.project_root / "exercices_generation/outputs"
        else:
            self.base_video_path = project_root / base_video_path

        logger.info(
            f"VideoService initialisé avec project_root: {self.project_root}, base_path: {self.base_video_path}"
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

    def apply_speed_adjustment(
        self, input_path: Path, output_path: Path, speed: float
    ) -> bool:
        """
        Applique un ajustement de vitesse à une vidéo

        Args:
            input_path: Chemin de la vidéo source
            output_path: Chemin de la vidéo de sortie
            speed: Multiplicateur de vitesse (0.8 = plus lent, 1.2 = plus rapide)

        Returns:
            bool: True si succès, False sinon

        Note:
            - speed < 1.0 : vidéo plus lente
            - speed = 1.0 : vitesse normale
            - speed > 1.0 : vidéo plus rapide
        """
        try:
            logger.info(
                f"Application ajustement vitesse {speed}x: {input_path} -> {output_path}"
            )

            # Calcul du PTS (Presentation TimeStamp) pour FFmpeg
            # PTS = 1/speed pour ajuster la vitesse
            pts_value = 1.0 / speed

            # Commande FFmpeg pour ajuster la vitesse
            command = [
                "ffmpeg",
                "-i",
                str(input_path),
                "-filter:v",
                f"setpts={pts_value}*PTS",
                "-an",  # Pas d'audio pour l'instant
                "-y",  # Overwrite output file
                str(output_path),
            ]

            logger.debug(f"Commande FFmpeg: {' '.join(command)}")

            # Exécution de la commande
            subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
            )

            logger.info(f"Vidéo avec vitesse ajustée créée: {output_path}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Erreur FFmpeg lors de l'ajustement de vitesse: {e}")
            logger.error(f"Stderr: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'ajustement de vitesse: {e}")
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
        sport_room_image = self.project_root / "sport_room.png"

        if not sport_room_image.exists():
            logger.error(f"Image sport_room.png introuvable: {sport_room_image}")
            return False

        command = [
            "ffmpeg",
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
            logger.info(f"Vidéo de break générée: {output_path} ({duration}s)")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Erreur génération break: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Erreur inattendue génération break: {e}")
            return False

    def build_ffmpeg_command(
        self,
        exercises: List[Exercise],
        config: WorkoutConfig,
        output_path: Path,
    ) -> List[str]:
        """
        Construit la commande FFmpeg pour concaténer plusieurs vidéos d'exercices

        Args:
            exercises: Liste des exercices à concaténer
            config: Configuration de l'entraînement
            output_path: Chemin du fichier de sortie

        Returns:
            List[str]: Commande FFmpeg complète

        Note:
            Cette méthode génère une commande FFmpeg complexe qui :
            1. Charge toutes les vidéos d'exercices
            2. Applique l'ajustement de vitesse selon l'intensité
            3. Concatène les vidéos
            4. Optimise pour le streaming
        """
        logger.info(f"Construction commande FFmpeg pour {len(exercises)} exercices")

        # Obtenir le multiplicateur de vitesse
        speed = self.get_speed_multiplier(config.intensity)
        logger.debug(f"Intensité: {config.intensity}, Vitesse: {speed}x")

        # Récupérer les durées work/rest
        work_time = config.intervals.get("work_time", 40)
        rest_time = config.intervals.get("rest_time", 20)
        logger.info(f"Intervals: work_time={work_time}s, rest_time={rest_time}s")

        # Créer un fichier temporaire de concaténation
        temp_dir = Path(tempfile.gettempdir())
        concat_file = temp_dir / f"concat_{os.getpid()}.txt"

        try:
            # Préparer les chemins des vidéos avec alternance exercices/breaks
            video_paths = []
            for idx, exercise in enumerate(exercises):
                # 1. Ajouter la vidéo d'exercice
                video_path = self._resolve_video_path(exercise)
                if video_path and video_path.exists():
                    video_paths.append(video_path)
                    logger.debug(f"Exercice {idx + 1}: {exercise.name} -> {video_path}")
                else:
                    logger.warning(
                        f"Vidéo non trouvée pour {exercise.name}: {video_path}"
                    )
                    continue

                # 2. Ajouter une vidéo de break (sauf après le dernier exercice)
                if idx < len(exercises) - 1:  # Pas de break après le dernier exercice
                    break_video_path = temp_dir / f"break_{idx}_{os.getpid()}.mp4"
                    if self.generate_break_video(rest_time, break_video_path):
                        video_paths.append(break_video_path)
                        logger.debug(
                            f"Break {idx + 1}: {rest_time}s -> {break_video_path}"
                        )
                    else:
                        logger.warning(
                            f"Impossible de générer la vidéo de break {idx + 1}"
                        )

            if not video_paths:
                logger.error("Aucune vidéo valide trouvée pour les exercices")
                return []

            # Créer le fichier de concaténation FFmpeg
            with open(concat_file, "w") as f:
                for video_path in video_paths:
                    # Format FFmpeg concat: file '/path/to/video.mov'
                    f.write(f"file '{video_path.absolute()}'\n")

            logger.debug(f"Fichier de concaténation créé: {concat_file}")

            # Construction de la commande FFmpeg
            command = [
                "ffmpeg",
                "-f",
                "concat",  # Format de concaténation
                "-safe",
                "0",  # Permet les chemins absolus
                "-i",
                str(concat_file),  # Fichier de concaténation
            ]

            # Ajout du filtre de vitesse si nécessaire
            if speed != 1.0:
                pts_value = 1.0 / speed
                command.extend(
                    [
                        "-filter:v",
                        f"setpts={pts_value}*PTS",
                    ]
                )

            # Options de sortie optimisées pour le streaming
            command.extend(
                [
                    "-c:v",
                    "libx264",  # Codec H.264
                    "-preset",
                    "ultrafast",  # Preset rapide pour réduire la latence
                    "-pix_fmt",
                    "yuv420p",  # Format pixel compatible
                    "-movflags",
                    "faststart+frag_keyframe+empty_moov+dash",  # Optimisation streaming progressif
                    "-an",  # Pas d'audio pour l'instant
                    "-y",  # Overwrite output file
                    str(output_path),
                ]
            )

            logger.info("Commande FFmpeg construite avec succès")
            logger.debug(f"Commande complète: {' '.join(command)}")

            return command

        except Exception as e:
            logger.error(f"Erreur lors de la construction de la commande FFmpeg: {e}")
            return []

    def _resolve_video_path(self, exercise: Exercise) -> Optional[Path]:
        """
        Résout le chemin de la vidéo d'un exercice

        Args:
            exercise: Exercice pour lequel résoudre le chemin

        Returns:
            Optional[Path]: Chemin vers la vidéo ou None si non trouvé

        Note:
            Pour l'instant, utilise des chemins locaux.
            TODO: Adapter pour gérer les URLs Supabase Storage
        """
        logger.debug(f"Résolution du chemin pour {exercise.name}")
        logger.debug(f"  video_url: {exercise.video_url}")
        logger.debug(f"  project_root: {self.project_root}")

        # Si video_url est défini et est un chemin local, l'utiliser directement
        if exercise.video_url:
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

        # Fallback: essayer de deviner le chemin basé sur le nom
        logger.warning(
            f"Impossible de résoudre le chemin vidéo pour {exercise.name}, video_url: {exercise.video_url}"
        )
        return None

    def generate_workout_video(
        self,
        exercises: List[Exercise],
        config: WorkoutConfig,
        output_path: Path,
    ) -> bool:
        """
        Génère une vidéo d'entraînement complète

        Args:
            exercises: Liste des exercices à inclure
            config: Configuration de l'entraînement
            output_path: Chemin du fichier de sortie

        Returns:
            bool: True si succès, False sinon
        """
        logger.info(f"Génération vidéo d'entraînement avec {len(exercises)} exercices")
        logger.info(f"Intensité: {config.intensity}")
        logger.info(f"Sortie: {output_path}")

        try:
            # Construire la commande FFmpeg
            command = self.build_ffmpeg_command(exercises, config, output_path)

            if not command:
                logger.error("Impossible de construire la commande FFmpeg")
                return False

            # Exécuter la commande
            logger.info("Exécution de FFmpeg...")
            subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
            )

            # Vérifier que le fichier a été créé
            if output_path.exists():
                file_size = output_path.stat().st_size
                logger.info(
                    f"Vidéo générée avec succès: {output_path} ({file_size} bytes)"
                )
                return True
            else:
                logger.error("Le fichier de sortie n'a pas été créé")
                return False

        except subprocess.CalledProcessError as e:
            logger.error(f"Erreur FFmpeg lors de la génération: {e}")
            logger.error(f"Stderr: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la génération: {e}")
            return False
        finally:
            # Nettoyage du fichier de concaténation temporaire
            temp_dir = Path(tempfile.gettempdir())
            concat_file = temp_dir / f"concat_{os.getpid()}.txt"
            if concat_file.exists():
                concat_file.unlink()
                logger.debug(f"Fichier temporaire supprimé: {concat_file}")

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
