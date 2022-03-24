# from typing import Any, List, Union
#
# from app.fuel_calculations.base_fuel_calculator import BaseFuelCalculator
#
#
# class CarFuelDataFuelCalculator(BaseFuelCalculator):
#     def __init__(self, carfueldata_car_ids: List[str], **kwargs: Union[Any]):
#         """
#         Keyword Args:
#             geometry: LineString,
#             tank_size: Union[int, None] = None,
#             driving_style: DrivingStyles = DrivingStyles.moderate,
#             manual_fuel_consumption: Union[float, None] = None,
#             request_id: Union[str, None] = None,
#         """
#         # Get the cfd car by id. include the car details into the super call.
#         self._carfueldata_car_ids: List[str] = carfueldata_car_ids
#         super().__init__(**kwargs)
#
#     def calculate_cost(self) -> Union[int, None]:
#         pass
