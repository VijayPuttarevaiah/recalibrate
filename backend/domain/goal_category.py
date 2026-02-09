from enum import Enum


class GoalCategory(str, Enum):
    CAREER_AND_LEARNING = "career_and_learning"
    FITNESS = "fitness"
    IMMIGRATION = "immigration"

    @classmethod
    def values(cls) -> list[str]:
        return [category.value for category in cls]

    @classmethod
    def from_raw(cls, value: str | None) -> "GoalCategory | None":
        if not value:
            return None
        normalized = value.strip().lower()
        for category in cls:
            if normalized == category.value:
                return category
        return None
