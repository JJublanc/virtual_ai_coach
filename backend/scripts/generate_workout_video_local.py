#!/usr/bin/env python3
"""
Script pour générer et sauvegarder localement des vidéos d'entraînement.

Usage:
    # Génération automatique basée sur des critères
    python generate_workout_video_local.py --auto --duration 600 --no-jump --intensity easy medium

    # Génération manuelle avec liste d'exercices
    python generate_workout_video_local.py --exercises "Push-ups" "Air Squat" "Plank"

    # Spécifier un dossier de sortie personnalisé
    python generate_workout_video_local.py --auto --duration 300 --output-dir ./mes_videos
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import List
from uuid import uuid4

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# ruff: noqa: E402
from app.api.exercises import load_exercises
from app.models.config import WorkoutConfig
from app.models.exercise import Difficulty, Exercise
from app.models.workout import Workout
from app.services.video_service_optimized import OptimizedVideoService
from app.services.workout_generator import generate_workout_exercises

# Configuration du logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("workout_generation.log"),
    ],
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse les arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Génère et sauvegarde localement des vidéos d'entraînement"
    )

    # Mode de génération
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--auto",
        action="store_true",
        help="Génération automatique d'un workout basé sur des critères",
    )
    mode_group.add_argument(
        "--exercises",
        nargs="+",
        metavar="EXERCISE",
        help='Liste des noms d\'exercices (ex: "Push-ups" "Air Squat")',
    )

    # Arguments pour le mode automatique
    parser.add_argument(
        "--duration",
        type=int,
        default=600,
        help="Durée totale du workout en secondes (défaut: 600 = 10 minutes)",
    )
    parser.add_argument(
        "--no-jump",
        action="store_true",
        help="Exclure les exercices avec sauts",
    )
    parser.add_argument(
        "--intensity",
        nargs="+",
        choices=["easy", "medium", "hard"],
        default=["easy", "medium"],
        help="Niveaux de difficulté des exercices (défaut: easy medium)",
    )

    # Configuration des intervalles
    parser.add_argument(
        "--work-time",
        type=int,
        default=40,
        help="Durée de travail par exercice en secondes (défaut: 40)",
    )
    parser.add_argument(
        "--rest-time",
        type=int,
        default=20,
        help="Durée de repos entre exercices en secondes (défaut: 20)",
    )

    # Paramètres de sortie
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./videos_generated",
        help="Dossier de sortie pour les vidéos (défaut: ./generated_videos)",
    )
    parser.add_argument(
        "--output-name",
        type=str,
        default=None,
        help="Nom du fichier de sortie (défaut: workout_<timestamp>.mp4)",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="Mon Workout",
        help="Nom du workout (défaut: Mon Workout)",
    )

    # Options avancées
    parser.add_argument(
        "--speed",
        type=str,
        choices=["low_intensity", "medium_intensity", "high_intensity"],
        default="medium_intensity",
        help="Intensité/vitesse de la vidéo (défaut: medium_intensity)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Mode verbose (plus de logs)",
    )

    return parser.parse_args()


def setup_output_directory(output_dir: str) -> Path:
    """Crée et retourne le dossier de sortie."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Dossier de sortie: {output_path.absolute()}")
    return output_path


def generate_auto_workout(
    duration: int,
    no_jump: bool,
    intensity_levels: List[str],
    work_time: int,
    rest_time: int,
    workout_name: str,
    speed: str,
) -> tuple[Workout, List[Exercise], WorkoutConfig]:
    """
    Génère automatiquement un workout basé sur les critères.

    Returns:
        Tuple (workout, exercises, config)
    """
    logger.info("🎲 Génération automatique du workout...")
    logger.info(f"   Durée: {duration}s ({duration // 60} minutes)")
    logger.info(f"   No jump: {no_jump}")
    logger.info(f"   Intensités: {intensity_levels}")
    logger.info(f"   Intervalles: {work_time}s travail / {rest_time}s repos")

    # Convertir les niveaux d'intensité en Difficulty
    difficulty_map = {
        "easy": Difficulty.EASY,
        "medium": Difficulty.MEDIUM,
        "hard": Difficulty.HARD,
    }
    difficulties = [difficulty_map[level] for level in intensity_levels]

    # Créer la configuration
    config = WorkoutConfig(
        intensity=speed,
        intervals={"work_time": work_time, "rest_time": rest_time},
        no_jump=no_jump,
        exercice_intensity_levels=difficulties,
        target_duration=duration // 60,  # en minutes
    )

    # Créer le workout
    workout = Workout(
        id=uuid4(),
        name=workout_name,
        config=config,
        total_duration=duration,
    )

    # Générer les exercices
    workout_exercises = generate_workout_exercises(workout)
    logger.info(f"✅ {len(workout_exercises)} exercices générés")

    # Charger les exercices complets
    all_exercises = load_exercises()
    selected_exercises = []

    for workout_ex in workout_exercises:
        exercise = next(
            (ex for ex in all_exercises if ex.id == workout_ex.exercise_id), None
        )
        if exercise:
            selected_exercises.append(exercise)
            logger.debug(f"   - {exercise.name} ({exercise.difficulty.value})")
        else:
            logger.warning(f"⚠️  Exercice non trouvé: {workout_ex.exercise_id}")

    return workout, selected_exercises, config


def generate_manual_workout(
    exercise_names: List[str],
    work_time: int,
    rest_time: int,
    workout_name: str,
    speed: str,
) -> tuple[List[Exercise], WorkoutConfig]:
    """
    Génère un workout à partir d'une liste manuelle d'exercices.

    Returns:
        Tuple (exercises, config)
    """
    logger.info("📝 Génération manuelle du workout...")
    logger.info(f"   {len(exercise_names)} exercices demandés")

    # Charger tous les exercices
    all_exercises = load_exercises()

    # Filtrer les exercices demandés
    selected_exercises = []
    for name in exercise_names:
        exercise = next(
            (ex for ex in all_exercises if ex.name.lower() == name.lower()),
            None,
        )
        if exercise:
            selected_exercises.append(exercise)
            logger.info(f"   ✓ {exercise.name}")
        else:
            logger.error(f"   ✗ Exercice non trouvé: {name}")
            raise ValueError(f"Exercice '{name}' non trouvé")

    # Créer la configuration
    config = WorkoutConfig(
        intensity=speed,
        intervals={"work_time": work_time, "rest_time": rest_time},
    )

    return selected_exercises, config


def generate_video(
    exercises: List[Exercise],
    config: WorkoutConfig,
    output_path: Path,
    workout_name: str = "Mon Workout",
) -> bool:
    """
    Génère la vidéo finale et la sauvegarde.

    Args:
        exercises: Liste des exercices
        config: Configuration du workout
        output_path: Chemin du fichier de sortie
        workout_name: Nom du workout

    Returns:
        True si succès, False sinon
    """
    try:
        logger.info(f"🎬 Génération de la vidéo: {workout_name}")
        logger.info(f"   Sortie: {output_path}")

        # Initialiser le service vidéo
        project_root = Path(__file__).parent.parent.parent
        video_service = OptimizedVideoService(
            project_root=project_root,
            max_parallel_downloads=4,
        )

        start_time = time.time()

        # Télécharger les vidéos en parallèle
        logger.info("📥 Téléchargement des vidéos d'exercices...")
        video_map = video_service._download_videos_parallel(exercises)

        # Vérifier que toutes les vidéos sont disponibles
        video_paths = []
        for exercise in exercises:
            video_path = video_map.get(exercise.name)
            if video_path and video_path.exists():
                video_paths.append(video_path)
            else:
                logger.error(f"❌ Vidéo manquante pour: {exercise.name}")
                return False

        # Préparer les breaks
        logger.info("⏸️  Préparation des vidéos de pause...")
        rest_time = config.intervals.get("rest_time", 20)
        break_paths = []

        # On ajoute un break entre chaque exercice (sauf après le dernier)
        for i in range(len(exercises) - 1):
            break_path = video_service._get_or_create_break(
                duration=rest_time,
                temp_dir=Path("/tmp"),
            )
            break_paths.append(break_path)

        # Construire la vidéo finale
        logger.info("🔧 Construction de la vidéo finale...")
        success = video_service.build_progressive_concat(
            video_paths=video_paths,
            break_paths=break_paths,
            output_path=output_path,
            cleanup_intermediates=True,
        )

        if success:
            elapsed = time.time() - start_time
            file_size = output_path.stat().st_size / (1024 * 1024)  # MB
            logger.info("✅ Vidéo générée avec succès!")
            logger.info(f"   Temps: {elapsed:.1f}s")
            logger.info(f"   Taille: {file_size:.1f} MB")
            logger.info(f"   Fichier: {output_path.absolute()}")
            return True
        else:
            logger.error("❌ Échec de la génération vidéo")
            return False

    except Exception as e:
        logger.error(f"❌ Erreur lors de la génération: {e}", exc_info=True)
        return False


def main():
    """Point d'entrée principal du script."""
    args = parse_arguments()

    # Configurer le niveau de log
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("=" * 60)
    logger.info("🏋️  GÉNÉRATEUR DE VIDÉOS D'ENTRAÎNEMENT")
    logger.info("=" * 60)

    try:
        # Créer le dossier de sortie
        output_dir = setup_output_directory(args.output_dir)

        # Générer le nom de fichier
        if args.output_name:
            output_filename = args.output_name
            if not output_filename.endswith(".mp4"):
                output_filename += ".mp4"
        else:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_filename = f"workout_{timestamp}.mp4"

        output_path = output_dir / output_filename

        # Générer le workout selon le mode
        if args.auto:
            # Mode automatique
            workout, exercises, config = generate_auto_workout(
                duration=args.duration,
                no_jump=args.no_jump,
                intensity_levels=args.intensity,
                work_time=args.work_time,
                rest_time=args.rest_time,
                workout_name=args.name,
                speed=args.speed,
            )
        else:
            # Mode manuel
            exercises, config = generate_manual_workout(
                exercise_names=args.exercises,
                work_time=args.work_time,
                rest_time=args.rest_time,
                workout_name=args.name,
                speed=args.speed,
            )

        # Afficher le résumé
        logger.info("")
        logger.info("📋 Résumé du workout:")
        logger.info(f"   Nom: {args.name}")
        logger.info(f"   Exercices: {len(exercises)}")
        logger.info(
            f"   Durée estimée: {len(exercises) * (args.work_time + args.rest_time)}s"
        )
        logger.info("")

        # Générer la vidéo
        success = generate_video(
            exercises=exercises,
            config=config,
            output_path=output_path,
            workout_name=args.name,
        )

        if success:
            logger.info("")
            logger.info("=" * 60)
            logger.info("✨ GÉNÉRATION TERMINÉE AVEC SUCCÈS!")
            logger.info("=" * 60)
            return 0
        else:
            logger.error("")
            logger.error("=" * 60)
            logger.error("❌ ÉCHEC DE LA GÉNÉRATION")
            logger.error("=" * 60)
            return 1

    except KeyboardInterrupt:
        logger.warning("\n⚠️  Génération interrompue par l'utilisateur")
        return 130
    except Exception as e:
        logger.error(f"\n❌ Erreur fatale: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
