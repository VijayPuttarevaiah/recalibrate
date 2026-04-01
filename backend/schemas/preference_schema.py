from pydantic import BaseModel, ConfigDict


class PreferenceBase(BaseModel):
    interest: str
    experience_level: str
    hours_per_week: int
    target_goal: str


class PreferenceCreate(PreferenceBase):
    pass


class PreferenceResponse(PreferenceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int