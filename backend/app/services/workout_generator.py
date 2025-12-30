"""Service de génération d'exercices pour les workouts.

Ce module fournit des fonctions pour générer automatiquement une liste d'exercices
aléatoires basée sur les critères de configuration d'un workout.

TODO: Migrer vers Supabase pour le chargement des exercices
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Optional
from uuid import uuid4

from ..models.config import WorkoutConfig
from ..models.exercise import Exercise, Difficulty, Laterality
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


def find_exercise_by_id(
    exercise_id: str, exercises_pool: List[Exercise]
) -> Optional[Exercise]:
    """
    Trouve un exercice par son ID dans le pool.

    Args:
        exercise_id: UUID de l'exercice à trouver
        exercises_pool: Pool d'exercices disponibles

    Returns:
        L'exercice correspondant si trouvé, None sinon
    """
    for ex in exercises_pool:
        if str(ex.id) == exercise_id:
            return ex
    return None


def generate_random_exercises(
    exercises_pool: List[Exercise], count: int
) -> List[Exercise]:
    """
    Tire aléatoirement des exercices depuis un pool en évitant que le même exercice
    apparaisse parmi les 2 exercices précédents.

    Gestion de la latéralité :
    - Si un exercice "left" ou "right" est tiré, l'exercice suivant DOIT être son symétrique
    - Si un exercice latéral est tiré en dernière position, il est remplacé par un bilateral

    Args:
        exercises_pool: Pool d'exercices éligibles
        count: Nombre d'exercices à tirer

    Returns:
        List[Exercise]: Exercices sélectionnés avec alternance left/right garantie

    Note:
        Évite qu'un exercice soit identique à l'un des 2 exercices précédents.
        Si le pool contient moins de 3 exercices, cette contrainte peut être
        partiellement respectée selon le nombre d'exercices disponibles.

    Example:
        >>> pool = [ex1, ex2, ex3, ex4]
        >>> selected = generate_random_exercises(pool, count=10)
        >>> # Vérifier qu'aucun exercice n'est identique aux 2 précédents
        >>> for i in range(2, len(selected)):
        ...     assert selected[i].id != selected[i-1].id
        ...     assert selected[i].id != selected[i-2].id
    """
    if count <= 0:
        return []

    if not exercises_pool:
        raise ValueError("Le pool d'exercices est vide")

    # Si moins de 3 exercices dans le pool, on ne peut pas garantir la contrainte
    # mais on fait de notre mieux
    if len(exercises_pool) < 3:
        # Pour 1 ou 2 exercices, on alterne simplement
        if len(exercises_pool) == 1:
            return exercises_pool * count
        else:  # 2 exercices
            result = []
            for i in range(count):
                result.append(exercises_pool[i % 2])
            return result

    selected_exercises = []
    must_use_symmetric = (
        False  # Flag pour forcer l'utilisation d'un exercice symétrique
    )
    expected_exercise = None  # L'exercice symétrique attendu

    for i in range(count):
        # Si on doit utiliser un exercice symétrique
        if must_use_symmetric and expected_exercise:
            exercise = expected_exercise
            must_use_symmetric = False
            expected_exercise = None
        else:
            if i < 2:
                # Pour les 2 premiers exercices : tirage aléatoire simple
                # mais on évite quand même le précédent si i == 1
                if i == 0:
                    exercise = random.choice(exercises_pool)
                else:  # i == 1
                    previous = selected_exercises[0]
                    available_pool = [
                        ex for ex in exercises_pool if ex.id != previous.id
                    ]
                    exercise = random.choice(available_pool)
            else:
                # Pour les exercices suivants : éviter les 2 précédents
                prev_1 = selected_exercises[-1]
                prev_2 = selected_exercises[-2]

                # Créer un pool sans les 2 exercices précédents
                available_pool = [
                    ex
                    for ex in exercises_pool
                    if ex.id != prev_1.id and ex.id != prev_2.id
                ]

                # Tirer un exercice du pool filtré
                exercise = random.choice(available_pool)

        # Vérifier si l'exercice a une latéralité left ou right
        if exercise.metadata and exercise.metadata.laterality in [
            Laterality.LEFT,
            Laterality.RIGHT,
        ]:
            # Si c'est le dernier exercice, le remplacer par un bilateral
            if i == count - 1:
                # Chercher un exercice bilateral
                bilateral_pool = [
                    ex
                    for ex in exercises_pool
                    if not ex.metadata or ex.metadata.laterality == Laterality.BILATERAL
                ]

                # Exclure aussi les 2 précédents si possible
                if i >= 2:
                    prev_1 = selected_exercises[-1]
                    prev_2 = selected_exercises[-2]
                    bilateral_pool = [
                        ex
                        for ex in bilateral_pool
                        if ex.id != prev_1.id and ex.id != prev_2.id
                    ]
                elif i == 1:
                    prev_1 = selected_exercises[-1]
                    bilateral_pool = [ex for ex in bilateral_pool if ex.id != prev_1.id]

                if bilateral_pool:
                    exercise = random.choice(bilateral_pool)
                # Sinon, garder l'exercice même s'il est latéral
            else:
                # Chercher l'exercice symétrique via symmetric_exercise_id
                if exercise.metadata.symmetric_exercise_id:
                    symmetric = find_exercise_by_id(
                        exercise.metadata.symmetric_exercise_id, exercises_pool
                    )
                    if symmetric:
                        must_use_symmetric = True
                        expected_exercise = symmetric

        selected_exercises.append(exercise)

    return selected_exercises


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

    # 2. Charger tous les exercices disponibles depuis Supabase
    from ..api.exercises import load_exercises

    all_exercises = load_exercises()

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


def generate_workout_with_intervals(
    exercises: List[Exercise], config: WorkoutConfig
) -> List[Dict]:
    """
    Génère la liste de WorkoutExercise en alternant exercices et breaks.

    Cette fonction crée la séquence complète d'un workout incluant :
    - Les exercices avec leur durée de travail (work_time)
    - Les périodes de repos (breaks) entre chaque exercice

    Args:
        exercises: Liste des exercices à inclure dans le workout
        config: Configuration du workout avec les intervals work_time/rest_time

    Returns:
        Liste de dictionnaires avec structure :
        [Exercice1, Break1, Exercice2, Break2, ...]

    Example:
        >>> exercises = [exercise1, exercise2]
        >>> config = WorkoutConfig(intervals={"work_time": 40, "rest_time": 20})
        >>> result = generate_workout_with_intervals(exercises, config)
        >>> len(result)
        3  # exercise1, break1, exercise2 (pas de break après le dernier)
    """
    work_time = config.intervals.get("work_time", 40)
    rest_time = config.intervals.get("rest_time", 20)

    workout_items = []
    order = 0

    for idx, exercise in enumerate(exercises):
        # Ajouter l'exercice
        workout_items.append(
            {
                "name": exercise.name,
                "description": exercise.description or f"Exercice {exercise.name}",
                "icon": getattr(exercise, "icon", "🏋️"),
                "duration": work_time,
                "order": order,
                "is_break": False,
                "exercise_id": exercise.id,
            }
        )
        order += 1

        # Ajouter un break (sauf après le dernier exercice)
        if idx < len(exercises) - 1:
            workout_items.append(
                {
                    "name": "Break",
                    "description": "Période de récupération",
                    "icon": "⏸️",
                    "duration": rest_time,
                    "order": order,
                    "is_break": True,
                    "exercise_id": "break",
                }
            )
            order += 1

    return workout_items
