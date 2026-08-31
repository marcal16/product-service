from fastapi import FastAPI
from .api.v1.router import router as v1_router
from .core.logs import setup_logging

setup_logging()

app = FastAPI()
app.include_router(v1_router)