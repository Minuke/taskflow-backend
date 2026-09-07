from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    password_confirm: str

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("El nombre no puede estar vacío.")
        return value.strip()

    @field_validator("password")
    @classmethod
    def password_min_length(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        return value

    @model_validator(mode="after")
    def passwords_match(self) -> Self:
        if self.password != self.password_confirm:
            raise ValueError("Las contraseñas no coinciden.")
        return self


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"