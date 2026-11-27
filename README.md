# TaskFlow — Backend

API REST de TaskFlow, un gestor de tareas personal con categorías, filtros, paginación, imágenes y dashboard.

- Frontend: `taskflow-frontend` (Angular 22)
- Documentación interactiva: http://localhost:8000/docs (Swagger UI)

![Swagger](docs/screenshots/swagger.png)

## Funcionalidades

- Registro, login y sesión persistente (JWT de acceso + refresh token rotatorio en cookie httpOnly).
- CRUD de tareas y categorías, siempre aislado por usuario (otro usuario recibe 404, no 403).
- Filtros, orden y paginación en servidor (`LIMIT/OFFSET` con orden estable).
- Subida de imagen por tarea (validada con Pillow).
- Endpoint de dashboard con contadores agregados (`COUNT(*) FILTER`).
- Errores con formato uniforme `{ detail, errors[] }`.

## Stack

| Capa | Tecnología |
|---|---|
| Framework | FastAPI |
| Base de datos | PostgreSQL |
| ORM / migraciones | SQLAlchemy 2.0 (sync, psycopg3) + Alembic |
| Validación | Pydantic v2 + pydantic-settings |
| Autenticación | PyJWT (HS256) + pwdlib (Argon2id) |
| Imágenes | Pillow |
| Tests | Pytest + pytest-cov |
| Calidad | Ruff + pre-commit |

## Arranque rápido (menos de 10 minutos)

Requisitos: Python 3.12+ (probado con 3.14), PostgreSQL, Node 20+.

### 1. Base de datos

```sql
CREATE ROLE taskflow_user WITH LOGIN PASSWORD 'cambia_esta_password';
CREATE DATABASE taskflow_db OWNER taskflow_user;
```

### 2. Backend

```bash
git clone <url-backend> taskflow-backend
cd taskflow-backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # edita DATABASE_URL y SECRET_KEY
alembic upgrade head
python -m uvicorn app.main:app --reload
```

Genera una `SECRET_KEY` segura con:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 3. Frontend

```bash
git clone <url-frontend> taskflow-frontend
cd taskflow-frontend
npm install
npm start
```

Abre http://localhost:4200 y **regístrate** (no hay usuarios precargados).

> Usa siempre `localhost`, no `127.0.0.1`: la cookie de refresh y CORS están configurados para `localhost`.

## Variables de entorno

| Variable | Ejemplo / por defecto | Descripción |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://taskflow_user:pass@localhost:5432/taskflow_db` | Conexión a PostgreSQL |
| `SECRET_KEY` | (obligatoria) | Clave de firma del JWT |
| `JWT_ALGORITHM` | `HS256` | Algoritmo JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Vida del access token |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | Vida del refresh token |
| `COOKIE_SECURE` | `false` en local, `true` bajo HTTPS | Flag `Secure` de la cookie |
| `UPLOAD_DIR` | `uploads` | Carpeta de imágenes |
| `MAX_UPLOAD_SIZE_MB` | `5` | Tamaño máximo de imagen |
| `ENVIRONMENT` | `development` | Entorno |
| `CORS_ORIGINS` | `http://localhost:4200` | Orígenes permitidos |

Solo se versionan `.env.example` y `.env.test.example`. Los `.env` reales están en `.gitignore`.

## Autenticación

1. `POST /auth/login` devuelve un **access token** (JWT, 30 min) y fija una cookie httpOnly con un **refresh token** opaco.
2. El frontend guarda el access token solo en memoria (un signal) y lo envía como `Authorization: Bearer`.
3. Al expirar, `POST /auth/refresh` valida la cookie, **rota** el refresh token (el anterior queda revocado) y devuelve un nuevo access token.
4. En BD solo se guarda el **hash SHA-256** del refresh token.
5. `POST /auth/logout` revoca el token y borra la cookie.

## API

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/auth/register` | Crear usuario |
| POST | `/auth/login` | Login (form OAuth2) |
| POST | `/auth/refresh` | Renovar sesión |
| POST | `/auth/logout` | Cerrar sesión |
| GET | `/auth/me` | Usuario actual |
| GET/POST | `/categories` | Listar / crear |
| PUT/DELETE | `/categories/{id}` | Editar / borrar |
| GET/POST | `/tasks` | Listar (filtros) / crear |
| GET/PUT/DELETE | `/tasks/{id}` | Detalle / editar / borrar |
| POST/DELETE | `/tasks/{id}/image` | Subir / quitar imagen |
| GET | `/dashboard` | Contadores agregados |

Parámetros de `GET /tasks` (snake_case): filtros por estado, prioridad, categoría y texto; orden (`dueDate`, `noDate`…); `page` y tamaño de página. Orden estable: criterio elegido, `priority desc`, `id desc`.

Contrato: JSON en camelCase (excepto `Token`: `access_token`, `token_type`); `estimatedHours` se serializa como número.

## Formato de errores

```json
{
  "detail": "Datos no válidos",
  "errors": [{ "field": "title", "message": "String should have at least 3 characters" }]
}
```

El frontend usa `errors[].field` para marcar campos del formulario y `detail` para los toasts.

## Arquitectura

```
app/
├── api/         # routers: auth, categories, tasks, dashboard, deps
├── core/        # config, security, dates, error_handlers, logging
├── models/      # SQLAlchemy
├── schemas/     # Pydantic (CamelModel)
├── services/    # auth_service, task_query_service
└── main.py
alembic/         # migraciones
tests/
```

## Decisiones técnicas

| Decisión | Motivo |
|---|---|
| Access JWT corto + refresh opaco rotatorio | Limita el daño de un robo de token y permite revocar sesiones |
| Refresh en cookie httpOnly | JavaScript no puede leerlo (mitiga XSS) |
| Hash del refresh en BD | Una fuga de la BD no expone sesiones válidas |
| 404 en vez de 403 | No revela la existencia de recursos de otros usuarios |
| Argon2id | Algoritmo de hash de contraseñas recomendado |
| SQLAlchemy síncrono | Más simple; suficiente para esta escala |
| Paginación en servidor con orden estable | Evita duplicados/saltos entre páginas |
| Imágenes en disco, validadas con Pillow | Simplicidad; no se confía en la extensión ni el MIME del cliente |
| Alembic con `compare_type` | Detecta cambios de tipo en las migraciones |

## Tests y calidad

```bash
cp .env.test.example .env.test   # apunta a taskflow_test_db
pytest --cov=app
ruff check . && ruff format --check .
pre-commit install
```

Cobertura actual: **92 %** (30+ tests).

## Limitaciones conocidas

- No hay usuario administrador precargado.
- Sin rate limiting en login.
- Algunos mensajes de validación de Pydantic están en inglés.
- Las imágenes se sirven desde disco local (no apto para varias instancias).
- La cookie `Secure` solo se activa bajo HTTPS (`COOKIE_SECURE=true`).

## Roadmap

- [ ] Fase D: Docker y Docker Compose (API + PostgreSQL + frontend).
- [ ] Mensajes de validación en español.
- [ ] Rate limiting en autenticación.
- [ ] Almacenamiento de imágenes en objeto (S3 o similar).
- [ ] Script de seed de datos de demo.