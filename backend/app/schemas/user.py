from pydantic import BaseModel, ConfigDict, Field


class UserCreateSchema(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str


class TokenSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
