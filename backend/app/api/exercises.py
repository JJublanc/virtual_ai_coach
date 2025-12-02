"""API endpoints pour la gestion des exercices."""

import json
import os
import logging
from pathlib import Path
from typing import List, Optional
from functools import lru_cache

from fastapi import APIRouter, HTTPException, Response
from supabase import create_client, Client

from ..models.exercise import Exercise

from dotenv import load_dotenv

load_dotenv()

# Configuration du logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["exercises"])

# Configuration Supabase avec logs de debug détaillés
logger.info("=== DIAGNOSTIC VARIABLES D'ENVIRONNEMENT SUPABASE ===")

# Afficher TOUTES les variables d'environnement disponibles (pour debug)
logger.info("=== TOUTES LES VARIABLES D'ENVIRONNEMENT ===")
all_env_vars = dict(os.environ)
logger.info(f"Nombre total de variables: {len(all_env_vars)}")
for key in sorted(all_env_vars.keys()):
    if "KEY" in key or "PASSWORD" in key or "SECRET" in key:
        logger.info(f"{key} = [MASQUÉ]")
    else:
        logger.info(f"{key} = {all_env_vars[key][:100]}")

logger.info("=== VARIABLES SUPABASE SPÉCIFIQUES ===")
SUPABASE_URL = os.getenv("SUPABASE_URL")
logger.info(f"SUPABASE_URL : {SUPABASE_URL}")
logger.info(f"SUPABASE_URL type: {type(SUPABASE_URL)}")
logger.info(f"SUPABASE_URL length: {len(SUPABASE_URL) if SUPABASE_URL else 0}")

SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
logger.info(f"SUPABASE_ANON_KEY exists: {SUPABASE_ANON_KEY is not None}")
logger.info(
    f"SUPABASE_ANON_KEY length: {len(SUPABASE_ANON_KEY) if SUPABASE_ANON_KEY else 0}"
)

# Lister TOUTES les variables d'environnement qui commencent par SUPABASE
logger.info("=== RECHERCHE DE TOUTES LES VARIABLES SUPABASE* ===")
supabase_vars = {
    key: value for key, value in os.environ.items() if "SUPABASE" in key.upper()
}
logger.info(f"Variables trouvées avec 'SUPABASE' dans le nom: {len(supabase_vars)}")
for key, value in supabase_vars.items():
    # Masquer les clés sensibles mais montrer leur longueur
    if "KEY" in key or "PASSWORD" in key:
        logger.info(f"  {key} = [MASQUÉ] (length: {len(value)})")
    else:
        logger.info(f"  {key} = {value}")

logger.info("=== FIN DIAGNOSTIC ===")

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
    import time

    try:
        total_start = time.time()
        logger.info("=== DIAGNOSTIC PERFORMANCE SUPABASE ===")
        logger.info("Chargement exercices depuis Supabase")

        # Timing: Création client
        client_start = time.time()
        supabase = get_supabase_client()
        client_time = (time.time() - client_start) * 1000
        logger.info(f"⏱️ Création client Supabase: {client_time:.0f}ms")

        if not supabase:
            logger.error("Supabase client non configuré")
            raise HTTPException(
                status_code=500,
                detail="Supabase non configuré (SUPABASE_URL ou SUPABASE_ANON_KEY manquant)",
            )

        # Timing: Requête Supabase
        query_start = time.time()
        logger.info("Appel Supabase table('exercises').select('*')")
        response = supabase.table("exercises").select("*").execute()
        query_time = (time.time() - query_start) * 1000
        logger.info(f"⏱️ Requête Supabase: {query_time:.0f}ms")

        logger.info(
            f"Nombre d'exercices trouvés: {len(response.data) if response.data else 0}"
        )

        if not response.data:
            logger.warning("Aucun exercice trouvé dans Supabase")
            return []

        # Timing: Mapping
        mapping_start = time.time()
        logger.info(f"Mapping de {len(response.data)} exercices")
        exercises = []
        for i, ex in enumerate(response.data):
            try:
                exercise = Exercise.from_supabase(ex)
                exercises.append(exercise)
            except Exception as mapping_error:
                logger.error(f"Erreur mapping exercice {i+1}: {str(mapping_error)}")
                logger.debug(f"Données exercice: {ex}")
                raise
        mapping_time = (time.time() - mapping_start) * 1000
        logger.info(f"⏱️ Mapping exercices: {mapping_time:.0f}ms")

        total_time = (time.time() - total_start) * 1000
        logger.info(f"=== TOTAL: {total_time:.0f}ms ===")
        logger.info(
            f"  - Client: {client_time:.0f}ms ({client_time/total_time*100:.0f}%)"
        )
        logger.info(
            f"  - Requête: {query_time:.0f}ms ({query_time/total_time*100:.0f}%)"
        )
        logger.info(
            f"  - Mapping: {mapping_time:.0f}ms ({mapping_time/total_time*100:.0f}%)"
        )
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
async def get_exercises(response: Response) -> List[Exercise]:
    """
    Récupère la liste de tous les exercices disponibles.

    OPTIMISATION: Cache HTTP activé pour réduire la latence.
    Les exercices sont mis en cache pendant 1 heure côté navigateur.

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
    # OPTIMISATION: Ajouter headers de cache HTTP
    # Cache public pendant 1 heure (3600 secondes)
    response.headers[
        "Cache-Control"
    ] = "public, max-age=3600, stale-while-revalidate=86400"
    response.headers["ETag"] = "exercises-v1"

    # Log pour monitoring
    logger.debug("Headers de cache ajoutés: Cache-Control=public, max-age=3600")

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
