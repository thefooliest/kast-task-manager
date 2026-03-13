from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None


class AddMemberRequest(BaseModel):
    email: str