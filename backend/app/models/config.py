from typing import List, Dict
from pydantic import BaseModel, Field
from .exercise import Difficulty
from .enums import Intensity


class WorkoutConfig(BaseModel):
    intensity: Intensity = Field(default=Intensity.MEDIUM_INTENSITY)
    intervals: Dict[str, int] = Field(default={"work_time": 40, "rest_time": 20})
    no_repeat: bool = False
    no_jump: bool = False
    intensity_levels: List[Difficulty] = [
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
