import logging
from typing import Any, Union

from app.fuel_calculations.base_fuel_calculator import BaseFuelCalculator

logger = logging.getLogger(__name__)


class EnvirocarFuelCalculator(BaseFuelCalculator):
    def __init__(self, **kwargs: Union[Any]):
        """
        Keyword Args:
            db: Session,
            envirocar_car_ids: List[str],
            tank_size: Union[int, None] = None,
            driving_style: DrivingStyles = DrivingStyles.moderate,
            manual_fuel_consumption: Union[float, None] = None,
        """
        # Get the cfd car by id. include the car details into the super call.
        super().__init__(**kwargs)
