from fastapi import APIRouter, status, Depends
from product_service.dependencies.session import get_db

router = APIRouter()

@router.get("/live", status_code=status.HTTP_200_OK)
def live():
    return {"status": "alive"}

@router.get("/ready", status_code=status.HTTP_200_OK)
async def ready(db=Depends(get_db)):
    # Perform a simple database query to check if the database is reachable
    try:
        await db.execute("SELECT 1")
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not ready", "error": str(e)}