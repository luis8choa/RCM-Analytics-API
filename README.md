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