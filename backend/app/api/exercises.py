"""API endpoints pour la gestion des exercices."""

import json
import os
import logging
from pathlib import Path
from typing import List, Optional
from functools import lru_cache

from fastapi import APIRouter, HTTPException
from supabase import create_client, Client

from ..models.exercise import Exercise

# Configuration du logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["exercises"])

# Configuration Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
logger.info(f"SUPABASE_URL : {SUPABASE_URL}")

SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Flag pour basculer entre JSON local et Supabase
USE_SUPABASE = True  # os.getenv("USE_SUPABASE", "false").lower() == "true"

# Chemin vers le fichier JSON des exercices (fallback)
EXERCISES_FILE = Path(__file__).parent.parent / "models" / "exercises.json"


@lru_cache()
def get_supabase_client() -> Optional[Client]:
    """
    Crée et retourne un client Supabase en cache

    Returns:
        Client Supabase ou None si non configuré
    """
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return None

    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def load_exercises_from_json() -> List[Exercise]:
    """
    Charge les exercices depuis le fichier JSON local.

    Returns:
        List[Exercise]: Liste des exercices validés par Pydantic

    Raises:
        HTTPException: Si le fichier n'existe pas ou est invalide
    """
    try:
        if not EXERCISES_FILE.exists():
            raise FileNotFoundError(
                f"Fichier exercises.json introuvable: {EXERCISES_FILE}"
            )

        with open(EXERCISES_FILE, "r", encoding="utf-8") as f:
            exercises_data = json.load(f)

        # Valider avec Pydantic
        exercises = [Exercise(**ex) for ex in exercises_data]
        return exercises

    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Erreur de parsing JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors du chargement des exercices: {str(e)}"
        )


def load_exercises_from_supabase() -> List[Exercise]:
    """
    Charge les exercices depuis Supabase PostgreSQL.

    Returns:
        List[Exercise]: Liste des exercices

    Raises:
        HTTPException: Si erreur de connexion ou de récupération
    """
    try:
        logger.info("Chargement exercices depuis Supabase")
        logger.debug(f"SUPABASE_URL: {SUPABASE_URL}")
        logger.debug(f"SUPABASE_ANON_KEY présent: {'✓' if SUPABASE_ANON_KEY else '✗'}")

        supabase = get_supabase_client()

        if not supabase:
            logger.error("Supabase client non configuré")
            raise HTTPException(
                status_code=500,
                detail="Supabase non configuré (SUPABASE_URL ou SUPABASE_ANON_KEY manquant)",
            )

        logger.info("Appel Supabase table('exercises').select('*')")
        # Récupérer tous les exercices
        response = supabase.table("exercises").select("*").execute()

        logger.debug(f"Réponse brute: {response}")
        logger.info(
            f"Nombre d'exercices trouvés: {len(response.data) if response.data else 0}"
        )

        if not response.data:
            logger.warning("Aucun exercice trouvé dans Supabase")
            return []

        # Mapper vers le modèle Exercise
        logger.info(f"Mapping de {len(response.data)} exercices")
        exercises = []
        for i, ex in enumerate(response.data):
            try:
                logger.debug(f"Mapping exercice {i+1}: {ex.get('name', 'Unknown')}")
                exercise = Exercise.from_supabase(ex)
                exercises.append(exercise)
            except Exception as mapping_error:
                logger.error(f"Erreur mapping exercice {i+1}: {str(mapping_error)}")
                logger.debug(f"Données exercice: {ex}")
                raise

        logger.info(f"✅ {len(exercises)} exercices chargés depuis Supabase")
        return exercises

    except Exception as e:
        logger.error(
            f"Erreur dans load_exercises_from_supabase: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du chargement depuis Supabase: {str(e)}",
        )


def load_exercises() -> List[Exercise]:
    """
    Charge les exercices depuis Supabase ou JSON selon la configuration.

    Returns:
        List[Exercise]: Liste des exercices
    """
    if USE_SUPABASE:
        return load_exercises_from_supabase()
    else:
        return load_exercises_from_json()


@router.get("/exercises", response_model=List[Exercise])
async def get_exercises() -> List[Exercise]:
    """
    Récupère la liste de tous les exercices disponibles.

    Returns:
        List[Exercise]: Liste des exercices avec leurs métadonnées

    Example response:
        ```json
        [
            {
                "name": "Push-ups",
                "description": "Pompes classiques...",
                "icon": "💪",
                "video_url": "https://...",
                "default_duration": 30,
                "difficulty": "medium",
                "has_jump": false,
                "access_tier": "free",
                "metadata": {
                    "muscles_targeted": ["chest", "triceps", "shoulders"],
                    "equipment_needed": [],
                    "calories_per_min": 7.0
                }
            }
        ]
        ```
    """
    return load_exercises()


@router.get("/exercises/{exercise_name}", response_model=Exercise)
async def get_exercise_by_name(exercise_name: str) -> Exercise:
    """
    Récupère un exercice spécifique par son nom.

    Args:
        exercise_name: Nom de l'exercice (case-insensitive)

    Returns:
        Exercise: L'exercice demandé

    Raises:
        HTTPException: 404 si l'exercice n'est pas trouvé
    """
    exercises = load_exercises()

    # Recherche insensible à la casse
    for exercise in exercises:
        if exercise.name.lower() == exercise_name.lower():
            return exercise

    raise HTTPException(
        status_code=404, detail=f"Exercice '{exercise_name}' non trouvé"
    )
