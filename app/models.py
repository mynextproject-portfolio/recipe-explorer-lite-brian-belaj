from pydantic import BaseModel, Field, field_serializer, ConfigDict
from datetime import datetime
from typing import List
from enum import Enum
import uuid


MAX_TITLE_LENGTH = 200
MAX_INGREDIENTS = 50


class DifficultyLevel(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class RecipeBase(BaseModel):
    title: str = Field(..., max_length=MAX_TITLE_LENGTH)
    description: str
    ingredients: List[str] = Field(..., max_length=MAX_INGREDIENTS)
    instructions: List[str]
    tags: List[str] = Field(default_factory=list)
    difficulty: DifficultyLevel
    cuisine: str = "Other"


class RecipeCreate(RecipeBase):
    pass


class RecipeUpdate(RecipeBase):
    pass


class Recipe(RecipeBase):
    model_config = ConfigDict()

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, v: datetime) -> str:
        return v.isoformat()
