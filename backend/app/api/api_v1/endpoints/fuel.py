from typing import Any, List, Union

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app.api import deps
from app.fuel_calculations.envirocar_fuel_calculator import EnvirocarFuelCalculator
from app.models import EnvirocarSensor
from app.schemas import ORSFeatureCollection
from app.schemas.fuel import FuelCalculationResults, OpenrouteserviceFuelRequest

router = APIRouter()


@router.post(
    "/envirocar/openrouteservice",
    response_model=schemas.FuelResponseEncapsulated,
    description="Return emission and cost calculations by car id.",
)
async def calculate_fuel_by_id_openrouteservice(
    request_in: OpenrouteserviceFuelRequest,
    db: Session = Depends(deps.get_db),
) -> Any:
    """Request the available models for fuel calculations."""
    cars: List[EnvirocarSensor] = EnvirocarSensor.get_all_by_filter(
        db=db, filter_ids=request_in.car_ids, id_only=False
    )
    if not cars:
        raise HTTPException(
            status_code=404, detail=f"No car found for IDs: {request_in.car_ids}"
        )
    result: Union[FuelCalculationResults, None] = EnvirocarFuelCalculator(
        envirocar_car_ids=[car.id for car in cars],
        tank_size=request_in.tank_size,
        driving_style=request_in.driving_style,
        db=db,
    ).calculate_fuel_for_openrouteservice_response(
        ORSFeatureCollection.parse_obj(request_in.geometry)
    )

    if not result:
        raise HTTPException(
            status_code=404, detail=f"No car found for IDs: {request_in.car_ids}"
        )
    return {"data": result}
