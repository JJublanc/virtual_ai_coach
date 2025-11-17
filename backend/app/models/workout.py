from uuid import UUID
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from .exercise import Difficulty
from .config import WorkoutConfig
from .enums import Status, Intensity


class WorkoutExercise(BaseModel):
    id: Optional[UUID] = None
    workout_id: Optional[UUID] = None
    exercise_id: UUID
    order_index: int = Field(..., ge=0)
    custom_duration: Optional[int] = Field(default=None, gt=0)


class Workout(BaseModel):
    id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    name: Optional[str] = Field(default=None, max_length=100)
    config: WorkoutConfig
    total_duration: Optional[int] = Field(default=None, gt=0)
    ai_generated: bool = False
    ai_prompt: Optional[str] = None
    status: Status = Field(default=Status.DRAFT)
    video_url: Optional[str] = None
    session_token: Optional[str] = Field(default=None, max_length=255)
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    exercises: Optional[List[WorkoutExercise]] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Séance Découverte",
                "config": {
                    "intensity": Intensity.LOW_IMPACT,
                    "intervals": {"work_time": 30, "rest_time": 30},
                    "no_jump": True,
                    "intensity_levels": [Difficulty.EASY, Difficulty.MEDIUM],
                    "target_duration": 10,
                },
                "total_duration": 600,
                "status": Status.DRAFT,
            }
        }
    )


class WorkoutSession(BaseModel):
    id: Optional[UUID] = None
    workout_id: UUID
    user_id: Optional[UUID] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = Field(default=None, ge=0)
    exercises_completed: Optional[int] = Field(default=None, ge=0)
    feedback: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "workout_id": "some-uuid",
                "duration_seconds": 600,
                "exercises_completed": 4,
                "feedback": {"difficulty": "too_easy", "enjoyed": True, "rating": 4},
            }
        }
    )
