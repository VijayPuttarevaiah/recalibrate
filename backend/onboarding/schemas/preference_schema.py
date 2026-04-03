from pydantic import BaseModel, ConfigDict


class PreferenceCreate(BaseModel):
    interest: str
    experience_level: str
    hours_per_week: int
    target_goal: str
    user_id: int | None = None


class PreferenceResponse(BaseModel):
    id: int
    user_id: int
    interest: str
    experience_level: str
    hours_per_week: int
    target_goal: str

    model_config = ConfigDict(from_attributes=True)
