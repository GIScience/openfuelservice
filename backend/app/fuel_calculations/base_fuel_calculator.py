import logging
from typing import List, Union

from shapely.geometry import LineString
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.fuel_calculations.fuel_model import FuelModel
from app.models import EnvirocarPhenomenon, EnvirocarSensor, EnvirocarSensorStatistic
from app.schemas import ORSFeatureCollection
from app.schemas.fuel import DrivingStyles, FuelCalculationResults

logger = logging.getLogger(__name__)


class BaseFuelCalculator:
    def __init__(
        self,
        db: Session,
        envirocar_car_ids: List[str],
        geometry: Union[LineString, ORSFeatureCollection],
        tank_size: Union[int, None] = None,
        driving_style: DrivingStyles = DrivingStyles.moderate,
        manual_fuel_consumption: Union[float, None] = None,
        request_id: Union[str, None] = None,
    ):
        """Initializes the basic calculation object."""
        self._db: Session = db
        self._geometry: Union[LineString, ORSFeatureCollection] = geometry
        self._tank_size: Union[int, None] = tank_size
        self._driving_style: DrivingStyles = driving_style
        self._manual_fuel_consumption: Union[float, None] = manual_fuel_consumption
        self._request_id: Union[str, None] = request_id
        self._envirocar_car_ids: List[str] = envirocar_car_ids
        self._envirocar_cars: List[EnvirocarSensor] = EnvirocarSensor.get_all_by_filter(
            db, self._envirocar_car_ids, id_only=False
        )
        sensors_statistics = (
            self._db.query(EnvirocarSensorStatistic)
            .filter(
                or_(
                    EnvirocarSensorStatistic.name == "CO2",
                    EnvirocarSensorStatistic.name == "Consumption",
                    EnvirocarSensorStatistic.name == "Speed",
                ),
                and_(EnvirocarSensorStatistic.id.in_(self._envirocar_car_ids)),
            )
            .join(
                EnvirocarPhenomenon,
                EnvirocarPhenomenon.name == EnvirocarSensorStatistic.name,
            )
            .all()
        )
        self._fuel_model: FuelModel = FuelModel(sensors_statistics)
        # self._price_models: [CountryLinePrice or GeneralLinePrice] = parse_price_model(self.geom)

    def calculate_fuel(
        self, kmh: float, length_in_meter: float
    ) -> FuelCalculationResults:
        return self._fuel_model.calculate_fuel(kmh=kmh, length_in_meter=length_in_meter)
