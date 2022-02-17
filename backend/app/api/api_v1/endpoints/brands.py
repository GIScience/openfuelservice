from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import schemas
from app.api import deps
from app.models import CarFuelDataCar

router = APIRouter()


@router.get("/", response_model=schemas.Brands)
async def read_brands(db: Session = Depends(deps.get_db)) -> Any:
    """Request the available brands for fuel calculations."""
    return {
        "data": [
            value for (value,) in db.query(CarFuelDataCar.manufacturer).distinct().all()
        ]
    }


@router.get(
    "/{brand}/cars", response_model=schemas.Cars, description="Return cars by brand."
)
async def read_cars_by_brand(brand: str, db: Session = Depends(deps.get_db)) -> Any:
    """Request the available models for fuel calculations."""
    results = (
        db.query(CarFuelDataCar).filter(CarFuelDataCar.manufacturer.like(brand)).all()
    )
    if not results:
        raise HTTPException(status_code=404, detail=f"No cars found for brand: {brand}")
    return {"data": results}


@router.get(
    "/{brand}/cars/sorted",
    response_model=schemas.CarsSorted,
    description="Return cars by brand ordered after Model and year.",
)
async def read_cars_by_brand_sorted_by_model_and_year(
    brand: str, db: Session = Depends(deps.get_db)
) -> Any:
    """Request the available models for fuel calculations."""
    results: Dict = {"ids": []}
    database_entries: List = db.query(CarFuelDataCar).filter(
        CarFuelDataCar.manufacturer.like(brand)
    ).all()
    if not database_entries:
        raise HTTPException(status_code=404, detail=f"No cars found for brand: {brand}")
    entry: CarFuelDataCar
    for entry in database_entries:
        database_entries.remove(entry)
        if entry.model not in results:
            results[entry.model] = {}
            results[entry.model]["ids"] = []
        if entry.year not in results[entry.model]:
            results[entry.model][entry.year] = {}
            results[entry.model][entry.year]["cars"] = []
            results[entry.model][entry.year]["ids"] = []
        results[entry.model][entry.year]["cars"].append(
            {
                "id": entry.id,
                "manufacturer": entry.manufacturer,
                "model": entry.model,
                "description": entry.description,
                "fuel_type": entry.fuel_type,
                "year": entry.year,
            }
        )
        results["ids"].append(entry.id)
        results[entry.model]["ids"].append(entry.id)
        results[entry.model][entry.year]["ids"].append(entry.id)

    return {"data": results}
