from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Convención de nombres para restricciones (claves foráneas, índices, etc.).
# Sin esto, PostgreSQL genera nombres automáticos poco predecibles (p.ej. "tasks_category_id_fkey"),
# lo que complica escribir o revisar migraciones futuras que necesiten referenciarlos por nombre.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Clase base de la que heredan todos los modelos ORM del proyecto."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)

CASCADE_DELETE_ORPHAN = "all, delete-orphan"