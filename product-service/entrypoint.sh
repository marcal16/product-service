#!/bin/sh

poetry run alembic upgrade head

poetry run uvicorn product_service.main:app --host 0.0.0.0 --port 8000 --app-dir src