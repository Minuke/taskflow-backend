from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Modelo base: el código Python sigue en snake_case (idiomático),
    pero el JSON de entrada/salida usa camelCase, para encajar con las
    interfaces TypeScript del frontend sin tocar la convención de Python."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        validate_by_alias=True,
        from_attributes=True,
    )