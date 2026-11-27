"""Carga datos de demostración para desarrollo.

Uso (desde la raíz del repo, con el venv activado):
    python -m scripts.seed            # crea el usuario demo si no existe
    python -m scripts.seed --reset    # borra el usuario demo y lo recrea
"""

import argparse
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.category import Category
from app.models.task import Priority, Task
from app.models.user import User

DEMO_NAME = "Usuario Demo"
DEMO_EMAIL = "demo@taskflow.dev"
DEMO_PASSWORD = "Demo1234!"

# (nombre, descripción)
CATEGORIES = [
    ("Trabajo", "Tareas de la oficina y proyectos"),
    ("Personal", "Recados y asuntos del día a día"),
    ("Estudios", "Cursos, lecturas y prácticas"),
    ("Casa", "Mantenimiento y compras del hogar"),
]

# (título, descripción, prioridad, horas, completada, días desde hoy o None, categoría)
TASKS = [
    (
        "Preparar informe trimestral",
        "Recopilar métricas y redactar conclusiones",
        Priority.HIGH,
        "6.5",
        False,
        -3,
        "Trabajo",
    ),
    (
        "Revisar pull requests pendientes",
        "Priorizar los del equipo de plataforma",
        Priority.HIGH,
        "2",
        False,
        0,
        "Trabajo",
    ),
    (
        "Reunión de planificación",
        "Preparar agenda y objetivos del sprint",
        Priority.MEDIUM,
        "1.5",
        False,
        1,
        "Trabajo",
    ),
    ("Actualizar documentación de la API", None, Priority.LOW, "3", False, 10, "Trabajo"),
    (
        "Enviar facturas del mes",
        "Comprobar importes antes de enviar",
        Priority.HIGH,
        "1",
        True,
        -5,
        "Trabajo",
    ),
    ("Pedir cita en el dentista", None, Priority.MEDIUM, "0.5", False, -1, "Personal"),
    (
        "Renovar el seguro del coche",
        "Comparar al menos tres presupuestos",
        Priority.HIGH,
        "2",
        False,
        4,
        "Personal",
    ),
    ("Llamar a los abuelos", None, Priority.LOW, "0.5", True, -2, "Personal"),
    (
        "Planificar las vacaciones",
        "Vuelos, alojamiento y presupuesto",
        Priority.MEDIUM,
        "4",
        False,
        30,
        "Personal",
    ),
    (
        "Terminar el curso de Angular",
        "Módulos de Signals y formularios",
        Priority.MEDIUM,
        "10",
        False,
        14,
        "Estudios",
    ),
    ("Leer capítulo de arquitectura limpia", None, Priority.LOW, "2.5", False, None, "Estudios"),
    (
        "Practicar SQL con ejercicios",
        "Joins, agregaciones y ventanas",
        Priority.MEDIUM,
        "3",
        True,
        -7,
        "Estudios",
    ),
    ("Comprar material de limpieza", None, Priority.LOW, "1", False, 0, "Casa"),
    (
        "Reparar el grifo de la cocina",
        "Cambiar la junta o llamar al fontanero",
        Priority.HIGH,
        "1.5",
        False,
        2,
        "Casa",
    ),
    ("Ordenar el trastero", None, Priority.LOW, "4", False, None, "Casa"),
    (
        "Sin categoría: ideas para el blog",
        "Lista de posibles temas",
        Priority.LOW,
        "1",
        False,
        None,
        None,
    ),
]


def create_demo_data(db) -> None:
    user = User(name=DEMO_NAME, email=DEMO_EMAIL, password_hash=hash_password(DEMO_PASSWORD))
    db.add(user)
    db.flush()  # asigna user.id sin cerrar la transacción

    categories = {}
    for name, description in CATEGORIES:
        category = Category(name=name, description=description, user_id=user.id)
        db.add(category)
        categories[name] = category
    db.flush()  # asigna category.id

    today = date.today()
    for title, description, priority, hours, completed, offset, category_name in TASKS:
        category = categories.get(category_name)
        db.add(
            Task(
                title=title,
                description=description,
                priority=priority,
                estimated_hours=Decimal(hours),
                completed=completed,
                due_date=today + timedelta(days=offset) if offset is not None else None,
                category_id=category.id if category else None,
                user_id=user.id,
            )
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Carga datos de demo de TaskFlow")
    parser.add_argument("--reset", action="store_true", help="Borra el usuario demo y lo recrea")
    args = parser.parse_args()

    if settings.environment == "production":
        raise SystemExit("Seed bloqueado: ENVIRONMENT=production.")

    with SessionLocal() as db:
        existing = db.scalar(select(User).where(User.email == DEMO_EMAIL))

        if existing and not args.reset:
            print(f"El usuario demo ya existe ({DEMO_EMAIL}). Usa --reset para recrearlo.")
            return

        if existing:
            db.delete(existing)  # cascade borra sus categorías y tareas
            db.flush()

        create_demo_data(db)
        db.commit()

    print(f"Datos de demo creados. Login: {DEMO_EMAIL} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
