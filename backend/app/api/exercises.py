"""API endpoints pour la gestion des exercices."""

import json
import os
from pathlib import Path
from typing import List, Optional
from functools import lru_cache

from fastapi import APIRouter, HTTPException
from supabase import create_client, Client

from ..models.exercise import Exercise

router = APIRouter(prefix="/api", tags=["exercises"])

# Configuration Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Flag pour basculer entre JSON local et Supabase
USE_SUPABASE = os.getenv("USE_SUPABASE", "false").lower() == "true"

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
        supabase = get_supabase_client()

        if not supabase:
            raise HTTPException(
                status_code=500,
                detail="Supabase non configuré (SUPABASE_URL ou SUPABASE_ANON_KEY manquant)",
            )

        # Récupérer tous les exercices
        response = supabase.table("exercises").select("*").execute()

        if not response.data:
            return []

        # Mapper vers le modèle Exercise
        exercises = [Exercise.from_supabase(ex) for ex in response.data]
        return exercises

    except Exception as e:
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
