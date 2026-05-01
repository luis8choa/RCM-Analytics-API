# RCM-Analytics-API

# Agregar una nueva dependencia en el futuro
uv add nombre-del-paquete

# Agregar dependencia solo para dev
uv add --dev nombre-del-paquete

# Correr la API
uv run uvicorn app.main:app --reload

# Correr los tests
uv run pytest

# Lint
uv run ruff check .

# Levantar el contenedor en background
docker compose up -d

# Verificar que está corriendo y saludable
docker compose ps

# Ver los logs si algo falla
docker compose logs db

# Verificar que acepta conexiones
docker exec rcm_postgres pg_isready -U rcm_user -d rcm_analytics

# Detener y eliminar contenedor + volumen
docker compose down -v

# Volver a levantar limpio
docker compose up -d

Con todo listo, los comandos para ejecutar la semana 2 completa en orden:
bash
# 1. Generar la primera migración
uv run alembic revision --autogenerate -m "create initial tables"

# 2. Aplicar la migración a Postgres
uv run alembic upgrade head

# 3. Verificar que las tablas existen
docker exec rcm_postgres psql -U rcm_user -d rcm_analytics -c "\dt"

# 4. Correr el seed
uv run python seed.py

# 5. Verificar que hay datos
docker exec rcm_postgres psql -U rcm_user -d rcm_analytics -c "SELECT COUNT(*) FROM claims;"