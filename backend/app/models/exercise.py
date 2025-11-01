from enum import Enum
from uuid import UUID, uuid4
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class AccessTier(str, Enum):
    FREE = "free"
    PREMIUM = "premium"


class ExerciseMetadata(BaseModel):
    muscles_targeted: Optional[List[str]] = None
    equipment_needed: Optional[List[str]] = None
    calories_per_min: Optional[float] = None
    alternative_exercises: Optional[List[UUID]] = None


class Exercise(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = Field(default=None, max_length=50)
    video_url: str
    thumbnail_url: Optional[str] = None
    default_duration: int = Field(..., gt=0)
    difficulty: Difficulty = Field(...)
    has_jump: bool = False
    access_tier: AccessTier = Field(default=AccessTier.FREE)
    metadata: Optional[ExerciseMetadata] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Push-ups",
                "description": "Pompes classiques, gardez le corps aligné",
                "icon": "💪",
                "video_url": "https://example.com/pushups.mov",
                "default_duration": 30,
                "difficulty": Difficulty.MEDIUM,
                "has_jump": False,
                "metadata": {
                    "muscles_targeted": ["chest", "triceps", "shoulders"],
                    "calories_per_min": 7.0,
                },
            }
        }
    )

    @field_validator("default_duration")
    @classmethod
    def validate_duration(cls, v):
        if v <= 0:
            raise ValueError("Duration must be positive")
        return v
