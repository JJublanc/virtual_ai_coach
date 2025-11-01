"""Tests unitaires pour le service de génération d'exercices."""

import pytest
from uuid import uuid4
from pathlib import Path
from unittest.mock import patch, mock_open

from app.models.exercise import Exercise, Difficulty
from app.models.workout import Workout, WorkoutExercise
from app.models.config import WorkoutConfig
from app.services.workout_generator import (
    load_exercises_from_json,
    filter_exercises,
    generate_random_exercises,
    generate_workout_exercises,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def sample_exercises():
    """Fixture fournissant une liste d'exercices de test."""
    return [
        Exercise(
            id=uuid4(),
            name="Push-ups",
            description="Pompes classiques",
            video_url="/path/to/video1.mov",
            default_duration=30,
            difficulty=Difficulty.MEDIUM,
            has_jump=False,
        ),
        Exercise(
            id=uuid4(),
            name="Air Squat",
            description="Squats au poids du corps",
            video_url="/path/to/video2.mov",
            default_duration=45,
            difficulty=Difficulty.EASY,
            has_jump=False,
        ),
        Exercise(
            id=uuid4(),
            name="Burpees",
            description="Burpees avec saut",
            video_url="/path/to/video3.mov",
            default_duration=30,
            difficulty=Difficulty.HARD,
            has_jump=True,
        ),
        Exercise(
            id=uuid4(),
            name="Plank",
            description="Gainage ventral",
            video_url="/path/to/video4.mov",
            default_duration=60,
            difficulty=Difficulty.MEDIUM,
            has_jump=False,
        ),
        Exercise(
            id=uuid4(),
            name="Jump Squats",
            description="Squats sautés",
            video_url="/path/to/video5.mov",
            default_duration=30,
            difficulty=Difficulty.HARD,
            has_jump=True,
        ),
    ]


@pytest.fixture
def sample_workout_config():
    """Fixture fournissant une configuration de workout standard."""
    return WorkoutConfig(
        no_jump=True,
        exercice_intensity_levels=[Difficulty.EASY, Difficulty.MEDIUM],
        intervals={"work_time": 40, "rest_time": 20},
    )


@pytest.fixture
def sample_workout(sample_workout_config):
    """Fixture fournissant un workout de test complet."""
    return Workout(
        name="Test Workout",
        total_duration=600,  # 10 minutes
        config=sample_workout_config,
    )


# ============================================================================
# TESTS DE load_exercises_from_json()
# ============================================================================


def test_load_exercises_from_json_success():
    """Vérifie que les exercices se chargent correctement depuis le JSON."""
    exercises = load_exercises_from_json()

    assert isinstance(exercises, list)
    assert len(exercises) > 0
    assert all(isinstance(ex, Exercise) for ex in exercises)
    # Vérifier que les IDs ont été générés
    assert all(ex.id is not None for ex in exercises)


def test_load_exercises_json_not_found():
    """Vérifie l'erreur si le fichier exercises.json n'existe pas."""
    with patch(
        "app.services.workout_generator.EXERCISES_FILE",
        Path("/fake/path/exercises.json"),
    ):
        with pytest.raises(FileNotFoundError) as exc_info:
            load_exercises_from_json()

        assert "exercises.json introuvable" in str(exc_info.value)


def test_load_exercises_invalid_json():
    """Vérifie l'erreur si le JSON est corrompu."""
    invalid_json = "{ invalid json }"

    with patch("builtins.open", mock_open(read_data=invalid_json)):
        with patch.object(Path, "exists", return_value=True):
            with pytest.raises(ValueError) as exc_info:
                load_exercises_from_json()

            assert "parsing JSON" in str(exc_info.value)


# ============================================================================
# TESTS DE filter_exercises()
# ============================================================================


def test_filter_no_jump(sample_exercises):
    """Vérifie que les exercices avec saut sont exclus si no_jump=True."""
    filtered = filter_exercises(
        exercises=sample_exercises,
        no_jump=True,
        intensity_levels=[Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD],
    )

    # Doit contenir uniquement Push-ups, Air Squat, Plank (pas de sauts)
    assert len(filtered) == 3
    assert all(not ex.has_jump for ex in filtered)
    assert all(ex.name in ["Push-ups", "Air Squat", "Plank"] for ex in filtered)


def test_filter_with_jump_allowed(sample_exercises):
    """Vérifie que tous les exercices passent si no_jump=False."""
    filtered = filter_exercises(
        exercises=sample_exercises,
        no_jump=False,
        intensity_levels=[Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD],
    )

    # Tous les exercices doivent être présents
    assert len(filtered) == 5


def test_filter_difficulty_levels(sample_exercises):
    """Vérifie le filtrage par niveau de difficulté."""
    filtered = filter_exercises(
        exercises=sample_exercises,
        no_jump=False,
        intensity_levels=[Difficulty.EASY, Difficulty.MEDIUM],
    )

    # Doit contenir Push-ups, Air Squat, Plank (pas HARD)
    assert len(filtered) == 3
    assert all(ex.difficulty in [Difficulty.EASY, Difficulty.MEDIUM] for ex in filtered)
    assert all(ex.name in ["Push-ups", "Air Squat", "Plank"] for ex in filtered)


def test_filter_combined_criteria(sample_exercises):
    """Vérifie le filtrage avec critères combinés (no_jump + difficulty)."""
    filtered = filter_exercises(
        exercises=sample_exercises, no_jump=True, intensity_levels=[Difficulty.EASY]
    )

    # Doit contenir uniquement Air Squat
    assert len(filtered) == 1
    assert filtered[0].name == "Air Squat"
    assert not filtered[0].has_jump
    assert filtered[0].difficulty == Difficulty.EASY


def test_filter_empty_pool(sample_exercises):
    """Vérifie l'exception si aucun exercice ne correspond aux critères."""
    with pytest.raises(ValueError) as exc_info:
        filter_exercises(
            exercises=sample_exercises,
            no_jump=True,
            intensity_levels=[Difficulty.HARD],  # Impossible: HARD avec no_jump
        )

    assert "Aucun exercice trouvé" in str(exc_info.value)


def test_filter_no_restrictions(sample_exercises):
    """Vérifie que tous les exercices passent sans restrictions."""
    filtered = filter_exercises(
        exercises=sample_exercises,
        no_jump=False,
        intensity_levels=[Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD],
    )

    assert len(filtered) == len(sample_exercises)


# ============================================================================
# TESTS DE generate_random_exercises()
# ============================================================================


def test_generate_random_exercises_count(sample_exercises):
    """Vérifie que le bon nombre d'exercices est généré."""
    selected = generate_random_exercises(sample_exercises, count=10)

    assert len(selected) == 10
    assert all(isinstance(ex, Exercise) for ex in selected)


def test_generate_random_exercises_with_replacement(sample_exercises):
    """Vérifie que le tirage avec remise fonctionne (doublons possibles)."""
    # Tirer plus d'exercices que le pool disponible
    selected = generate_random_exercises(sample_exercises, count=20)

    assert len(selected) == 20
    # Vérifier qu'il y a au moins un doublon
    exercise_names = [ex.name for ex in selected]
    assert len(exercise_names) > len(set(exercise_names))


def test_generate_random_exercises_zero_count(sample_exercises):
    """Vérifie le comportement avec count=0."""
    selected = generate_random_exercises(sample_exercises, count=0)
    assert len(selected) == 0


def test_generate_random_exercises_empty_pool():
    """Vérifie l'erreur si le pool est vide."""
    with pytest.raises(ValueError) as exc_info:
        generate_random_exercises([], count=5)

    assert "pool d'exercices est vide" in str(exc_info.value)


# ============================================================================
# TESTS DE generate_workout_exercises()
# ============================================================================


def test_generate_workout_exercises_success(sample_workout):
    """Test nominal avec une config valide."""
    with patch("app.services.workout_generator.load_exercises_from_json") as mock_load:
        mock_load.return_value = [
            Exercise(
                id=uuid4(),
                name="Push-ups",
                video_url="/path/to/video.mov",
                default_duration=30,
                difficulty=Difficulty.MEDIUM,
                has_jump=False,
            ),
            Exercise(
                id=uuid4(),
                name="Air Squat",
                video_url="/path/to/video2.mov",
                default_duration=45,
                difficulty=Difficulty.EASY,
                has_jump=False,
            ),
        ]

        result = generate_workout_exercises(sample_workout)

        assert isinstance(result, list)
        assert len(result) == 10  # 600s / 60 = 10 exercices
        assert all(isinstance(ex, WorkoutExercise) for ex in result)


def test_generate_workout_exercises_no_config():
    """Vérifie l'erreur si la config est manquante."""
    # Pydantic valide déjà config, donc on utilise model_construct pour contourner
    workout = Workout.model_construct(total_duration=600, config=None)

    with pytest.raises(ValueError) as exc_info:
        generate_workout_exercises(workout)

    assert "doit avoir une configuration" in str(exc_info.value)


def test_generate_workout_exercises_invalid_duration():
    """Vérifie l'erreur si la durée est invalide."""
    # Pydantic valide déjà total_duration > 0, donc on utilise model_construct
    workout = Workout.model_construct(
        total_duration=0,
        config=WorkoutConfig(no_jump=True, exercice_intensity_levels=[Difficulty.EASY]),
    )

    with pytest.raises(ValueError) as exc_info:
        generate_workout_exercises(workout)

    assert "doit être positif" in str(exc_info.value)


def test_generate_workout_exercises_order_index(sample_workout):
    """Vérifie que order_index est séquentiel (0, 1, 2...)."""
    with patch("app.services.workout_generator.load_exercises_from_json") as mock_load:
        mock_load.return_value = [
            Exercise(
                id=uuid4(),
                name="Test Exercise",
                video_url="/path/to/video.mov",
                default_duration=30,
                difficulty=Difficulty.MEDIUM,
                has_jump=False,
            )
        ]

        result = generate_workout_exercises(sample_workout)

        # Vérifier l'ordre séquentiel
        for i, workout_ex in enumerate(result):
            assert workout_ex.order_index == i

        assert result[0].order_index == 0
        assert result[-1].order_index == len(result) - 1


def test_generate_workout_exercises_correct_count():
    """Vérifie que nb_exercises = total_duration / 60."""
    test_cases = [
        (600, 10),  # 10 minutes
        (1200, 20),  # 20 minutes
        (300, 5),  # 5 minutes
        (120, 2),  # 2 minutes
    ]

    for duration, expected_count in test_cases:
        workout = Workout(
            total_duration=duration,
            config=WorkoutConfig(
                no_jump=False,
                exercice_intensity_levels=[Difficulty.EASY, Difficulty.MEDIUM],
            ),
        )

        with patch(
            "app.services.workout_generator.load_exercises_from_json"
        ) as mock_load:
            mock_load.return_value = [
                Exercise(
                    id=uuid4(),
                    name="Test Exercise",
                    video_url="/path/to/video.mov",
                    default_duration=30,
                    difficulty=Difficulty.EASY,
                    has_jump=False,
                )
            ]

            result = generate_workout_exercises(workout)
            assert len(result) == expected_count


def test_generate_workout_exercises_too_short_duration():
    """Vérifie l'erreur si la durée est trop courte."""
    workout = Workout(
        total_duration=30,  # < 60 secondes
        config=WorkoutConfig(no_jump=True, exercice_intensity_levels=[Difficulty.EASY]),
    )

    with patch("app.services.workout_generator.load_exercises_from_json") as mock_load:
        mock_load.return_value = [
            Exercise(
                id=uuid4(),
                name="Test Exercise",
                video_url="/path/to/video.mov",
                default_duration=30,
                difficulty=Difficulty.EASY,
                has_jump=False,
            )
        ]

        with pytest.raises(ValueError) as exc_info:
            generate_workout_exercises(workout)

        assert "trop courte" in str(exc_info.value)


def test_generate_workout_exercises_custom_duration_is_none():
    """Vérifie que custom_duration est None (utilise default_duration)."""
    workout = Workout(
        total_duration=600,
        config=WorkoutConfig(no_jump=True, exercice_intensity_levels=[Difficulty.EASY]),
    )

    with patch("app.services.workout_generator.load_exercises_from_json") as mock_load:
        mock_load.return_value = [
            Exercise(
                id=uuid4(),
                name="Test Exercise",
                video_url="/path/to/video.mov",
                default_duration=30,
                difficulty=Difficulty.EASY,
                has_jump=False,
            )
        ]

        result = generate_workout_exercises(workout)

        assert all(ex.custom_duration is None for ex in result)


# ============================================================================
# TESTS D'INTÉGRATION
# ============================================================================


def test_full_workflow_10_minutes():
    """Test complet : 10 min = 10 exercices filtrés correctement."""
    workout = Workout(
        name="Full Workflow Test",
        total_duration=600,
        config=WorkoutConfig(
            no_jump=True, exercice_intensity_levels=[Difficulty.EASY, Difficulty.MEDIUM]
        ),
    )

    # Utiliser les vrais exercices du JSON
    result = generate_workout_exercises(workout)

    assert len(result) == 10
    assert all(isinstance(ex, WorkoutExercise) for ex in result)
    assert all(ex.order_index == i for i, ex in enumerate(result))


def test_full_workflow_restrictive_filters():
    """Test avec filtres très restrictifs."""
    workout = Workout(
        name="Restrictive Test",
        total_duration=300,  # 5 minutes
        config=WorkoutConfig(no_jump=True, exercice_intensity_levels=[Difficulty.EASY]),
    )

    # Ce test peut échouer si aucun exercice EASY sans saut n'existe
    # Dans ce cas, il doit lever une ValueError
    try:
        result = generate_workout_exercises(workout)
        assert len(result) == 5
        assert all(isinstance(ex, WorkoutExercise) for ex in result)
    except ValueError as e:
        # Comportement attendu si aucun exercice ne correspond
        assert "Aucun exercice trouvé" in str(e)


def test_full_workflow_all_exercises_allowed():
    """Test sans restrictions (tous les exercices autorisés)."""
    workout = Workout(
        name="No Restrictions Test",
        total_duration=1200,  # 20 minutes
        config=WorkoutConfig(
            no_jump=False,
            exercice_intensity_levels=[
                Difficulty.EASY,
                Difficulty.MEDIUM,
                Difficulty.HARD,
            ],
        ),
    )

    result = generate_workout_exercises(workout)

    assert len(result) == 20
    assert all(isinstance(ex, WorkoutExercise) for ex in result)
    assert result[0].order_index == 0
    assert result[-1].order_index == 19
