"""
Script de test pour le service vidéo
Teste la génération d'une vidéo avec 2 exercices du dossier exercices_generation/outputs/
"""

import sys
from pathlib import Path
import logging

# Ajouter le répertoire backend au path pour les imports
sys.path.insert(0, str(Path(__file__).parent))

from app.services.video_service import VideoService  # noqa: E402
from app.models.exercise import Exercise, Difficulty, AccessTier  # noqa: E402
from app.models.config import WorkoutConfig  # noqa: E402
from app.models.enums import Intensity  # noqa: E402

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def test_video_generation():
    """Test de génération de vidéo avec 2 exercices"""

    logger.info("=" * 80)
    logger.info("DÉMARRAGE DU TEST DE GÉNÉRATION VIDÉO")
    logger.info("=" * 80)

    # 1. Créer le service vidéo avec chemin personnalisé
    # Les vidéos sont dans le dossier videos/ à la racine du projet
    video_service = VideoService(base_video_path=Path("../videos"))

    # 2. Créer des exercices de test
    exercises = [
        Exercise(
            name="Push-ups",
            description="Pompes classiques",
            icon="💪",
            video_url="../videos/push_ups.mov",
            default_duration=30,
            difficulty=Difficulty.MEDIUM,
            has_jump=False,
            access_tier=AccessTier.FREE,
        ),
        Exercise(
            name="Air Squat",
            description="Squats au poids du corps",
            icon="🦵",
            video_url="../videos/air_squat.mov",
            default_duration=45,
            difficulty=Difficulty.EASY,
            has_jump=False,
            access_tier=AccessTier.FREE,
        ),
    ]

    logger.info(f"Exercices créés: {len(exercises)}")
    for idx, ex in enumerate(exercises):
        logger.info(f"  {idx + 1}. {ex.name} ({ex.difficulty}, {ex.default_duration}s)")

    # 3. Test avec différentes intensités
    intensities = [
        Intensity.LOW_IMPACT,
        Intensity.MEDIUM_INTENSITY,
        Intensity.HIGH_INTENSITY,
    ]

    for intensity in intensities:
        logger.info("\n" + "-" * 80)
        logger.info(f"TEST AVEC INTENSITÉ: {intensity}")
        logger.info("-" * 80)

        # Créer la configuration
        config = WorkoutConfig(
            intensity=intensity,
            intervals={"work_time": 40, "rest_time": 20},
            no_jump=False,
            no_repeat=False,
            intensity_levels=[Difficulty.EASY, Difficulty.MEDIUM],
            target_duration=30,
        )

        logger.info(f"Configuration créée: {config.intensity}")

        # Définir le chemin de sortie
        output_path = Path(f"test_output_{intensity.value}.mp4")

        # Générer la vidéo
        logger.info(f"Génération de la vidéo: {output_path}")
        success = video_service.generate_workout_video(exercises, config, output_path)

        if success:
            logger.info(f"✅ SUCCÈS: Vidéo générée pour {intensity}")
            if output_path.exists():
                size_mb = output_path.stat().st_size / (1024 * 1024)
                logger.info(f"   Taille du fichier: {size_mb:.2f} MB")
        else:
            logger.error(f"❌ ÉCHEC: Génération échouée pour {intensity}")

        logger.info("-" * 80)

    # 4. Test de l'ajustement de vitesse seul
    logger.info("\n" + "=" * 80)
    logger.info("TEST D'AJUSTEMENT DE VITESSE")
    logger.info("=" * 80)

    input_video = Path("../videos/push_ups.mov")
    output_video = Path("test_speed_adjustment.mp4")

    if input_video.exists():
        logger.info(f"Test avec la vidéo: {input_video}")
        success = video_service.apply_speed_adjustment(
            input_video, output_video, speed=1.5
        )

        if success:
            logger.info("✅ SUCCÈS: Ajustement de vitesse 1.5x")
            if output_video.exists():
                size_mb = output_video.stat().st_size / (1024 * 1024)
                logger.info(f"   Taille du fichier: {size_mb:.2f} MB")
        else:
            logger.error("❌ ÉCHEC: Ajustement de vitesse")
    else:
        logger.warning(f"⚠️  Vidéo d'entrée non trouvée: {input_video}")

    # 5. Test d'obtention d'informations vidéo
    logger.info("\n" + "=" * 80)
    logger.info("TEST D'OBTENTION D'INFORMATIONS VIDÉO")
    logger.info("=" * 80)

    if input_video.exists():
        info = video_service.get_video_info(input_video)
        if info:
            logger.info("✅ Informations vidéo récupérées:")
            if "format" in info:
                duration = info["format"].get("duration", "N/A")
                size = info["format"].get("size", "N/A")
                logger.info(f"   Durée: {duration}s")
                logger.info(f"   Taille: {size} bytes")
        else:
            logger.error("❌ Impossible de récupérer les informations")

    logger.info("\n" + "=" * 80)
    logger.info("FIN DES TESTS")
    logger.info("=" * 80)


if __name__ == "__main__":
    try:
        test_video_generation()
    except Exception as e:
        logger.error(f"Erreur lors du test: {e}", exc_info=True)
        sys.exit(1)
