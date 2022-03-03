from typing import List, Union

from shapely.geometry import LineString

from app.misc.geometry_handling import linestring_length_in_meter
from app.schemas.fuel import DrivingStyles


class BaseFuelCalculator:
    def __init__(
        self,
        geometry: LineString,
        tank_size: Union[int, None] = None,
        driving_style: DrivingStyles = DrivingStyles.moderate,
        manual_fuel_consumption: Union[float, None] = None,
        request_id: Union[str, None] = None,
    ):
        """Initializes the basic calculation object."""
        self.geometry: LineString = geometry

        self.tank_size: Union[int, None] = tank_size
        self.driving_style: DrivingStyles = driving_style
        self.manual_fuel_consumption: Union[float, None] = manual_fuel_consumption
        self.request_id: Union[str, None] = request_id

        self.categories: List = []
        # self.price_models: Union[
        #     EurostatGeneralPrice, EurostatCountryPrice
        # ] = parse_price_model(self.geom)
        self.route_length: Union[float, None] = linestring_length_in_meter(
            linestring=self.geometry
        )
        self.fuel_models = None

    def calculate_cost(self) -> None:
        pass
