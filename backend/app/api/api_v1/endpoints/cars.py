from typing import Any, Union

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app.api import deps
from app.models import CarFuelDataCar, EnvirocarSensor

router = APIRouter()


@router.get("/", response_model=schemas.Cars, description="Return all cars.")
async def read_cars(db: Session = Depends(deps.get_db)) -> Any:
    """Request the available models for fuel calculations."""
    results = db.query(CarFuelDataCar).all()
    if not results:
        raise HTTPException(status_code=404, detail="No cars found in database.")
    return {"data": results}


@router.get(
    "/carfueldata/{vehicle_id}",
    response_model=schemas.CarResponse,
    description="Return a car by id.",
)
async def read_carfueldata_car_by_id(
    vehicle_id: str, db: Session = Depends(deps.get_db)
) -> Any:
    """Request the available models for fuel calculations."""
    result = db.query(CarFuelDataCar).filter(CarFuelDataCar.id == vehicle_id).first()
    if not result:
        raise HTTPException(
            status_code=404, detail=f"No car found for id: {vehicle_id}"
        )
    return {"data": result}


@router.get(
    "/envirocar/{vehicle_id}",
    response_model=schemas.SensorResponse,
    description="Return a car by id.",
)
async def read_envirocar_car_by_id(
    vehicle_id: str, db: Session = Depends(deps.get_db)
) -> Any:
    """Request the available models for fuel calculations."""
    result: Union[EnvirocarSensor, None] = (
        db.query(EnvirocarSensor).filter(EnvirocarSensor.id == vehicle_id).first()
    )
    if not result:
        raise HTTPException(
            status_code=404, detail=f"No car found for id: {vehicle_id}"
        )
    return {"data": result}
