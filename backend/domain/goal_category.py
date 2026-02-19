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
        normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
        alias_map: dict[str, GoalCategory] = {
            "career": cls.CAREER_AND_LEARNING,
            "learning": cls.CAREER_AND_LEARNING,
            "education": cls.CAREER_AND_LEARNING,
            "academics": cls.CAREER_AND_LEARNING,
            "study": cls.CAREER_AND_LEARNING,
            "career_learning": cls.CAREER_AND_LEARNING,
            "careerandlearning": cls.CAREER_AND_LEARNING,
            "workout": cls.FITNESS,
            "health": cls.FITNESS,
            "wellness": cls.FITNESS,
            "visa": cls.IMMIGRATION,
            "pr": cls.IMMIGRATION,
            "citizenship": cls.IMMIGRATION,
            "migration": cls.IMMIGRATION,
        }
        if normalized in alias_map:
            return alias_map[normalized]
        for category in cls:
            if normalized == category.value:
                return category
        return None
