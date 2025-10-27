"""API endpoints pour la génération de vidéos d'entraînement."""

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..models.config import WorkoutConfig
from ..models.exercise import Exercise
from ..services.video_service import VideoService
from ..api.exercises import load_exercises

# Configuration du logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Forcer le niveau DEBUG pour voir tous les messages

# Ajouter un handler pour afficher les logs dans la console
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

router = APIRouter(prefix="/api", tags=["workouts"])

# Timeout maximum pour la génération vidéo (5 minutes)
GENERATION_TIMEOUT = 300  # secondes


class GenerateVideoRequest(BaseModel):
    """Requête pour générer une vidéo d'entraînement"""

    exercise_names: List[str] = Field(
        ...,
        min_length=1,
        description="Liste des noms d'exercices à inclure dans la vidéo",
        examples=[["Push-ups", "Air Squat", "Plank"]],
    )
    config: WorkoutConfig = Field(
        default_factory=WorkoutConfig,
        description="Configuration de l'entraînement",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "exercise_names": ["Push-ups", "Air Squat", "Plank"],
                "config": {
                    "intensity": "medium_intensity",
                    "intervals": {"work_time": 40, "rest_time": 20},
                    "no_jump": False,
                    "target_duration": 30,
                },
            }
        }
    }


async def stream_ffmpeg_output(
    command: List[str], concat_file: Path, timeout: int = GENERATION_TIMEOUT
):
    """
    Stream la sortie d'une commande FFmpeg de manière asynchrone.

    Args:
        command: Commande FFmpeg à exécuter
        concat_file: Chemin du fichier de concaténation temporaire à nettoyer après succès
        timeout: Timeout en secondes

    Yields:
        bytes: Chunks de données vidéo MP4

    Raises:
        HTTPException: En cas d'erreur ou timeout
    """
    process = None
    try:
        logger.info(f"Démarrage du processus FFmpeg avec timeout de {timeout}s")
        logger.debug(f"Commande: {' '.join(command)}")

        # Lancer le processus FFmpeg
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Streamer la sortie par chunks
        chunk_size = 64 * 1024  # 64KB chunks
        while True:
            try:
                # Lire un chunk avec timeout
                chunk = await asyncio.wait_for(
                    process.stdout.read(chunk_size), timeout=timeout
                )

                if not chunk:
                    # Fin du stream
                    break

                yield chunk

            except asyncio.TimeoutError:
                logger.error("Timeout lors de la lecture du stream FFmpeg")
                if process:
                    process.kill()
                    await process.wait()
                raise HTTPException(
                    status_code=504,
                    detail=f"Timeout de génération vidéo ({timeout}s dépassé)",
                )

        # Attendre la fin du processus
        return_code = await process.wait()

        if return_code != 0:
            stderr = await process.stderr.read()
            error_msg = stderr.decode("utf-8", errors="ignore")
            logger.error(f"Erreur FFmpeg (code {return_code}): {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la génération vidéo: {error_msg}",
            )

        logger.info("Génération vidéo terminée avec succès")

        # Nettoyage du fichier de concaténation temporaire après succès
        try:
            if concat_file and concat_file.exists():
                concat_file.unlink()
                logger.debug(f"Fichier temporaire nettoyé après succès: {concat_file}")
        except Exception as e:
            logger.warning(f"Impossible de nettoyer le fichier temporaire: {e}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur inattendue lors du streaming FFmpeg: {e}")
        if process:
            process.kill()
            await process.wait()
        raise HTTPException(
            status_code=500,
            detail=f"Erreur interne lors de la génération vidéo: {str(e)}",
        )


@router.post("/generate-workout-video")
async def generate_workout_video(request: GenerateVideoRequest):
    """
    Génère et streame une vidéo d'entraînement personnalisée.

    Cette endpoint :
    1. Charge les exercices demandés depuis la base de données
    2. Construit une commande FFmpeg pour concaténer et ajuster les vidéos
    3. Streame la vidéo MP4 résultante directement au client
    4. Applique l'intensité configurée (ajustement de vitesse)

    Args:
        request: Configuration contenant la liste d'exercices et les paramètres

    Returns:
        StreamingResponse: Vidéo MP4 streamée avec les headers appropriés

    Raises:
        HTTPException 404: Si un exercice demandé n'est pas trouvé
        HTTPException 500: Si une erreur survient lors de la génération
        HTTPException 504: Si le timeout de 5 minutes est dépassé

    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/generate-workout-video" \\
             -H "Content-Type: application/json" \\
             -d '{
                   "exercise_names": ["Push-ups", "Air Squat"],
                   "config": {"intensity": "medium_intensity"}
                 }' \\
             --output workout.mp4
        ```
    """
    try:
        logger.info(
            f"Requête de génération vidéo reçue pour {len(request.exercise_names)} exercices"
        )
        logger.info(f"Intensité: {request.config.intensity}")

        # 1. Charger tous les exercices disponibles
        all_exercises = load_exercises()

        # 2. Filtrer les exercices demandés
        selected_exercises: List[Exercise] = []
        for exercise_name in request.exercise_names:
            # Recherche insensible à la casse
            exercise = next(
                (
                    ex
                    for ex in all_exercises
                    if ex.name.lower() == exercise_name.lower()
                ),
                None,
            )

            if exercise is None:
                logger.error(f"Exercice non trouvé: {exercise_name}")
                raise HTTPException(
                    status_code=404,
                    detail=f"Exercice '{exercise_name}' non trouvé",
                )

            selected_exercises.append(exercise)
            logger.debug(f"Exercice sélectionné: {exercise.name}")

        if not selected_exercises:
            raise HTTPException(
                status_code=400,
                detail="Aucun exercice valide sélectionné",
            )

        # 3. Initialiser le service vidéo
        project_root = Path(
            __file__
        ).parent.parent.parent.parent  # Remonter à la racine du projet
        video_service = VideoService(project_root=project_root)

        # 4. Construire la commande FFmpeg pour le streaming
        # Note: On va utiliser stdout pour le streaming, donc on utilise 'pipe:1'
        # On modifie légèrement la commande pour écrire sur stdout
        speed = video_service.get_speed_multiplier(request.config.intensity)
        logger.debug(f"Multiplicateur de vitesse: {speed}x")

        # Préparer les chemins des vidéos et créer le fichier de concat
        temp_dir = Path(tempfile.gettempdir())
        import os

        concat_file = temp_dir / f"concat_{os.getpid()}.txt"

        video_paths = []
        for exercise in selected_exercises:
            video_path = video_service._resolve_video_path(exercise)
            if video_path and video_path.exists():
                video_paths.append(video_path)
                logger.debug(f"Vidéo trouvée: {exercise.name} -> {video_path}")
            else:
                logger.error(f"Vidéo manquante pour: {exercise.name}")
                raise HTTPException(
                    status_code=404,
                    detail=f"Fichier vidéo manquant pour l'exercice '{exercise.name}'",
                )

        # Créer le fichier de concaténation
        with open(concat_file, "w") as f:
            for video_path in video_paths:
                f.write(f"file '{video_path.absolute()}'\n")

        logger.debug(f"Fichier de concaténation créé: {concat_file}")
        logger.info(f"Fichier de concaténation existe: {concat_file.exists()}")

        # Construire la commande FFmpeg pour streaming vers stdout
        command = [
            "ffmpeg",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
        ]

        # Ajout du filtre de vitesse si nécessaire
        if speed != 1.0:
            pts_value = 1.0 / speed
            command.extend(["-filter:v", f"setpts={pts_value}*PTS"])

        # Options de sortie optimisées pour le streaming vers stdout
        command.extend(
            [
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "frag_keyframe+empty_moov",
                "-f",
                "mp4",  # Format MP4
                "-an",  # Pas d'audio
                "pipe:1",  # Écrire vers stdout
            ]
        )

        logger.info("Commande FFmpeg construite, démarrage du streaming")

        # 6. Retourner la réponse en streaming
        return StreamingResponse(
            stream_ffmpeg_output(command, concat_file, timeout=GENERATION_TIMEOUT),
            media_type="video/mp4",
            headers={
                "Content-Disposition": 'inline; filename="workout.mp4"',
                "Cache-Control": "no-cache",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Erreur inattendue lors de la génération vidéo: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erreur interne du serveur: {str(e)}",
        )
