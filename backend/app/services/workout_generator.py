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
    exercises: List[Exercise],
    no_jump: bool,
    intensity_levels: List[Difficulty],
    exercise_type: Optional[str] = None,
) -> List[Exercise]:
    """
    Filtre les exercices selon les critères de configuration.

    Args:
        exercises: Liste complète des exercices disponibles
        no_jump: Si True, exclut les exercices avec has_jump=True
        intensity_levels: Liste des niveaux de difficulté acceptés
        exercise_type: Type d'exercice spécifique (burpee, jump, run, push_ups, plank, squat, crunch)

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

    # Filtrage par type d'exercice
    if exercise_type:
        filtered = [
            ex
            for ex in filtered
            if ex.metadata
            and hasattr(ex.metadata, "exercise_type")
            and ex.metadata.exercise_type == exercise_type
        ]

    # Filtrage par sauts
    if no_jump:
        filtered = [ex for ex in filtered if not ex.has_jump]

    # Filtrage par difficulté
    if intensity_levels:
        filtered = [ex for ex in filtered if ex.difficulty in intensity_levels]

    # Validation du pool résultant
    if not filtered:
        criteria = f"no_jump={no_jump}, intensity_levels={[level.value for level in intensity_levels]}"
        if exercise_type:
            criteria += f", exercise_type={exercise_type}"
        raise ValueError(f"Aucun exercice trouvé pour les critères : {criteria}")

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
    Tire aléatoirement des exercices depuis un pool SANS REMISE.

    Principe :
    - Tirage sans remise : un exercice tiré est retiré du pool temporaire
    - Quand le pool est vide, il est réinitialisé avec tous les exercices du pool initial
    - Les paires unilatérales (left/right) sont TOUJOURS ajoutées ensemble et comptent pour 2 exercices
    - La dernière position DOIT être un exercice bilatéral

    Gestion de la latéralité :
    - Si un exercice unilatéral (left/right) est tiré :
        * EN DERNIÈRE POSITION : on le rejette et on tire un exercice bilatéral
        * AUTRES POSITIONS : on ajoute immédiatement son symétrique et on retire les 2 du pool

    Args:
        exercises_pool: Pool d'exercices éligibles (pool initial)
        count: Nombre d'exercices à tirer

    Returns:
        List[Exercise]: Exercices sélectionnés (peut contenir des paires unilatérales)

    Example:
        >>> pool = [ex1_bilateral, ex2_left, ex2_right, ex3_bilateral]
        >>> selected = generate_random_exercises(pool, count=10)
        >>> # Les exercices ne se répètent pas tant que le pool n'est pas épuisé
        >>> # Les paires left/right sont toujours consécutives
    """
    if count <= 0:
        return []

    if not exercises_pool:
        raise ValueError("Le pool d'exercices est vide")

    # Pool initial (référence pour réinitialisation)
    initial_pool = exercises_pool.copy()

    # Pool disponible (sera modifié au fil des tirages)
    available_pool = exercises_pool.copy()

    selected_exercises = []

    while len(selected_exercises) < count:
        # Réinitialiser le pool s'il est vide
        if not available_pool:
            available_pool = initial_pool.copy()

        # Calculer combien d'exercices il reste à tirer
        remaining = count - len(selected_exercises)

        # Si c'est la dernière position, on doit tirer un exercice bilatéral
        if remaining == 1:
            # Filtrer pour ne garder que les exercices bilatéraux
            bilateral_pool = [
                ex
                for ex in available_pool
                if not ex.metadata or ex.metadata.laterality == Laterality.BILATERAL
            ]

            # Si aucun exercice bilatéral disponible, réinitialiser et filtrer à nouveau
            if not bilateral_pool:
                available_pool = initial_pool.copy()
                bilateral_pool = [
                    ex
                    for ex in available_pool
                    if not ex.metadata or ex.metadata.laterality == Laterality.BILATERAL
                ]

            # Si toujours aucun exercice bilatéral, prendre n'importe lequel
            if not bilateral_pool:
                bilateral_pool = available_pool

            exercise = random.choice(bilateral_pool)
            selected_exercises.append(exercise)

            # Retirer du pool disponible
            available_pool = [ex for ex in available_pool if ex.id != exercise.id]

        else:
            # Tirer un exercice aléatoire
            exercise = random.choice(available_pool)

            # Vérifier si c'est un exercice unilatéral
            if exercise.metadata and exercise.metadata.laterality in [
                Laterality.LEFT,
                Laterality.RIGHT,
            ]:
                # Si c'est un unilatéral, on doit aussi ajouter son symétrique
                # MAIS seulement s'il reste au moins 2 places
                if remaining >= 2:
                    # Trouver l'exercice symétrique
                    symmetric = None
                    if exercise.metadata.symmetric_exercise_id:
                        symmetric = find_exercise_by_id(
                            exercise.metadata.symmetric_exercise_id, available_pool
                        )

                        # Si le symétrique n'est pas dans le pool, le chercher dans le pool initial
                        if not symmetric:
                            symmetric = find_exercise_by_id(
                                exercise.metadata.symmetric_exercise_id, initial_pool
                            )

                    if symmetric:
                        # Ajouter les deux exercices (la paire complète)
                        selected_exercises.append(exercise)
                        selected_exercises.append(symmetric)

                        # Retirer les deux du pool disponible
                        available_pool = [
                            ex
                            for ex in available_pool
                            if ex.id != exercise.id and ex.id != symmetric.id
                        ]
                    else:
                        # Pas de symétrique trouvé, ajouter juste l'exercice
                        selected_exercises.append(exercise)
                        available_pool = [
                            ex for ex in available_pool if ex.id != exercise.id
                        ]
                else:
                    # Il ne reste qu'une place mais on a tiré un unilatéral
                    # On le rejette et on tire un bilatéral
                    bilateral_pool = [
                        ex
                        for ex in available_pool
                        if not ex.metadata
                        or ex.metadata.laterality == Laterality.BILATERAL
                    ]

                    if bilateral_pool:
                        exercise = random.choice(bilateral_pool)
                    # Sinon on garde l'exercice unilatéral tiré

                    selected_exercises.append(exercise)
                    available_pool = [
                        ex for ex in available_pool if ex.id != exercise.id
                    ]
            else:
                # C'est un exercice bilatéral, on l'ajoute simplement
                selected_exercises.append(exercise)

                # Retirer du pool disponible
                available_pool = [ex for ex in available_pool if ex.id != exercise.id]

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
    2. Filtre selon les critères (no_jump, intensity_levels, exercise_type)
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
        exercise_type=workout.config.exercise_type,
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
    Génère la liste de segments d'overlay synchronisés avec la timeline vidéo réelle.

    IMPORTANT : Chaque exercice dans la vidéo dure work_time + rest_time (ex: 40 + 20 = 60s).
    Les overlays créent visuellement les temps de pause et les previews.

    Timeline réelle pour work_time=40s, rest_time=20s (exercices de 60s chacun) :

    EXERCICE 1 (vidéo 0-60s) :
    - 0-5s : Warning overlay
    - 5-45s : No overlay (40s d'exercice visible)
    - 45-60s : Break classic overlay (15s)

    EXERCICE 2 (vidéo 60-120s) :
    - 60-65s : Break transparent overlay (5s) - preview, vidéo visible dessous
    - 65-105s : No overlay (40s d'exercice visible)
    - 105-120s : Break classic overlay (15s)

    EXERCICE 3 (vidéo 120-180s) :
    - 120-125s : Break transparent overlay (5s)
    - 125-165s : No overlay (40s d'exercice visible)
    - 165-180s : Break classic overlay (15s)

    DERNIER EXERCICE :
    - 0-5s : Preview overlay
    - 5-45s : No overlay (40s)
    - 45-60s : rien (fin du workout)

    Args:
        exercises: Liste des exercices à inclure dans le workout
        config: Configuration du workout avec les intervals work_time/rest_time

    Returns:
        Liste de dictionnaires avec structure détaillée des overlays alignés sur la vidéo

    Example:
        >>> exercises = [exercise1, exercise2, exercise3]
        >>> config = WorkoutConfig(intervals={"work_time": 40, "rest_time": 20})
        >>> result = generate_workout_with_intervals(exercises, config)
        >>> # Total durée = 180s (3 exercices × 60s chacun)
    """
    work_time = config.intervals.get("work_time", 40)
    rest_time = config.intervals.get("rest_time", 20)

    PREVIEW_DURATION = 5  # Durée de la preview transparente
    WARNING_DURATION = 5  # Durée du warning initial
    BREAK_CLASSIC_DURATION = rest_time - PREVIEW_DURATION  # 20 - 5 = 15s

    workout_items = []
    order = 0

    for idx, exercise in enumerate(exercises):
        is_first = idx == 0
        is_last = idx == len(exercises) - 1

        if is_first:
            # EXERCICE 1 : Warning (5s) + No overlay (40s) + Break classic (15s)
            workout_items.append(
                {
                    "name": "Get Ready!",
                    "description": f"Préparez-vous pour {exercise.name}",
                    "icon": "⚠️",
                    "duration": WARNING_DURATION,
                    "order": order,
                    "overlay_type": "warning",
                    "is_break": False,
                    "exercise_id": exercise.id,
                    "next_exercise_name": exercise.name,
                }
            )
            order += 1

            workout_items.append(
                {
                    "name": exercise.name,
                    "description": exercise.description or f"Exercice {exercise.name}",
                    "icon": getattr(exercise, "icon", "🏋️"),
                    "duration": work_time,
                    "order": order,
                    "overlay_type": "none",
                    "is_break": False,
                    "exercise_id": exercise.id,
                }
            )
            order += 1

            # Break classic sauf si c'est le dernier exercice
            if not is_last:
                workout_items.append(
                    {
                        "name": "Break",
                        "description": "Période de récupération",
                        "icon": "⏸️",
                        "duration": BREAK_CLASSIC_DURATION,
                        "order": order,
                        "overlay_type": "break_classic",
                        "is_break": True,
                        "exercise_id": "break",
                        "next_exercise_name": exercises[idx + 1].name
                        if idx + 1 < len(exercises)
                        else "",
                        "next_exercise_duration": work_time,
                    }
                )
                order += 1
        else:
            # EXERCICES SUIVANTS : Preview (5s) + No overlay (40s) + Break classic (15s)

            # 1. Preview transparent overlay (5s) - fin du break, début de l'exercice
            workout_items.append(
                {
                    "name": "Next Up",
                    "description": f"Prochain : {exercise.name}",
                    "icon": "👁️",
                    "duration": PREVIEW_DURATION,
                    "order": order,
                    "overlay_type": "break_transparent",
                    "is_break": True,
                    "exercise_id": "preview",
                    "next_exercise_name": exercise.name,
                    "next_exercise_icon": getattr(exercise, "icon", "🏋️"),
                }
            )
            order += 1

            # 2. No overlay pour l'exercice (40s)
            workout_items.append(
                {
                    "name": exercise.name,
                    "description": exercise.description or f"Exercice {exercise.name}",
                    "icon": getattr(exercise, "icon", "🏋️"),
                    "duration": work_time,
                    "order": order,
                    "overlay_type": "none",
                    "is_break": False,
                    "exercise_id": exercise.id,
                }
            )
            order += 1

            # 3. Break classic (15s) sauf si c'est le dernier exercice
            if not is_last:
                workout_items.append(
                    {
                        "name": "Break",
                        "description": "Période de récupération",
                        "icon": "⏸️",
                        "duration": BREAK_CLASSIC_DURATION,
                        "order": order,
                        "overlay_type": "break_classic",
                        "is_break": True,
                        "exercise_id": "break",
                        "next_exercise_name": exercises[idx + 1].name
                        if idx + 1 < len(exercises)
                        else "",
                        "next_exercise_duration": work_time,
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
