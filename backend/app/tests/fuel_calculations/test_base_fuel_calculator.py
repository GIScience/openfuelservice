import pytest
from sqlalchemy.orm import Session

from app.fuel_calculations.base_fuel_calculator import BaseFuelCalculator
from app.schemas.fuel import DrivingStyles


@pytest.mark.parametrize(
    "tank_size,driving_style,manual_fuel_consumption,expected_route_length",
    [
        (
            10,
            DrivingStyles.moderate,
            4.5,
            567.6399544896653,
        ),
        (
            10,
            DrivingStyles.moderate,
            4.5,
            567.6399544896653,
        ),
        (10, DrivingStyles.moderate, 4.5, None),
        (None, None, None, None),
    ],
)
def test_base_fuel_calculator(
    db: Session,
    tank_size: int,
    driving_style: DrivingStyles,
    manual_fuel_consumption: float,
    expected_route_length: float,
) -> None:
    test = BaseFuelCalculator(
        db=db,
        envirocar_car_ids=[],
        tank_size=tank_size,
        driving_style=driving_style,
        manual_fuel_consumption=manual_fuel_consumption,
    )
    assert test._tank_size == tank_size
    assert test._driving_style == driving_style
    assert test._manual_fuel_consumption == manual_fuel_consumption
    assert test._fuel_model
