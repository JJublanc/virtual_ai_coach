"""API endpoints pour la génération de vidéos d'entraînement."""

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import List
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..models.config import WorkoutConfig
from ..models.exercise import Exercise
from ..models.workout import Workout
from ..services.video_service_optimized import OptimizedVideoService
from ..services.workout_generator import (
    generate_workout_exercises,
)
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


class GenerateWorkoutVideoRequest(BaseModel):
    """Requête pour générer automatiquement un workout et sa vidéo"""

    config: WorkoutConfig = Field(
        ...,
        description="Configuration du workout (intensité, durée, critères de filtrage)",
    )
    total_duration: int = Field(
        ..., gt=0, description="Durée totale du workout en secondes"
    )
    name: str = Field(default="Workout Généré", description="Nom du workout")
    workout_id: str = Field(
        default=None,
        description="ID unique du workout pour le streaming progressif (optionnel)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "config": {
                    "intensity": "medium_intensity",
                    "intervals": {"work_time": 40, "rest_time": 20},
                    "no_jump": True,
                    "exercice_intensity_levels": ["easy", "medium"],
                    "target_duration": 30,
                },
                "total_duration": 600,  # 10 minutes
                "name": "Mon Workout Matinal",
            }
        }
    }


class WorkoutGenerationResponse(BaseModel):
    """Réponse contenant les informations du workout généré"""

    workout_id: str = Field(..., description="ID unique du workout généré")
    name: str = Field(..., description="Nom du workout")
    total_duration: int = Field(..., description="Durée totale en secondes")
    exercise_count: int = Field(..., description="Nombre d'exercices générés")
    exercises: List[str] = Field(..., description="Liste des noms d'exercices")
    config: WorkoutConfig = Field(..., description="Configuration utilisée")

    model_config = {
        "json_schema_extra": {
            "example": {
                "workout_id": "12345678-1234-1234-1234-123456789012",
                "name": "Mon Workout Matinal",
                "total_duration": 600,
                "exercise_count": 10,
                "exercises": [
                    "Push-ups",
                    "Air Squat",
                    "Plank",
                    "Push-ups",
                    "Air Squat",
                ],
                "config": {
                    "intensity": "medium_intensity",
                    "intervals": {"work_time": 40, "rest_time": 20},
                    "no_jump": True,
                    "exercice_intensity_levels": ["easy", "medium"],
                },
            }
        }
    }


class WorkoutExerciseDetail(BaseModel):
    """Détail d'un exercice dans un workout"""

    name: str = Field(..., description="Nom de l'exercice")
    description: str = Field(..., description="Description détaillée de l'exercice")
    icon: str = Field(..., description="Icône de l'exercice")
    duration: int = Field(..., description="Durée en secondes")
    order: int = Field(..., description="Ordre dans la séquence")
    difficulty: str = Field(..., description="Niveau de difficulté")


class WorkoutDetailResponse(BaseModel):
    """Réponse détaillée d'un workout avec ses exercices"""

    workout_id: str = Field(..., description="ID unique du workout")
    name: str = Field(..., description="Nom du workout")
    total_duration: int = Field(..., description="Durée totale en secondes")
    exercise_count: int = Field(..., description="Nombre d'exercices")
    exercises: List[WorkoutExerciseDetail] = Field(
        ..., description="Liste détaillée des exercices"
    )
    config: WorkoutConfig = Field(..., description="Configuration utilisée")


# Store temporaire pour les workouts générés (en production, utiliser une DB)
generated_workouts = {}


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

        # 3. Initialiser le service vidéo optimisé
        project_root = Path(
            __file__
        ).parent.parent.parent.parent  # Remonter à la racine du projet
        video_service = OptimizedVideoService(project_root=project_root)

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
                "Accept-Ranges": "bytes",  # Support des Range Requests pour streaming progressif
                "Content-Disposition": 'inline; filename="workout.mp4"',
                "Cache-Control": "no-cache",
                "Transfer-Encoding": "chunked",  # Streaming par chunks
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


@router.post("/generate-auto-workout-video")
async def generate_auto_workout_video(request: GenerateWorkoutVideoRequest):
    """
    Génère automatiquement un workout et streame sa vidéo.

    Cette endpoint effectue un processus complet de bout en bout :
    1. Crée un objet Workout basé sur la configuration fournie
    2. Génère automatiquement une liste d'exercices aléatoires via workout_generator
    3. Charge les exercices complets depuis la base de données
    4. Construit et streame la vidéo MP4 résultante

    Args:
        request: Configuration contenant la durée, les critères de filtrage et les paramètres

    Returns:
        StreamingResponse: Vidéo MP4 streamée avec les headers appropriés

    Raises:
        HTTPException 400: Si la configuration est invalide
        HTTPException 404: Si aucun exercice ne correspond aux critères
        HTTPException 500: Si une erreur survient lors de la génération
        HTTPException 504: Si le timeout de 5 minutes est dépassé

    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/generate-auto-workout-video" \\
             -H "Content-Type: application/json" \\
             -d '{
                   "config": {
                     "intensity": "medium_intensity",
                     "intervals": {"work_time": 40, "rest_time": 20},
                     "no_jump": true,
                     "exercice_intensity_levels": ["easy", "medium"]
                   },
                   "total_duration": 600,
                   "name": "Mon Workout Matinal"
                 }' \\
             --output workout.mp4
        ```
    """
    try:
        logger.info("Requête de génération automatique de workout reçue")
        logger.info(f"Nom: {request.name}")
        logger.info(
            f"Durée: {request.total_duration}s ({request.total_duration // 60} minutes)"
        )
        logger.info(f"Intensité: {request.config.intensity}")
        logger.info(f"No jump: {request.config.no_jump}")
        logger.info(
            f"Niveaux de difficulté: {request.config.exercice_intensity_levels}"
        )

        # 1. Créer l'objet Workout
        workout_id = uuid4()
        workout = Workout(
            id=workout_id,
            name=request.name,
            config=request.config,
            total_duration=request.total_duration,
            ai_generated=True,
        )

        logger.info(f"Workout créé avec ID: {workout_id}")

        # 2. Générer automatiquement les exercices via workout_generator
        try:
            workout_exercises = generate_workout_exercises(workout)
            logger.info(f"{len(workout_exercises)} exercices générés automatiquement")
        except ValueError as e:
            logger.error(f"Erreur lors de la génération des exercices: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Impossible de générer des exercices avec ces critères: {str(e)}",
            )

        # 3. Charger les exercices complets depuis la base de données
        all_exercises = load_exercises()

        # Créer un mapping ID -> Exercise pour une recherche rapide
        exercises_by_id = {str(ex.id): ex for ex in all_exercises}

        # Récupérer les exercices complets dans l'ordre généré
        selected_exercises: List[Exercise] = []
        for workout_ex in workout_exercises:
            exercise_id_str = str(workout_ex.exercise_id)
            if exercise_id_str in exercises_by_id:
                selected_exercises.append(exercises_by_id[exercise_id_str])
                logger.debug(
                    f"Exercice {workout_ex.order_index}: {exercises_by_id[exercise_id_str].name}"
                )
            else:
                logger.error(
                    f"Exercice avec ID {exercise_id_str} non trouvé dans la base"
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Exercice avec ID {exercise_id_str} non trouvé",
                )

        if not selected_exercises:
            raise HTTPException(
                status_code=500, detail="Aucun exercice valide n'a pu être chargé"
            )

        logger.info(f"{len(selected_exercises)} exercices chargés pour la vidéo")

        # 4. Initialiser le service vidéo optimisé
        project_root = Path(__file__).parent.parent.parent.parent
        video_service = OptimizedVideoService(project_root=project_root)

        # 5. Préparer la commande FFmpeg pour le streaming
        speed = video_service.get_speed_multiplier(request.config.intensity)
        logger.debug(f"Multiplicateur de vitesse: {speed}x")

        # Créer le fichier de concaténation temporaire
        temp_dir = Path(tempfile.gettempdir())
        import os

        concat_file = temp_dir / f"concat_{os.getpid()}.txt"

        # Vérifier et préparer les chemins vidéo
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

        # 6. Construire la commande FFmpeg pour streaming vers stdout
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

        # Options de sortie optimisées pour le streaming
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
                "mp4",
                "-an",  # Pas d'audio
                "pipe:1",  # Écrire vers stdout
            ]
        )

        logger.info("Commande FFmpeg construite, démarrage du streaming")
        logger.info(f"Workout: {request.name} - {len(selected_exercises)} exercices")

        # 7. Stocker les détails du workout pour récupération ultérieure
        workout_details = []
        for i, exercise in enumerate(selected_exercises):
            workout_details.append(
                WorkoutExerciseDetail(
                    name=exercise.name,
                    description=exercise.description or "Description non disponible",
                    icon=exercise.icon or "🏋️",
                    duration=exercise.default_duration,
                    order=i + 1,
                    difficulty=exercise.difficulty.value,
                )
            )

        generated_workouts[str(workout_id)] = WorkoutDetailResponse(
            workout_id=str(workout_id),
            name=request.name,
            total_duration=request.total_duration,
            exercise_count=len(selected_exercises),
            exercises=workout_details,
            config=request.config,
        )

        # 8. Retourner la réponse en streaming
        return StreamingResponse(
            stream_ffmpeg_output(command, concat_file, timeout=GENERATION_TIMEOUT),
            media_type="video/mp4",
            headers={
                "Content-Disposition": f'inline; filename="{request.name.replace(" ", "_")}.mp4"',
                "Cache-Control": "no-cache",
                "X-Workout-ID": str(workout_id),
                "X-Exercise-Count": str(len(selected_exercises)),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Erreur inattendue lors de la génération automatique: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erreur interne du serveur: {str(e)}",
        )


@router.get("/workout-details/{workout_id}", response_model=WorkoutDetailResponse)
async def get_workout_details(workout_id: str):
    """
    Récupère les détails d'un workout généré par son ID.

    Args:
        workout_id: ID unique du workout généré

    Returns:
        WorkoutDetailResponse: Détails complets du workout avec la liste des exercices

    Raises:
        HTTPException 404: Si le workout n'est pas trouvé

    Example:
        ```bash
        curl -X GET "http://localhost:8000/api/workout-details/12345678-1234-1234-1234-123456789012"
        ```
    """
    if workout_id not in generated_workouts:
        raise HTTPException(
            status_code=404, detail=f"Workout avec ID '{workout_id}' non trouvé"
        )

    return generated_workouts[workout_id]


@router.post("/start-workout-generation")
async def start_workout_generation(request: GenerateWorkoutVideoRequest):
    """
    Démarre la génération d'un workout en arrière-plan pour le streaming progressif.

    Cette endpoint permet de séparer le démarrage de la génération du streaming,
    permettant au frontend de commencer immédiatement le streaming via /stream-workout/{workout_id}

    Returns:
        dict: Contient le workout_id pour accéder au stream
    """
    logger.info("Démarrage de génération de workout en arrière-plan")

    try:
        # Générer un ID unique si non fourni
        workout_id = request.workout_id or str(uuid4())

        # 1. Créer l'objet Workout
        workout = Workout(
            id=workout_id,
            name=request.name,
            config=request.config,
            total_duration=request.total_duration,
        )

        logger.info(f"Workout créé: {workout.name} (ID: {workout_id})")

        # 2. Générer la liste d'exercices
        exercises = generate_workout_exercises(workout)
        logger.info(f"Génération terminée: {len(exercises)} exercices")

        # 3. Charger les exercices complets depuis la base de données
        all_exercises = load_exercises()

        full_exercises = []
        for workout_exercise in exercises:
            # workout_exercise est un objet WorkoutExercise, on récupère l'exercise_id
            exercise_id = workout_exercise.exercise_id
            # Chercher l'exercice complet par ID
            matching_exercise = next(
                (ex for ex in all_exercises if ex.id == exercise_id), None
            )
            if matching_exercise:
                full_exercises.append(matching_exercise)
            else:
                logger.warning(
                    f"Exercice avec ID '{exercise_id}' non trouvé dans la base"
                )

        if not full_exercises:
            raise HTTPException(
                status_code=404,
                detail="Aucun exercice valide trouvé pour cette configuration",
            )

        logger.info(f"Exercices chargés: {len(full_exercises)} exercices valides")

        # 4. Stocker les données du workout pour le streaming
        workout_data = {
            "exercises": full_exercises,
            "config": request.config,
            "total_duration": request.total_duration,
            "name": request.name,
            "workout_id": workout_id,
        }

        generated_workouts[workout_id] = workout_data

        logger.info(f"Workout {workout_id} prêt pour streaming")

        return {
            "workout_id": workout_id,
            "message": "Génération démarrée, utilisez /stream-workout/{workout_id} pour le streaming",
            "total_exercises": len(full_exercises),
            "estimated_duration_minutes": request.total_duration // 60,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de génération: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur interne du serveur: {str(e)}",
        )


@router.get("/workout-exercises/{workout_id}")
async def get_workout_exercises(workout_id: str):
    """
    Récupère la liste des exercices d'un workout généré, incluant les périodes de break.
    Utilisé par le frontend pour afficher la liste des exercices avec alternance work/rest.
    """
    logger.info(f"Récupération des exercices pour workout {workout_id}")

    # Vérifier si le workout existe
    workout_data = generated_workouts.get(workout_id)
    if not workout_data:
        logger.error(f"Workout {workout_id} non trouvé")
        raise HTTPException(404, "Workout not found")

    # Extraire les exercices et la config
    exercises = workout_data.get("exercises", [])
    config = workout_data.get("config")

    # Générer la liste avec alternance exercices/breaks
    from ..services.workout_generator import generate_workout_with_intervals

    workout_items = generate_workout_with_intervals(exercises, config)

    logger.info(
        f"Retour de {len(workout_items)} items (exercices + breaks) pour workout {workout_id}"
    )

    return {
        "workout_id": workout_id,
        "exercises": workout_items,
        "total_exercises": len(workout_items),
    }


# ============================================================================
# NOUVEAUX ENDPOINTS POUR STREAMING PROGRESSIF - PHASE 1.4
# ============================================================================


@router.get("/stream-workout/{workout_id}")
async def stream_workout(workout_id: str, request: Request):
    """
    Stream progressif d'une vidéo de workout pré-générée ou en cours de génération.
    Support des Range Requests pour lecture progressive.

    Cette endpoint permet au navigateur de commencer la lecture dès que les premières
    données sont disponibles, sans attendre la fin complète de la génération.
    """
    logger.info(f"Demande de streaming pour workout {workout_id}")

    # Vérifier si le workout existe
    workout_data = generated_workouts.get(workout_id)
    if not workout_data:
        logger.error(f"Workout {workout_id} non trouvé")
        raise HTTPException(404, "Workout not found")

    # Gérer les Range Requests du navigateur
    range_header = request.headers.get("Range")
    logger.debug(f"Range header reçu: {range_header}")

    # CORRECTION: Pour le streaming progressif, on ignore les Range Requests
    # et on fait toujours du streaming complet depuis le début
    # Cela permet au navigateur de commencer la lecture immédiatement

    logger.info(f"Démarrage streaming complet pour workout {workout_id}")
    return StreamingResponse(
        stream_workout_progressive(workout_data),
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Transfer-Encoding": "chunked",  # Streaming par chunks
            "Cache-Control": "public, max-age=3600",  # Cache 1h
            "Content-Disposition": f'inline; filename="workout_{workout_id}.mp4"',
        },
    )


async def stream_workout_progressive(workout_data):
    """
    Stream la génération FFmpeg avec buffer intelligent pour optimiser
    le temps de démarrage de la lecture vidéo.

    Cette fonction accumule les premières données (contenant l'atom moov)
    avant de commencer le streaming, permettant au navigateur de démarrer
    la lecture plus rapidement.
    """
    logger.info("Démarrage du streaming progressif")

    # Construire la commande FFmpeg optimisée
    command = build_optimized_ffmpeg_command(workout_data)
    logger.debug(f"Commande FFmpeg: {' '.join(command)}")

    # OPTIMISATION 2: Buffer réduit pour démarrer le streaming plus vite
    # Réduit de 1MB à 256KB pour diminuer le temps d'attente initial
    initial_buffer = bytearray()
    buffer_size = 256 * 1024  # 256KB buffer initial (optimisé pour démarrage rapide)

    try:
        logger.info(f"Lancement de FFmpeg avec commande: {' '.join(command)}")

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        logger.info("Processus FFmpeg démarré, buffering des premières données...")

        # Lire stderr en arrière-plan pour capturer les erreurs
        async def read_stderr():
            stderr_data = []
            while True:
                line = await process.stderr.readline()
                if not line:
                    break
                decoded_line = line.decode("utf-8", errors="replace").strip()
                if decoded_line:
                    stderr_data.append(decoded_line)
                    # Log les erreurs importantes
                    if (
                        "error" in decoded_line.lower()
                        or "no such file" in decoded_line.lower()
                    ):
                        logger.error(f"FFmpeg stderr: {decoded_line}")
                    elif "warning" in decoded_line.lower():
                        logger.warning(f"FFmpeg stderr: {decoded_line}")
            return "\n".join(stderr_data)

        # Démarrer la lecture de stderr en arrière-plan
        stderr_task = asyncio.create_task(read_stderr())

        # Lire et buffer les premières données avec timeout
        timeout_seconds = 120  # 2 minutes de timeout pour le buffer initial
        start_time = asyncio.get_event_loop().time()

        while len(initial_buffer) < buffer_size:
            # Vérifier le timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout_seconds:
                logger.error(f"Timeout après {elapsed}s lors du buffering initial")
                # Récupérer les erreurs stderr
                stderr_output = await asyncio.wait_for(stderr_task, timeout=5)
                logger.error(f"FFmpeg stderr complet: {stderr_output}")
                raise HTTPException(500, f"Timeout FFmpeg après {int(elapsed)}s")

            try:
                chunk = await asyncio.wait_for(
                    process.stdout.read(64 * 1024), timeout=30
                )  # 64KB chunks avec timeout 30s
            except asyncio.TimeoutError:
                logger.warning(
                    f"Timeout lors de la lecture d'un chunk, buffer actuel: {len(initial_buffer)} bytes"
                )
                continue

            if not chunk:
                # Vérifier si le processus s'est terminé avec une erreur
                return_code = process.returncode
                if return_code is not None and return_code != 0:
                    stderr_output = await asyncio.wait_for(stderr_task, timeout=10)
                    logger.error(
                        f"FFmpeg s'est terminé avec le code {return_code}: {stderr_output}"
                    )
                    raise HTTPException(
                        500,
                        f"Erreur FFmpeg (code {return_code}): {stderr_output[:500]}",
                    )
                break
            initial_buffer.extend(chunk)

            # Log de progression
            if len(initial_buffer) % (256 * 1024) == 0:  # Tous les 256KB
                logger.debug(f"Buffer progression: {len(initial_buffer)} bytes")

        logger.info(f"Buffer initial de {len(initial_buffer)} bytes prêt")

        # Vérifier si nous avons des données à envoyer
        if len(initial_buffer) == 0:
            # Vérifier les erreurs FFmpeg
            stderr_output = await asyncio.wait_for(stderr_task, timeout=10)
            logger.error(f"Aucune donnée FFmpeg. Stderr: {stderr_output}")
            raise HTTPException(
                500, f"FFmpeg n'a produit aucune donnée: {stderr_output[:500]}"
            )

        # === LOGS D'ENVOI DES CHUNKS ===
        logger.info("=== DÉBUT ENVOI CHUNKS AU FRONTEND ===")
        logger.info(
            f"Buffer initial prêt: {len(initial_buffer)} bytes ({len(initial_buffer)/1024:.1f} KB)"
        )

        # Envoyer le buffer initial (contient moov atom)
        logger.info(f"Envoi buffer initial: {len(initial_buffer)} bytes")
        yield bytes(initial_buffer)
        logger.info("✓ Buffer initial envoyé au frontend")

        total_bytes_sent = len(initial_buffer)

        # Continuer le streaming normal
        chunk_count = 0
        start_streaming_time = asyncio.get_event_loop().time()

        while True:
            chunk = await process.stdout.read(256 * 1024)  # 256KB chunks
            if not chunk:
                break
            chunk_count += 1
            chunk_size = len(chunk)
            total_bytes_sent += chunk_size

            # Log plus fréquent pour le débogage
            if chunk_count <= 10:  # Les 10 premiers chunks
                logger.info(
                    f"Chunk {chunk_count}: {chunk_size} bytes envoyé (total: {total_bytes_sent/1024:.1f} KB)"
                )
            elif chunk_count % 50 == 0:  # Puis tous les 50 chunks (~12.5MB)
                elapsed = asyncio.get_event_loop().time() - start_streaming_time
                speed = total_bytes_sent / elapsed / 1024 if elapsed > 0 else 0
                logger.info(
                    f"Chunk {chunk_count}: total {total_bytes_sent/1024/1024:.1f} MB envoyé, vitesse: {speed:.1f} KB/s"
                )

            yield chunk

        # Statistiques finales
        total_time = asyncio.get_event_loop().time() - start_streaming_time
        avg_speed = total_bytes_sent / total_time / 1024 if total_time > 0 else 0

        logger.info("=== FIN STREAMING ===")
        logger.info(f"Total chunks envoyés: {chunk_count}")
        logger.info(
            f"Total bytes envoyés: {total_bytes_sent} ({total_bytes_sent/1024/1024:.2f} MB)"
        )
        logger.info(f"Temps total: {total_time:.1f}s")
        logger.info(f"Vitesse moyenne: {avg_speed:.1f} KB/s")

        # Attendre la fin du processus
        return_code = await process.wait()
        logger.info(f"FFmpeg terminé avec code: {return_code}")

        # Récupérer et logger les dernières erreurs stderr
        try:
            stderr_final = await asyncio.wait_for(stderr_task, timeout=5)
            if stderr_final:
                logger.info(
                    f"FFmpeg stderr final: {stderr_final[-500:]}"
                )  # Derniers 500 chars
        except asyncio.TimeoutError:
            logger.warning("Timeout lors de la récupération du stderr final")

    except Exception as e:
        logger.error(f"Erreur lors du streaming progressif: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(500, f"Erreur de streaming: {str(e)}")


async def handle_range_request(workout_data, range_header: str):
    """
    Gère les Range Requests pour permettre le seeking dans la vidéo
    même pendant la génération.

    Note: Implémentation simplifiée pour le moment.
    Une version complète nécessiterait de gérer les ranges partiels.
    """
    logger.info(f"Traitement Range Request: {range_header}")

    # Pour le moment, on retourne une réponse 416 (Range Not Satisfiable)
    # car l'implémentation complète des Range Requests nécessite de connaître
    # la taille finale du fichier et de pouvoir accéder à des portions spécifiques
    raise HTTPException(
        416,
        "Range requests not yet supported during generation",
        headers={"Content-Range": "bytes */0"},
    )


def build_optimized_ffmpeg_command(workout_data):
    """
    Construit une commande FFmpeg optimisée pour le streaming progressif.
    Utilise OptimizedVideoService pour la construction de la commande.
    """
    import tempfile
    import os
    from pathlib import Path

    # Récupérer les exercices depuis workout_data (dictionnaire)
    exercises = workout_data.get("exercises", [])
    config = workout_data.get("config", None)

    if not exercises or not config:
        raise HTTPException(500, "Données de workout incomplètes")

    # Utiliser le service vidéo optimisé
    project_root = Path(__file__).parent.parent.parent
    video_service = OptimizedVideoService(project_root=project_root)

    # Préparer les chemins des vidéos et créer le fichier de concat
    temp_dir = Path(tempfile.gettempdir())
    concat_file = temp_dir / f"concat_{os.getpid()}.txt"

    video_paths = []
    for exercise in exercises:
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

    # Construire la commande FFmpeg pour streaming vers stdout
    speed = video_service.get_speed_multiplier(config.intensity)

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
            "mp4",
            "-an",
            "pipe:1",
        ]
    )

    return command


def estimate_video_size(workout_data) -> int:
    """
    Estime la taille finale de la vidéo basée sur les exercices
    pour fournir un Content-Length approximatif.

    Cette estimation aide le navigateur à afficher une barre de progression.
    """
    try:
        # Estimation basique: ~2MB par minute de vidéo
        # Cette valeur peut être affinée basée sur les statistiques réelles
        duration_seconds = workout_data.get(
            "total_duration", 2400
        )  # défaut 40min = 2400s
        duration_minutes = duration_seconds / 60
        estimated_size = duration_minutes * 2 * 1024 * 1024  # 2MB par minute

        logger.debug(
            f"Taille estimée pour {duration_minutes}min: {estimated_size} bytes"
        )
        return estimated_size

    except Exception as e:
        logger.warning(f"Impossible d'estimer la taille: {e}")
        return 100 * 1024 * 1024  # 100MB par défaut
