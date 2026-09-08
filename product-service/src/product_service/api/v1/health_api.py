# ruff: noqa: BLE001
from fastapi import APIRouter, status, Depends, HTTPException
from product_service.dependencies.session import get_session
from sqlalchemy import text

router = APIRouter()

@router.get("/live", status_code=status.HTTP_200_OK)
def live():
    return {"status": "alive"}

@router.get("/ready")
async def ready(db=Depends(get_session)):
    # Perform a simple database query to check if the database is reachable
    try:
        await db.execute(text("SELECT 1;"))
        return {"status": "ready"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable"
        )