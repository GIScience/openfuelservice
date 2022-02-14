from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import schemas
from app.api import deps
from app.models import WikiCarCategory

router = APIRouter()


@router.get("/", response_model=schemas.Categories)
async def read_categories(db: Session = Depends(deps.get_db)) -> Any:
    """Request the available categories for fuel calculations."""
    return {"data": db.query(WikiCarCategory).distinct().all()}
