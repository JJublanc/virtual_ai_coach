import json
from uuid import uuid4
from datetime import datetime

from app.models.exercise import Exercise, Difficulty
from app.models.workout import (
    Workout,
    WorkoutExercise,
    WorkoutSession,
    Status,
    Intensity,
)
from app.models.config import WorkoutConfig


def test_workout_status_enum():
    # Test WorkoutStatus enum
    assert Status.DRAFT == "draft"
    assert Status.READY == "ready"
    assert Status.IN_PROGRESS == "in_progress"
    assert Status.COMPLETED == "completed"


def test_workout_intensity_enum():
    # Test WorkoutIntensity enum
    assert Intensity.LOW_IMPACT == "low_impact"
    assert Intensity.MEDIUM_INTENSITY == "medium_intensity"
    assert Intensity.HIGH_INTENSITY == "high_intensity"


def test_workout_config():
    # Test WorkoutConfig
    config_data = {
        "intensity": Intensity.HIGH_INTENSITY,
        "intervals": {"work_time": 45, "rest_time": 15},
        "no_jump": True,
        "intensity_levels": [Difficulty.MEDIUM, Difficulty.HARD],
        "target_duration": 20,
    }
    config = WorkoutConfig(**config_data)
    assert config.intensity == Intensity.HIGH_INTENSITY
    assert config.intervals["work_time"] == 45
    assert config.no_jump
    assert config.intensity_levels == [Difficulty.MEDIUM, Difficulty.HARD]


def test_workout_model():
    # Test Workout model
    workout_data = {
        "name": "Test Workout",
        "config": {
            "intensity": Intensity.MEDIUM_INTENSITY,
            "intervals": {"work_time": 40, "rest_time": 20},
            "intensity_levels": [Difficulty.EASY, Difficulty.MEDIUM],
        },
        "total_duration": 600,
        "status": Status.DRAFT,
    }
    workout = Workout(**workout_data)
    assert workout.name == "Test Workout"
    assert workout.status == Status.DRAFT
    assert workout.config.intensity == Intensity.MEDIUM_INTENSITY
    assert workout.config.intensity_levels == [Difficulty.EASY, Difficulty.MEDIUM]


def test_workout_exercise():
    # Test WorkoutExercise
    exercise_id = uuid4()
    workout_exercise = WorkoutExercise(
        exercise_id=exercise_id, order_index=0, custom_duration=45
    )
    assert exercise_id == workout_exercise.exercise_id
    assert workout_exercise.order_index == 0
    assert workout_exercise.custom_duration == 45


def test_workout_session():
    # Test WorkoutSession
    workout_id = uuid4()
    session_data = {
        "workout_id": workout_id,
        "started_at": datetime.now(),
        "duration_seconds": 600,
        "exercises_completed": 4,
        "feedback": {"difficulty": "medium", "enjoyed": True},
    }
    session = WorkoutSession(**session_data)
    assert session.workout_id == workout_id
    assert session.duration_seconds == 600
    assert session.feedback["difficulty"] == "medium"


def test_load_mock_exercises():
    # Test loading mock exercises
    with open("backend/app/models/exercises.json", "r") as f:
        mock_exercises = json.load(f)

    assert len(mock_exercises) == 3

    for exercise_data in mock_exercises:
        exercise = Exercise(**exercise_data)
        assert exercise.name is not None
        assert exercise.video_url is not None
        assert exercise.default_duration > 0
