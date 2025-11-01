"""Service de génération d'exercices pour les workouts.

Ce module fournit des fonctions pour générer automatiquement une liste d'exercices
aléatoires basée sur les critères de configuration d'un workout.

TODO: Migrer vers Supabase pour le chargement des exercices
"""

import json
import random
from pathlib import Path
from typing import List
from uuid import uuid4

from ..models.exercise import Exercise, Difficulty
from ..models.workout import Workout, WorkoutExercise


# Chemin vers le fichier JSON des exercices
EXERCISES_FILE = Path(__file__).parent.parent / "models" / "exercises.json"


def load_exercises_from_json() -> List[Exercise]:
    """
    Charge tous les exercices depuis le fichier exercises.json.

    Returns:
        List[Exercise]: Liste complète des exercices validés par Pydantic

    Raises:
        FileNotFoundError: Si le fichier exercises.json n'existe pas
        ValueError: Si le JSON est invalide ou la validation Pydantic échoue

    Example:
        >>> exercises = load_exercises_from_json()
        >>> len(exercises) > 0
        True

    Note:
        TODO: Remplacer par une requête Supabase dans une version future
        async def load_exercises_from_db() -> List[Exercise]:
            supabase = get_supabase_client()
            response = await supabase.table('exercises').select('*').execute()
            return [Exercise(**ex) for ex in response.data]
    """
    try:
        if not EXERCISES_FILE.exists():
            raise FileNotFoundError(
                f"Fichier exercises.json introuvable: {EXERCISES_FILE}"
            )

        with open(EXERCISES_FILE, "r", encoding="utf-8") as f:
            exercises_data = json.load(f)

        # Générer des UUID pour les exercices qui n'en ont pas
        exercises = []
        for ex_data in exercises_data:
            if "id" not in ex_data or ex_data["id"] is None:
                ex_data["id"] = str(uuid4())
            exercises.append(Exercise(**ex_data))

        return exercises

    except FileNotFoundError:
        raise
    except json.JSONDecodeError as e:
        raise ValueError(f"Erreur de parsing JSON dans exercises.json: {str(e)}")
    except Exception as e:
        raise ValueError(f"Erreur lors du chargement des exercices: {str(e)}")


def filter_exercises(
    exercises: List[Exercise], no_jump: bool, intensity_levels: List[Difficulty]
) -> List[Exercise]:
    """
    Filtre les exercices selon les critères de configuration.

    Args:
        exercises: Liste complète des exercices disponibles
        no_jump: Si True, exclut les exercices avec has_jump=True
        intensity_levels: Liste des niveaux de difficulté acceptés

    Returns:
        List[Exercise]: Exercices correspondant aux critères

    Raises:
        ValueError: Si aucun exercice ne correspond aux critères de filtrage

    Example:
        >>> exercises = [
        ...     Exercise(name="Push-ups", has_jump=False, difficulty=Difficulty.MEDIUM),
        ...     Exercise(name="Burpees", has_jump=True, difficulty=Difficulty.HARD)
        ... ]
        >>> filtered = filter_exercises(exercises, no_jump=True, intensity_levels=[Difficulty.MEDIUM])
        >>> len(filtered)
        1
        >>> filtered[0].name
        'Push-ups'
    """
    filtered = exercises

    # Filtrage par sauts
    if no_jump:
        filtered = [ex for ex in filtered if not ex.has_jump]

    # Filtrage par difficulté
    if intensity_levels:
        filtered = [ex for ex in filtered if ex.difficulty in intensity_levels]

    # Validation du pool résultant
    if not filtered:
        raise ValueError(
            f"Aucun exercice trouvé pour les critères : "
            f"no_jump={no_jump}, "
            f"intensity_levels={[level.value for level in intensity_levels]}"
        )

    return filtered


def generate_random_exercises(
    exercises_pool: List[Exercise], count: int
) -> List[Exercise]:
    """
    Tire aléatoirement avec remise des exercices depuis un pool.

    Args:
        exercises_pool: Pool d'exercices éligibles
        count: Nombre d'exercices à tirer

    Returns:
        List[Exercise]: Exercices sélectionnés (peut contenir des doublons)

    Note:
        Utilise random.choices() pour un tirage avec remise, permettant
        la répétition d'exercices. Ceci est important lorsque le pool
        d'exercices disponibles est plus petit que le nombre demandé.

    Example:
        >>> pool = [ex1, ex2, ex3]
        >>> selected = generate_random_exercises(pool, count=5)
        >>> len(selected)
        5
        >>> # Peut contenir des doublons car tirage avec remise
    """
    if count <= 0:
        return []

    if not exercises_pool:
        raise ValueError("Le pool d'exercices est vide")

    # Tirage aléatoire avec remise (permet les doublons)
    return random.choices(exercises_pool, k=count)


def generate_workout_exercises(workout: Workout) -> List[WorkoutExercise]:
    """
    Génère la liste complète des exercices pour un workout.

    Cette fonction principale orchestre tout le processus de génération :
    1. Valide les entrées (config, duration)
    2. Charge tous les exercices disponibles
    3. Filtre selon les critères (no_jump, intensity_levels)
    4. Calcule le nombre d'exercices nécessaires
    5. Tire aléatoirement avec remise
    6. Crée les WorkoutExercise avec order_index séquentiel

    Args:
        workout: Objet Workout avec config et total_duration remplis

    Returns:
        List[WorkoutExercise]: Liste ordonnée des exercices pour le workout

    Raises:
        ValueError: Si la config est manquante, la durée invalide,
                   ou si aucun exercice ne correspond aux critères
        FileNotFoundError: Si le fichier exercises.json n'existe pas

    Example:
        >>> workout = Workout(
        ...     total_duration=600,  # 10 minutes
        ...     config=WorkoutConfig(
        ...         no_jump=True,
        ...         exercice_intensity_levels=[Difficulty.EASY, Difficulty.MEDIUM]
        ...     )
        ... )
        >>> exercises = generate_workout_exercises(workout)
        >>> len(exercises)
        10
        >>> exercises[0].order_index
        0
        >>> exercises[-1].order_index
        9

    Note:
        Le calcul du nombre d'exercices suit la règle :
        1 exercice par minute (intervals de ~60s avec work_time + rest_time)
        Donc nb_exercises = total_duration // 60
    """
    # 1. Validation des entrées
    if not workout.config:
        raise ValueError("Le workout doit avoir une configuration (config)")

    if not workout.total_duration or workout.total_duration <= 0:
        raise ValueError(
            f"total_duration doit être positif, reçu: {workout.total_duration}"
        )

    # 2. Charger tous les exercices disponibles
    all_exercises = load_exercises_from_json()

    # 3. Filtrer selon les critères de configuration
    filtered_exercises = filter_exercises(
        exercises=all_exercises,
        no_jump=workout.config.no_jump,
        intensity_levels=workout.config.exercice_intensity_levels,
    )

    # 4. Calculer le nombre d'exercices nécessaires
    # 1 exercice par minute (intervals de ~60s)
    num_exercises = workout.total_duration // 60

    if num_exercises <= 0:
        raise ValueError(
            f"La durée est trop courte pour générer des exercices. "
            f"Minimum 60 secondes requis, reçu: {workout.total_duration}s"
        )

    # 5. Tirer aléatoirement avec remise
    selected_exercises = generate_random_exercises(
        exercises_pool=filtered_exercises, count=num_exercises
    )

    # 6. Créer les WorkoutExercise avec order_index séquentiel
    workout_exercises = []
    for index, exercise in enumerate(selected_exercises):
        workout_exercise = WorkoutExercise(
            exercise_id=exercise.id,
            order_index=index,
            custom_duration=None,  # Utiliser default_duration de l'exercice
        )
        workout_exercises.append(workout_exercise)

    return workout_exercises
