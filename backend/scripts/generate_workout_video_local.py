#!/usr/bin/env python3
"""
Script pour générer et sauvegarder localement des vidéos d'entraînement.

Ce script génère automatiquement :
- Une vidéo MP4 de la session complète
- Un fichier texte (.txt) résumant la session avec :
  * Caractéristiques générales (durée, nombre d'exercices, etc.)
  * Structure par blocs (si applicable)
  * Répartition par difficulté et par thème
  * Liste détaillée de tous les exercices
  * Description globale et conseils

Usage:
    # Génération automatique basée sur des critères
    python generate_workout_video_local.py --auto --duration 600 --no-jump --intensity easy medium

    # Génération avec blocs thématiques (30 minutes)
    python generate_workout_video_local.py --auto --use-blocks --duration 1800 \
        --themes abs upper_body cardio --intensity medium hard

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
from app.models.config import WorkoutConfig, BlockConfig
from app.models.exercise import Difficulty, Exercise, ExerciseTheme
from app.models.workout import Workout
from app.services.video_service_optimized import OptimizedVideoService
from app.services.workout_generator import generate_workout_exercises
from video_studio.generators.workout_video_generator_v2 import WorkoutVideoGeneratorV2

# Import du nouveau module video_studio pour les overlays

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
    parser.add_argument(
        "--exercise-type",
        type=str,
        choices=["burpee", "jump", "run", "push_ups", "plank", "squat", "crunch"],
        default=None,
        help="Filtrer par type d'exercice spécifique (ex: burpee pour uniquement des burpees)",
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

    # NOUVEAU : Options pour le mode blocs thématiques
    parser.add_argument(
        "--use-blocks",
        action="store_true",
        help="Utiliser la génération par blocs thématiques (minimum 10 minutes)",
    )
    parser.add_argument(
        "--themes",
        nargs="+",
        choices=["abs", "upper_body", "legs", "cardio", "full_body"],
        default=["abs", "upper_body", "cardio"],
        help="Thèmes des blocs dans l'ordre (défaut: abs upper_body cardio)",
    )
    parser.add_argument(
        "--exercises-per-block",
        type=int,
        default=3,
        help="Nombre d'exercices différents par bloc (défaut: 3)",
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=3,
        help="Nombre de répétitions de chaque bloc (défaut: 3)",
    )
    parser.add_argument(
        "--no-finishers",
        action="store_true",
        help="Ne pas ajouter de finishers à la fin",
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
    use_blocks: bool = False,
    themes: List[str] = None,
    exercises_per_block: int = 3,
    repetitions: int = 3,
    no_finishers: bool = False,
    exercise_type: str = None,
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
    if exercise_type:
        logger.info(f"   Type d'exercice: {exercise_type}")

    if use_blocks:
        logger.info("   🎯 Mode BLOCS activé")
        logger.info(f"      Thèmes: {themes}")
        logger.info(f"      Exercices par bloc: {exercises_per_block}")
        logger.info(f"      Répétitions: {repetitions}")

    # Convertir les niveaux d'intensité en Difficulty
    difficulty_map = {
        "easy": Difficulty.EASY,
        "medium": Difficulty.MEDIUM,
        "hard": Difficulty.HARD,
    }
    difficulties = [difficulty_map[level] for level in intensity_levels]

    # Créer la configuration des blocs si demandé
    block_config = None
    if use_blocks:
        theme_enum_map = {
            "abs": ExerciseTheme.ABS,
            "upper_body": ExerciseTheme.UPPER_BODY,
            "legs": ExerciseTheme.LEGS,
            "cardio": ExerciseTheme.CARDIO,
            "full_body": ExerciseTheme.FULL_BODY,
        }
        theme_enums = [
            theme_enum_map[t] for t in (themes or ["abs", "upper_body", "cardio"])
        ]

        block_config = BlockConfig(
            themes=theme_enums,
            exercises_per_block=exercises_per_block,
            repetitions_per_block=repetitions,
            fill_remaining_with_finishers=not no_finishers,
            finisher_themes=[ExerciseTheme.CARDIO, ExerciseTheme.FULL_BODY],
        )

    # Créer la configuration
    config = WorkoutConfig(
        intensity=speed,
        intervals={"work_time": work_time, "rest_time": rest_time},
        no_jump=no_jump,
        exercice_intensity_levels=difficulties,
        target_duration=duration // 60,  # en minutes
        use_block_structure=use_blocks,
        block_config=block_config,
        exercise_type=exercise_type,
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
    Génère la vidéo finale avec overlays et la sauvegarde.

    Args:
        exercises: Liste des exercices
        config: Configuration du workout
        output_path: Chemin du fichier de sortie
        workout_name: Nom du workout

    Returns:
        True si succès, False sinon
    """
    try:
        logger.info(
            f"🎬 Génération de la vidéo avec overlays Pillow V2: {workout_name}"
        )
        logger.info(f"   Sortie: {output_path}")

        # Initialiser le service vidéo (pour télécharger les vidéos)
        project_root = Path(__file__).parent.parent.parent
        video_service = OptimizedVideoService(
            project_root=project_root,
            max_parallel_downloads=4,
        )

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

        # Préparer les données des exercices pour le générateur
        exercise_data = []
        for exercise in exercises:
            exercise_data.append(
                {
                    "name": exercise.name,
                    "description": exercise.description
                    or "Follow the movement carefully",
                }
            )

        # Utiliser le nouveau WorkoutVideoGeneratorV2 avec overlays Pillow
        logger.info(
            "🎨 Application des overlays Pillow (timer circulaire, panneaux arrondis, breaks)..."
        )
        generator = WorkoutVideoGeneratorV2(project_root=project_root)

        success = generator.generate_from_paths(
            exercise_videos=video_paths,
            exercise_data=exercise_data,
            config={
                "work_time": config.intervals.get("work_time", 40),
                "rest_time": config.intervals.get("rest_time", 20),
            },
            output_path=output_path,
            cleanup=True,
        )

        return success

    except Exception as e:
        logger.error(f"❌ Erreur lors de la génération: {e}", exc_info=True)
        return False


def generate_workout_summary(
    workout_name: str,
    exercises: List[Exercise],
    config: WorkoutConfig,
    output_path: Path,
    use_blocks: bool = False,
    themes: List[str] = None,
    exercises_per_block: int = None,
    repetitions: int = None,
) -> Path:
    """
    Génère un fichier texte résumant la session de workout.

    Args:
        workout_name: Nom du workout
        exercises: Liste des exercices
        config: Configuration du workout
        output_path: Chemin du fichier vidéo (pour générer le .txt à côté)
        use_blocks: Si le workout utilise des blocs thématiques
        themes: Liste des thèmes utilisés
        exercises_per_block: Nombre d'exercices par bloc
        repetitions: Nombre de répétitions par bloc

    Returns:
        Path du fichier de résumé généré
    """
    # Créer le chemin du fichier de résumé
    summary_path = output_path.with_suffix(".txt")

    # Calculer les statistiques
    work_time = config.intervals.get("work_time", 40)
    rest_time = config.intervals.get("rest_time", 20)
    total_duration = len(exercises) * (work_time + rest_time)
    total_minutes = total_duration // 60
    total_seconds = total_duration % 60

    # Compter les exercices par difficulté
    difficulty_counts = {
        "EASY": sum(1 for ex in exercises if ex.difficulty == Difficulty.EASY),
        "MEDIUM": sum(1 for ex in exercises if ex.difficulty == Difficulty.MEDIUM),
        "HARD": sum(1 for ex in exercises if ex.difficulty == Difficulty.HARD),
    }

    # Compter les exercices par thème
    theme_counts = {}
    for ex in exercises:
        if ex.metadata:
            for theme in ex.metadata.themes:
                theme_name = theme.value
                theme_counts[theme_name] = theme_counts.get(theme_name, 0) + 1

    # Construire le résumé
    lines = []
    lines.append("=" * 70)
    lines.append(f"WORKOUT SESSION SUMMARY: {workout_name}")
    lines.append("=" * 70)
    lines.append("")

    # Section: Caractéristiques générales
    lines.append("📊 GENERAL CHARACTERISTICS")
    lines.append("-" * 70)
    lines.append(
        f"Total duration       : {total_minutes}min {total_seconds}s ({total_duration}s)"
    )
    lines.append(f"Number of exercises  : {len(exercises)}")
    lines.append(f"Work time            : {work_time}s per exercise")
    lines.append(f"Rest time            : {rest_time}s between exercises")
    lines.append(f"Video intensity      : {config.intensity}")
    lines.append(f"No jumping           : {'Yes' if config.no_jump else 'No'}")
    lines.append("")

    # Section: Mode blocs (si applicable)
    if use_blocks:
        lines.append("🎯 THEMATIC BLOCK STRUCTURE")
        lines.append("-" * 70)
        lines.append(f"Themes used          : {', '.join(themes or [])}")
        lines.append(f"Exercises per block  : {exercises_per_block}")
        lines.append(f"Repetitions per block: {repetitions}")
        lines.append(
            f"Automatic finishers  : {'Yes' if config.block_config and config.block_config.fill_remaining_with_finishers else 'No'}"
        )
        lines.append("")

    # Section: Répartition par difficulté
    lines.append("💪 DIFFICULTY BREAKDOWN")
    lines.append("-" * 70)
    for difficulty, count in difficulty_counts.items():
        percentage = (count / len(exercises)) * 100 if exercises else 0
        lines.append(f"{difficulty:8} : {count:3} exercises ({percentage:5.1f}%)")
    lines.append("")

    # Section: Répartition par thème
    lines.append("🎨 THEME BREAKDOWN")
    lines.append("-" * 70)
    for theme, count in sorted(theme_counts.items()):
        percentage = (count / len(exercises)) * 100 if exercises else 0
        lines.append(f"{theme:12} : {count:3} exercises ({percentage:5.1f}%)")
    lines.append("")

    # Section: Liste détaillée des exercices
    lines.append("📝 DETAILED EXERCISE LIST")
    lines.append("-" * 70)
    lines.append("")

    for i, exercise in enumerate(exercises, 1):
        # Calculer le temps de début
        start_time = (i - 1) * (work_time + rest_time)
        start_minutes = start_time // 60
        start_seconds = start_time % 60

        lines.append(f"{i:3}. {exercise.name}")
        lines.append(
            f"     Time        : {start_minutes:02d}:{start_seconds:02d} - {start_minutes:02d}:{(start_seconds + work_time) % 60:02d}"
        )
        lines.append(f"     Difficulty  : {exercise.difficulty.value}")

        # Thèmes (si metadata existe)
        if exercise.metadata:
            themes_str = ", ".join([t.value for t in exercise.metadata.themes])
            lines.append(f"     Themes      : {themes_str}")

            # Muscles (si disponibles)
            if exercise.metadata.muscles_targeted:
                lines.append(
                    f"     Muscles     : {', '.join(exercise.metadata.muscles_targeted)}"
                )

        # has_jump est un attribut direct d'Exercise
        if exercise.has_jump:
            lines.append("     ⚠️  With jumping")

        # Vérifier si premium via access_tier
        if exercise.access_tier.value == "premium":
            lines.append("     ⭐ Premium")

        lines.append("")

    # Section: Description globale
    lines.append("📖 OVERALL DESCRIPTION")
    lines.append("-" * 70)

    if use_blocks and themes:
        theme_names_en = {
            "abs": "abs",
            "upper_body": "upper body",
            "legs": "legs",
            "cardio": "cardio",
            "full_body": "full body",
        }
        themes_en = [theme_names_en.get(t, t) for t in themes]

        description = (
            f"This {total_minutes}-minute session is structured into thematic blocks "
            f"for a complete and progressive workout. Each block targets a specific muscle group "
            f"({', '.join(themes_en)}) with {exercises_per_block} different exercises "
            f"repeated {repetitions} times. "
        )

        if config.block_config and config.block_config.fill_remaining_with_finishers:
            description += (
                "The session ends with intense finishers to maximize effort. "
            )
    else:
        description = (
            f"This {total_minutes}-minute session features {len(exercises)} varied exercises "
            f"for a complete full-body workout. "
        )

    # Ajouter des informations sur la difficulté dominante
    max_difficulty = max(difficulty_counts.items(), key=lambda x: x[1])[0]
    description += f"The dominant difficulty level is {max_difficulty.lower()}. "

    # Ajouter des informations sur les thèmes principaux
    if theme_counts:
        top_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:2]
        theme_names = [t[0] for t in top_themes]
        description += f"The main areas worked are: {', '.join(theme_names)}."

    lines.append(description)
    lines.append("")

    # Section: Conseils
    lines.append("💡 TIPS")
    lines.append("-" * 70)
    lines.append("• Warm up for 5-10 minutes before starting")
    lines.append("• Stay hydrated throughout the session")
    lines.append("• Respect rest times to optimize recovery")
    lines.append("• Adjust intensity according to your level")
    if config.no_jump:
        lines.append("• This no-jump session is apartment-friendly")
    lines.append("• End with stretching to promote recovery")
    lines.append("")

    lines.append("=" * 70)
    lines.append("Good workout! 🏋️")
    lines.append("=" * 70)

    # Écrire dans le fichier
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info(f"📄 Summary generated: {summary_path}")
    return summary_path


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
        use_blocks = False
        themes = None
        exercises_per_block = None
        repetitions = None

        if args.auto:
            # Valider la durée minimale pour les blocs
            if args.use_blocks and args.duration < 600:
                logger.error(
                    "❌ Erreur: Les blocs thématiques nécessitent minimum 10 minutes (600s)"
                )
                return 1

            # Mode automatique
            use_blocks = args.use_blocks
            themes = args.themes if args.use_blocks else None
            exercises_per_block = args.exercises_per_block
            repetitions = args.repetitions

            workout, exercises, config = generate_auto_workout(
                duration=args.duration,
                no_jump=args.no_jump,
                intensity_levels=args.intensity,
                work_time=args.work_time,
                rest_time=args.rest_time,
                workout_name=args.name,
                speed=args.speed,
                use_blocks=use_blocks,
                themes=themes,
                exercises_per_block=exercises_per_block,
                repetitions=repetitions,
                no_finishers=args.no_finishers,
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
            # Générer le résumé texte
            logger.info("")
            logger.info("📝 Génération du résumé de la session...")
            summary_path = generate_workout_summary(
                workout_name=args.name,
                exercises=exercises,
                config=config,
                output_path=output_path,
                use_blocks=use_blocks,
                themes=themes,
                exercises_per_block=exercises_per_block,
                repetitions=repetitions,
            )

            logger.info("")
            logger.info("=" * 60)
            logger.info("✨ GÉNÉRATION TERMINÉE AVEC SUCCÈS!")
            logger.info("=" * 60)
            logger.info(f"📹 Vidéo  : {output_path.absolute()}")
            logger.info(f"📄 Résumé : {summary_path.absolute()}")
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
