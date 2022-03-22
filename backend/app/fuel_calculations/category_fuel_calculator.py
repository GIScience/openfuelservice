# from typing import Any, List, Union
#
# from sqlalchemy.orm import Session
#
# from app.fuel_calculations.base_fuel_calculator import BaseFuelCalculator
#
#
# class CategoryFuelCalculator(BaseFuelCalculator):
#     def __init__(self, db: Session, car_category_ids: List[str], **kwargs: Union[Any]):
#         """
#         Keyword Args:
#             geometry: LineString,
#             tank_size: Union[int, None] = None,
#             driving_style: DrivingStyles = DrivingStyles.moderate,
#             manual_fuel_consumption: Union[float, None] = None,
#             request_id: Union[str, None] = None,
#         """
#         # Get the cfd car by id. include the car details into the super call.
#         self._car_category_ids: List[str] = car_category_ids
#         self._db: Session = db
#         super().__init__(**kwargs)
#
#     def calculate_cost(self) -> None:
#         pass
