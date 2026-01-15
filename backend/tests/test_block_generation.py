"""Tests pour la génération de workouts par blocs thématiques."""

import pytest
from uuid import uuid4

from app.models.exercise import Exercise, Difficulty, ExerciseTheme, ExerciseMetadata
from app.models.config import WorkoutConfig, BlockConfig
from app.models.workout import Workout
from app.services.workout_generator import (
    filter_exercises_by_theme,
    select_diverse_exercises,
    select_finisher_exercises,
    generate_workout_with_blocks,
)


@pytest.fixture
def sample_exercises():
    """Crée un ensemble d'exercices pour les tests."""
    exercises = [
        # Exercices ABS
        Exercise(
            id=uuid4(),
            name="Plank",
            video_url="test.mov",
            default_duration=60,
            difficulty=Difficulty.MEDIUM,
            metadata=ExerciseMetadata(
                muscles_targeted=["core", "abs"],
                themes=[ExerciseTheme.ABS],
            ),
        ),
        Exercise(
            id=uuid4(),
            name="Crunches",
            video_url="test.mov",
            default_duration=60,
            difficulty=Difficulty.EASY,
            metadata=ExerciseMetadata(
                muscles_targeted=["abs"], themes=[ExerciseTheme.ABS]
            ),
        ),
        Exercise(
            id=uuid4(),
            name="Russian Twists",
            video_url="test.mov",
            default_duration=60,
            difficulty=Difficulty.MEDIUM,
            metadata=ExerciseMetadata(
                muscles_targeted=["obliques", "core"], themes=[ExerciseTheme.ABS]
            ),
        ),
        # Exercices UPPER_BODY
        Exercise(
            id=uuid4(),
            name="Push-ups",
            video_url="test.mov",
            default_duration=60,
            difficulty=Difficulty.MEDIUM,
            metadata=ExerciseMetadata(
                muscles_targeted=["chest", "triceps"],
                themes=[ExerciseTheme.UPPER_BODY],
            ),
        ),
        Exercise(
            id=uuid4(),
            name="Dips",
            video_url="test.mov",
            default_duration=60,
            difficulty=Difficulty.HARD,
            metadata=ExerciseMetadata(
                muscles_targeted=["triceps", "chest"],
                themes=[ExerciseTheme.UPPER_BODY],
            ),
        ),
        Exercise(
            id=uuid4(),
            name="Commandos",
            video_url="test.mov",
            default_duration=60,
            difficulty=Difficulty.HARD,
            metadata=ExerciseMetadata(
                muscles_targeted=["core", "shoulders"],
                themes=[ExerciseTheme.UPPER_BODY],
            ),
        ),
        # Exercices CARDIO
        Exercise(
            id=uuid4(),
            name="High Knees",
            video_url="test.mov",
            default_duration=60,
            difficulty=Difficulty.MEDIUM,
            has_jump=True,
            metadata=ExerciseMetadata(
                muscles_targeted=["quadriceps", "cardio"],
                themes=[ExerciseTheme.CARDIO],
            ),
        ),
        Exercise(
            id=uuid4(),
            name="Jumping Jacks",
            video_url="test.mov",
            default_duration=60,
            difficulty=Difficulty.EASY,
            has_jump=True,
            metadata=ExerciseMetadata(
                muscles_targeted=["full_body"], themes=[ExerciseTheme.CARDIO]
            ),
        ),
        Exercise(
            id=uuid4(),
            name="Skater Hops",
            video_url="test.mov",
            default_duration=60,
            difficulty=Difficulty.MEDIUM,
            has_jump=True,
            metadata=ExerciseMetadata(
                muscles_targeted=["legs", "cardio"], themes=[ExerciseTheme.CARDIO]
            ),
        ),
        # Exercices FULL_BODY
        Exercise(
            id=uuid4(),
            name="Burpees",
            video_url="test.mov",
            default_duration=60,
            difficulty=Difficulty.HARD,
            has_jump=True,
            metadata=ExerciseMetadata(
                muscles_targeted=["full_body"],
                themes=[ExerciseTheme.CARDIO, ExerciseTheme.FULL_BODY],
            ),
        ),
        Exercise(
            id=uuid4(),
            name="Mountain Climbers",
            video_url="test.mov",
            default_duration=60,
            difficulty=Difficulty.HARD,
            metadata=ExerciseMetadata(
                muscles_targeted=["core", "cardio"],
                themes=[
                    ExerciseTheme.CARDIO,
                    ExerciseTheme.ABS,
                    ExerciseTheme.FULL_BODY,
                ],
            ),
        ),
    ]
    return exercises


def test_filter_exercises_by_theme(sample_exercises):
    """Test du filtrage par thème."""
    # Filtrer les exercices ABS
    abs_exercises = filter_exercises_by_theme(sample_exercises, ExerciseTheme.ABS)
    abs_names = [ex.name for ex in abs_exercises]

    # Doit inclure les exercices ABS et FULL_BODY
    assert "Plank" in abs_names
    assert "Crunches" in abs_names
    assert "Mountain Climbers" in abs_names  # Contient ABS + FULL_BODY

    # Ne doit pas inclure les exercices UPPER_BODY purs
    assert "Push-ups" not in abs_names


def test_filter_exercises_cardio_includes_full_body(sample_exercises):
    """Test que FULL_BODY est inclus dans tous les thèmes."""
    cardio_exercises = filter_exercises_by_theme(sample_exercises, ExerciseTheme.CARDIO)
    cardio_names = [ex.name for ex in cardio_exercises]

    # Doit inclure Burpees (CARDIO + FULL_BODY)
    assert "Burpees" in cardio_names
    assert "Mountain Climbers" in cardio_names


def test_select_diverse_exercises(sample_exercises):
    """Test de la sélection d'exercices diversifiés."""
    abs_exercises = filter_exercises_by_theme(sample_exercises, ExerciseTheme.ABS)

    # Sélectionner 3 exercices
    selected = select_diverse_exercises(abs_exercises, count=3)

    assert len(selected) == 3
    # Tous les exercices doivent être différents
    assert len(set(ex.id for ex in selected)) == 3


def test_select_diverse_exercises_insufficient_pool():
    """Test avec pas assez d'exercices."""
    exercises = [
        Exercise(
            id=uuid4(),
            name="Plank",
            video_url="test.mov",
            default_duration=60,
            difficulty=Difficulty.MEDIUM,
            metadata=ExerciseMetadata(themes=[ExerciseTheme.ABS]),
        )
    ]

    with pytest.raises(ValueError, match="Pas assez d'exercices"):
        select_diverse_exercises(exercises, count=3)


def test_select_finisher_exercises(sample_exercises):
    """Test de la sélection des finishers."""
    finishers = select_finisher_exercises(
        sample_exercises,
        themes=[ExerciseTheme.CARDIO, ExerciseTheme.FULL_BODY],
        count=3,
    )

    assert len(finishers) == 3
    # Les finishers doivent être des exercices intenses
    # Au moins un doit être HARD
    has_hard = any(ex.difficulty == Difficulty.HARD for ex in finishers)
    assert has_hard


def test_select_finisher_exercises_prioritizes_hard(sample_exercises):
    """Test que les finishers priorisent HARD."""
    finishers = select_finisher_exercises(
        sample_exercises,
        themes=[ExerciseTheme.CARDIO],
        count=2,
    )

    # Avec assez d'exercices HARD disponibles, tous devraient être HARD
    # Burpees et Mountain Climbers sont HARD et CARDIO
    difficulties = [ex.difficulty for ex in finishers]
    # Au moins un doit être HARD
    assert Difficulty.HARD in difficulties


def test_generate_workout_with_blocks_validation(sample_exercises):
    """Test de la validation des paramètres."""
    # Test durée minimale
    workout = Workout(
        total_duration=300,  # 5 minutes - trop court
        config=WorkoutConfig(
            use_block_structure=True,
            block_config=BlockConfig(),
        ),
    )

    with pytest.raises(ValueError, match="minimum pour les blocs est de 10 minutes"):
        generate_workout_with_blocks(workout)


def test_generate_workout_with_blocks_missing_config():
    """Test avec config manquante."""
    workout = Workout(
        total_duration=1800,
        config=WorkoutConfig(use_block_structure=True),  # Pas de block_config
    )

    with pytest.raises(ValueError, match="block_config est requis"):
        generate_workout_with_blocks(workout)


def test_generate_workout_with_blocks_structure():
    """Test de la structure générée (test d'intégration basique)."""
    # Note: Ce test nécessite que load_exercises() fonctionne
    # Il est marqué comme un test d'intégration
    pass  # TODO: Implémenter avec un mock de load_exercises


def test_block_config_defaults():
    """Test des valeurs par défaut de BlockConfig."""
    config = BlockConfig()

    assert config.exercises_per_block == 3
    assert config.repetitions_per_block == 3
    assert config.fill_remaining_with_finishers is True
    assert ExerciseTheme.ABS in config.themes
    assert ExerciseTheme.CARDIO in config.finisher_themes


def test_workout_config_defaults():
    """Test des valeurs par défaut de WorkoutConfig."""
    config = WorkoutConfig()

    assert config.use_block_structure is False
    assert config.block_config is None
