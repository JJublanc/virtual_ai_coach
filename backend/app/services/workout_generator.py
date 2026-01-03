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
from ..models.exercise import Exercise, Difficulty, Laterality, ExerciseTheme
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
    Point d'entrée principal pour la génération d'exercices.

    Route vers l'algorithme approprié :
    - Génération par blocs si use_block_structure=True
    - Génération classique sinon

    Args:
        workout: Objet Workout avec config et total_duration remplis

    Returns:
        List[WorkoutExercise]: Liste ordonnée des exercices pour le workout

    Raises:
        ValueError: Si la config est manquante, la durée invalide,
                   ou si aucun exercice ne correspond aux critères

    Example:
        >>> # Génération classique
        >>> workout = Workout(
        ...     total_duration=600,
        ...     config=WorkoutConfig(no_jump=True)
        ... )
        >>> exercises = generate_workout_exercises(workout)

        >>> # Génération par blocs
        >>> workout = Workout(
        ...     total_duration=1800,
        ...     config=WorkoutConfig(
        ...         use_block_structure=True,
        ...         block_config=BlockConfig(themes=[ExerciseTheme.ABS, ExerciseTheme.CARDIO])
        ...     )
        ... )
        >>> exercises = generate_workout_exercises(workout)
    """
    # Validation de base
    if not workout.config:
        raise ValueError("Le workout doit avoir une configuration")

    if not workout.total_duration or workout.total_duration <= 0:
        raise ValueError(f"total_duration invalide: {workout.total_duration}")

    # Router vers l'algorithme approprié
    if workout.config.use_block_structure:
        return generate_workout_with_blocks(workout)
    else:
        return _generate_workout_classic(workout)


def _generate_workout_classic(workout: Workout) -> List[WorkoutExercise]:
    """
    Génère la liste complète des exercices pour un workout (algorithme classique).

    Cette fonction orchestre le processus de génération classique :
    1. Charge tous les exercices disponibles
    2. Filtre selon les critères (no_jump, intensity_levels)
    3. Calcule le nombre d'exercices nécessaires
    4. Tire aléatoirement avec remise
    5. Crée les WorkoutExercise avec order_index séquentiel

    Args:
        workout: Objet Workout avec config et total_duration remplis

    Returns:
        List[WorkoutExercise]: Liste ordonnée des exercices pour le workout

    Raises:
        ValueError: Si aucun exercice ne correspond aux critères

    Note:
        Le calcul du nombre d'exercices suit la règle :
        1 exercice par minute (intervals de ~60s avec work_time + rest_time)
        Donc nb_exercises = total_duration // 60
    """
    # 1. Charger tous les exercices disponibles depuis Supabase
    from ..api.exercises import load_exercises

    all_exercises = load_exercises()

    # 2. Filtrer selon les critères de configuration
    filtered_exercises = filter_exercises(
        exercises=all_exercises,
        no_jump=workout.config.no_jump,
        intensity_levels=workout.config.exercice_intensity_levels,
    )

    # 3. Calculer le nombre d'exercices nécessaires
    # 1 exercice par minute (intervals de ~60s)
    num_exercises = workout.total_duration // 60

    if num_exercises <= 0:
        raise ValueError(
            f"La durée est trop courte pour générer des exercices. "
            f"Minimum 60 secondes requis, reçu: {workout.total_duration}s"
        )

    # 4. Tirer aléatoirement avec remise
    selected_exercises = generate_random_exercises(
        exercises_pool=filtered_exercises, count=num_exercises
    )

    # 5. Créer les WorkoutExercise avec order_index séquentiel
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


def filter_exercises_by_theme(
    exercises: List[Exercise], theme: ExerciseTheme
) -> List[Exercise]:
    """
    Filtre les exercices par thème.

    Un exercice est inclus si :
    - Il a exactement ce thème
    - Il a ce thème parmi plusieurs
    - Il est FULL_BODY (compatible avec tous les blocs)

    Args:
        exercises: Pool d'exercices filtrés
        theme: Thème recherché

    Returns:
        Liste d'exercices correspondant au thème

    Example:
        >>> abs_exercises = filter_exercises_by_theme(exercises, ExerciseTheme.ABS)
        >>> # Retourne tous les exercices avec theme ABS ou FULL_BODY
    """
    filtered = []
    for ex in exercises:
        if not ex.metadata or not ex.metadata.themes:
            # Si pas de thèmes définis, considérer comme FULL_BODY
            if theme == ExerciseTheme.FULL_BODY:
                filtered.append(ex)
        else:
            # Inclure si le thème est dans la liste OU si c'est un FULL_BODY
            if (
                theme in ex.metadata.themes
                or ExerciseTheme.FULL_BODY in ex.metadata.themes
            ):
                filtered.append(ex)

    return filtered


def select_diverse_exercises(exercises: List[Exercise], count: int) -> List[Exercise]:
    """
    Sélectionne N exercices différents en maximisant la diversité.

    Critères de sélection :
    - Tous les exercices doivent être différents
    - Éviter les exercices trop similaires (même muscles principaux)
    - Respecter la latéralité (alternance left/right)

    Args:
        exercises: Pool d'exercices du thème
        count: Nombre d'exercices à sélectionner

    Returns:
        Liste de N exercices différents

    Raises:
        ValueError: Si pas assez d'exercices disponibles

    Example:
        >>> selected = select_diverse_exercises(abs_exercises, count=3)
        >>> len(selected)
        3
        >>> # Les 3 exercices sont différents
    """
    if len(exercises) < count:
        raise ValueError(
            f"Pas assez d'exercices pour le thème. "
            f"Requis: {count}, Disponibles: {len(exercises)}"
        )

    selected = []
    available = exercises.copy()

    while len(selected) < count:
        # Éviter les exercices avec muscles trop similaires aux précédents
        if selected:
            last_muscles = set(selected[-1].metadata.muscles_targeted or [])
            # Prioriser les exercices avec muscles différents
            different_muscle_exercises = [
                ex
                for ex in available
                if not (set(ex.metadata.muscles_targeted or []) & last_muscles)
            ]
            if different_muscle_exercises:
                pool = different_muscle_exercises
            else:
                pool = available
        else:
            pool = available

        # Sélection aléatoire
        exercise = random.choice(pool)
        selected.append(exercise)

        # Retirer l'exercice sélectionné du pool
        available = [ex for ex in available if ex.id != exercise.id]

        # Gérer la latéralité
        if exercise.metadata and exercise.metadata.laterality in [
            Laterality.LEFT,
            Laterality.RIGHT,
        ]:
            # Ajouter automatiquement l'exercice symétrique si disponible
            if exercise.metadata.symmetric_exercise_id and len(selected) < count:
                symmetric = find_exercise_by_id(
                    exercise.metadata.symmetric_exercise_id, available
                )
                if symmetric:
                    selected.append(symmetric)
                    available = [ex for ex in available if ex.id != symmetric.id]

    return selected[:count]


def select_finisher_exercises(
    exercises: List[Exercise], themes: List[ExerciseTheme], count: int
) -> List[Exercise]:
    """
    Sélectionne plusieurs exercices intenses pour finir le workout.

    Les finishers sont sélectionnés pour maximiser l'intensité finale :
    - Difficulté HARD de préférence
    - Thèmes CARDIO ou FULL_BODY privilégiés
    - has_jump=True privilégié (sauf si no_jump actif)
    - Diversité entre les finishers

    Args:
        exercises: Pool d'exercices filtrés
        themes: Thèmes autorisés pour les finishers
        count: Nombre de finishers à sélectionner

    Returns:
        Liste de finishers

    Raises:
        ValueError: Si pas assez d'exercices disponibles

    Example:
        >>> finishers = select_finisher_exercises(
        ...     exercises,
        ...     themes=[ExerciseTheme.CARDIO, ExerciseTheme.FULL_BODY],
        ...     count=3
        ... )
        >>> len(finishers)
        3
    """
    # Filtrer par thèmes autorisés
    finisher_pool = []
    for theme in themes:
        finisher_pool.extend(filter_exercises_by_theme(exercises, theme))

    # Retirer les doublons
    finisher_pool = list({ex.id: ex for ex in finisher_pool}.values())

    if len(finisher_pool) < count:
        raise ValueError(
            f"Pas assez d'exercices pour les finishers. "
            f"Requis: {count}, Disponibles: {len(finisher_pool)}"
        )

    # Prioriser HARD
    hard_exercises = [ex for ex in finisher_pool if ex.difficulty == Difficulty.HARD]
    if hard_exercises and len(hard_exercises) >= count:
        finisher_pool = hard_exercises

    # Prioriser has_jump si disponible
    jump_exercises = [ex for ex in finisher_pool if ex.has_jump]
    if jump_exercises and len(jump_exercises) >= count:
        finisher_pool = jump_exercises

    # Sélectionner de manière diversifiée
    selected = []
    available = finisher_pool.copy()

    for _ in range(count):
        if not available:
            # Si on manque d'options, réinitialiser le pool
            available = finisher_pool.copy()

        exercise = random.choice(available)
        selected.append(exercise)
        # Retirer pour éviter les répétitions immédiates
        available = [ex for ex in available if ex.id != exercise.id]

    return selected


def generate_workout_with_blocks(workout: Workout) -> List[WorkoutExercise]:
    """
    Génère un workout structuré en blocs thématiques répétitifs.

    Cette fonction organise les exercices en blocs thématiques où chaque bloc :
    - Contient N exercices différents du même thème
    - Est répété X fois
    - Le temps restant est rempli avec des finishers

    Args:
        workout: Objet Workout avec config.use_block_structure=True

    Returns:
        List[WorkoutExercise]: Liste ordonnée des exercices avec blocs

    Raises:
        ValueError: Si duration < 10 min ou config invalide

    Example:
        >>> workout = Workout(
        ...     total_duration=1800,  # 30 minutes
        ...     config=WorkoutConfig(
        ...         use_block_structure=True,
        ...         block_config=BlockConfig(
        ...             themes=[ExerciseTheme.ABS, ExerciseTheme.UPPER_BODY, ExerciseTheme.CARDIO],
        ...             exercises_per_block=3,
        ...             repetitions_per_block=3,
        ...             fill_remaining_with_finishers=True
        ...         )
        ...     )
        ... )
        >>> exercises = generate_workout_with_blocks(workout)
        >>> # Résultat : 3 blocs × 3 exercices × 3 répétitions + finishers = 30 exercices
    """
    # 1. Validation
    if not workout.config.use_block_structure:
        raise ValueError("use_block_structure doit être True")

    if workout.total_duration < 600:
        raise ValueError("La durée minimum pour les blocs est de 10 minutes (600s)")

    block_config = workout.config.block_config
    if not block_config:
        raise ValueError("block_config est requis quand use_block_structure=True")

    # 2. Charger et filtrer les exercices
    from ..api.exercises import load_exercises

    all_exercises = load_exercises()
    filtered_exercises = filter_exercises(
        exercises=all_exercises,
        no_jump=workout.config.no_jump,
        intensity_levels=workout.config.exercice_intensity_levels,
    )

    # 3. Calculer le nombre total d'exercices possibles dans la session
    work_time = workout.config.intervals.get("work_time", 40)
    rest_time = workout.config.intervals.get("rest_time", 20)
    interval_duration = work_time + rest_time  # ex: 60s

    total_exercises_capacity = workout.total_duration // interval_duration

    # 4. Calculer combien d'exercices pour les blocs thématiques
    num_blocks = len(block_config.themes)
    exercises_per_complete_block = (
        block_config.exercises_per_block * block_config.repetitions_per_block
    )
    total_exercises_in_blocks = num_blocks * exercises_per_complete_block

    # 5. Vérifier que les blocs rentrent dans la durée
    if total_exercises_in_blocks > total_exercises_capacity:
        raise ValueError(
            f"Configuration impossible : les blocs nécessitent {total_exercises_in_blocks} exercices "
            f"mais la durée permet seulement {total_exercises_capacity} exercices. "
            f"Réduisez le nombre de blocs, d'exercices par bloc, ou de répétitions."
        )

    # 6. Générer chaque bloc
    workout_exercises = []
    order_index = 0

    for theme in block_config.themes:
        # Filtrer les exercices par thème
        theme_exercises = filter_exercises_by_theme(filtered_exercises, theme)

        # Sélectionner N exercices différents pour ce bloc
        block_exercises = select_diverse_exercises(
            theme_exercises, count=block_config.exercises_per_block
        )

        # Répéter le bloc X fois
        for rep in range(block_config.repetitions_per_block):
            for exercise in block_exercises:
                workout_exercise = WorkoutExercise(
                    exercise_id=exercise.id,
                    order_index=order_index,
                    custom_duration=None,
                )
                workout_exercises.append(workout_exercise)
                order_index += 1

    # 7. Remplir le temps restant avec des finishers
    exercises_remaining = total_exercises_capacity - len(workout_exercises)

    if block_config.fill_remaining_with_finishers and exercises_remaining > 0:
        finishers = select_finisher_exercises(
            filtered_exercises,
            themes=block_config.finisher_themes,
            count=exercises_remaining,
        )

        for finisher in finishers:
            workout_exercises.append(
                WorkoutExercise(
                    exercise_id=finisher.id,
                    order_index=order_index,
                    custom_duration=None,
                )
            )
            order_index += 1

    return workout_exercises
