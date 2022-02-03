from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app import schemas
from app.api import deps
from app.models import CarFuelDataCar

router = APIRouter()


@router.get("/", response_model=schemas.Brands)
def read_brands(db: Session = Depends(deps.get_db)) -> Any:
    """Request the available models for fuel calculations."""
    return {"brands": [value for (value,) in db.query(CarFuelDataCar.manufacturer).distinct().all()]}
