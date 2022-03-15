from typing import Any, List, Union

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app.api import deps
from app.fuel_calculations.carfueldata_fuel_calculator import CarFuelDataFuelCalculator
from app.models import CarFuelDataCar
from app.schemas import FuelRequestCars

router = APIRouter()


@router.get("/", response_model=schemas.Cars, description="Return all cars.")
async def read_cars(db: Session = Depends(deps.get_db)) -> Any:
    """Request the available models for fuel calculations."""
    results = db.query(CarFuelDataCar).all()
    if not results:
        raise HTTPException(status_code=404, detail="No cars found in database.")
    return {"data": results}


@router.get(
    "/{vehicle_id}",
    response_model=schemas.CarResponse,
    description="Return a car by id.",
)
async def read_car_by_id(vehicle_id: str, db: Session = Depends(deps.get_db)) -> Any:
    """Request the available models for fuel calculations."""
    result = db.query(CarFuelDataCar).filter(CarFuelDataCar.id == vehicle_id).first()
    if not result:
        raise HTTPException(
            status_code=404, detail=f"No car found for id: {vehicle_id}"
        )
    return {"data": result}


@router.post(
    "/fuel",
    response_model=schemas.FuelResponse,
    description="Return emission and cost calculations by car id.",
)
async def calculate_emissions_and_cost_by_id(
    request_in: FuelRequestCars,
    db: Session = Depends(deps.get_db),
) -> Any:
    """Request the available models for fuel calculations."""
    cars: List[CarFuelDataCar] = CarFuelDataCar.get_all_by_filter(
        db=db, filter_ids=request_in.car_ids, id_only=False
    )
    if not cars:
        raise HTTPException(
            status_code=404, detail=f"No car found for IDs: {request_in.car_ids}"
        )
    result: Union[int, None] = CarFuelDataFuelCalculator(
        carfueldata_car_ids=[car.id for car in cars], kwargs=dict(request_in)
    ).calculate_cost()

    if not result:
        raise HTTPException(
            status_code=404, detail=f"No car found for IDs: {request_in.car_ids}"
        )
    return {"data": result}
