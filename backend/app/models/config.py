from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from .exercise import Difficulty, ExerciseTheme
from .enums import Intensity


class BlockConfig(BaseModel):
    """Configuration pour la génération par blocs thématiques"""

    themes: List[ExerciseTheme] = Field(
        default=[ExerciseTheme.ABS, ExerciseTheme.UPPER_BODY, ExerciseTheme.CARDIO],
        description="Ordre des thèmes pour les blocs",
    )

    exercises_per_block: int = Field(
        default=3,
        ge=2,
        le=10,
        description="Nombre d'exercices différents par bloc",
    )

    repetitions_per_block: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Nombre de répétitions de chaque bloc",
    )

    fill_remaining_with_finishers: bool = Field(
        default=True,
        description="Remplir le temps restant avec des finishers après les blocs",
    )

    finisher_themes: List[ExerciseTheme] = Field(
        default=[ExerciseTheme.CARDIO, ExerciseTheme.FULL_BODY],
        description="Thèmes possibles pour les finishers",
    )


class WorkoutConfig(BaseModel):
    intensity: Intensity = Field(default=Intensity.MEDIUM_INTENSITY)
    intervals: Dict[str, int] = Field(default={"work_time": 40, "rest_time": 20})
    no_repeat: bool = False
    no_jump: bool = False
    exercice_intensity_levels: List[Difficulty] = [
        Difficulty.EASY,
        Difficulty.MEDIUM,
        Difficulty.HARD,
    ]
    include_warm_up: bool = True
    include_cool_down: bool = True
    target_duration: int = 30
    show_timer: bool = True
    show_progress_bar: bool = True
    show_exercise_name: bool = True

    # Filtre par type d'exercice
    exercise_type: Optional[str] = Field(
        default=None,
        description="Type d'exercice spécifique (burpee, jump, run, push_ups, plank, squat, crunch)",
    )

    # Configuration pour structure en blocs thématiques
    use_block_structure: bool = Field(
        default=False,
        description="Activer la génération par blocs thématiques (minimum 10 minutes)",
    )

    block_config: Optional[BlockConfig] = Field(
        default=None,
        description="Configuration des blocs (requis si use_block_structure=True)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "intensity": Intensity.MEDIUM_INTENSITY,
                "intervals": {"work_time": 40, "rest_time": 20},
                "no_jump": False,
                "intensity_levels": [Difficulty.EASY, Difficulty.MEDIUM],
                "target_duration": 30,
            }
        }
    }
