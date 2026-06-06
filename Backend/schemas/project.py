from pydantic import BaseModel

class ProjectCreate(BaseModel):

    name: str
    company_name: str
    location: str
    project_capacity_mw: float
    turbine_model: str
    rated_power_kw: float
    description: str | None = None


class ProjectResponse(BaseModel):

    id: int
    name: str
    description: str | None

    model_config = {
        "from_attributes": True
    }