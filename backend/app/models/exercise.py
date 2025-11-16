from enum import Enum
from uuid import UUID, uuid4
from typing import List, Optional, Dict, Any
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

    @classmethod
    def from_supabase(cls, data: Dict[str, Any]) -> "Exercise":
        """
        Crée une instance Exercise depuis les données Supabase

        Args:
            data: Dictionnaire de données depuis Supabase PostgreSQL

        Returns:
            Instance Exercise
        """
        # Mapper les données Supabase vers le modèle Exercise
        return cls(
            id=UUID(data["id"]) if isinstance(data["id"], str) else data["id"],
            name=data["name"],
            description=data.get("description"),
            icon=data.get("icon"),
            video_url=data["video_url"],
            thumbnail_url=data.get("thumbnail_url"),
            default_duration=data["default_duration"],
            difficulty=Difficulty(data["difficulty"]),
            has_jump=data.get("has_jump", False),
            access_tier=AccessTier(data.get("access_tier", "free")),
            metadata=ExerciseMetadata(**data["metadata"])
            if data.get("metadata")
            else None,
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'exercice en dictionnaire pour insertion Supabase

        Returns:
            Dictionnaire avec les champs de l'exercice
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "video_url": self.video_url,
            "thumbnail_url": self.thumbnail_url,
            "default_duration": self.default_duration,
            "difficulty": self.difficulty.value,
            "has_jump": self.has_jump,
            "access_tier": self.access_tier.value,
            "metadata": self.metadata.model_dump() if self.metadata else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_supabase_url(self) -> bool:
        """
        Vérifie si video_url est une URL Supabase Storage

        Returns:
            True si URL Supabase, False sinon
        """
        return self.video_url.startswith("http")
