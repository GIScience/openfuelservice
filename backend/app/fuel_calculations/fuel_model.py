import logging
from enum import Enum
from statistics import median
from typing import List, Set, Tuple, Union

from fastapi import HTTPException
from scipy.interpolate import interp1d

from app.db.importer.mappings import FuelMappings
from app.models import EnvirocarSensor, EnvirocarSensorStatistic
from app.schemas.fuel import FuelCalculationResults

logger = logging.getLogger(__name__)


class FuelModel:
    def __init__(self, statistics: List[EnvirocarSensorStatistic]):
        # Set statistical minimum values for co2 that must be met.
        self._minimum_gasoline_co2_gram_emission = 2392
        self._minimum_diesel_co2_gram_emission = 2640
        self._fuel_type: Union[Enum, None] = None
        self._consumption_interpolator: Union[interp1d, None] = None
        self._co2_interpolator: Union[interp1d, None] = None
        self._co2_statistics: List = [
            statistic for statistic in statistics if statistic.name == "CO2"
        ]
        self._speed_statistics: List = [
            statistic for statistic in statistics if statistic.name == "Speed"
        ]
        self._consumption_statistics: List = [
            statistic for statistic in statistics if statistic.name == "Consumption"
        ]
        self.__clean_models()
        self._initialize_interpolators()

    def __clean_models(self) -> None:
        if (
            not len(self._co2_statistics)
            or not len(self._speed_statistics)
            or not len(self._consumption_statistics)
        ):
            logger.warning("Couldn't create statistics model. Flushing all.")
            self._co2_statistics = []
            self._speed_statistics = []
            self._consumption_statistics = []
            return
        co2_statistics: List = self._co2_statistics
        speed_statistics: List = self._speed_statistics
        consumption_statistics: List = self._consumption_statistics
        self._co2_statistics = []
        self._speed_statistics = []
        self._consumption_statistics = []

        fuel_types: Set = set()
        statistic: EnvirocarSensorStatistic
        for statistic in consumption_statistics:
            ec_sensor: EnvirocarSensor = statistic.envirocar
            fuel_types.add(ec_sensor.fueltype)
            if len(fuel_types) > 1:
                raise HTTPException(
                    status_code=400,
                    detail="Don't mix fuel types for fuel calculation requests.",
                )
            sub_statistic: EnvirocarSensorStatistic
            found: bool = True
            for sub_statistic in co2_statistics:
                if not sub_statistic.id == statistic.id:
                    found = False
                else:
                    found = True
                    self._co2_statistics.append(sub_statistic)
                    break
            for sub_statistic in speed_statistics:
                if not sub_statistic.id == statistic.id:
                    found = False
                else:
                    found = True
                    self._speed_statistics.append(sub_statistic)
                    break
            if found:
                self._consumption_statistics.append(statistic)
        self._fuel_type = FuelMappings.from_value(fuel_types.pop())

    @staticmethod
    def _get_statistics(
        statistics: List[EnvirocarSensorStatistic],
    ) -> Tuple[Union[float, None], Union[float, None], Union[float, None]]:
        if not statistics or len(statistics) == 0:
            return None, None, None
        consumption_values_max: List[float] = []
        consumption_values_avg: List[float] = []
        consumption_values_min: List[float] = []
        statistic: EnvirocarSensorStatistic
        for statistic in statistics:
            consumption_values_max.append(float(statistic.max))
            consumption_values_avg.append(float(statistic.avg))
            consumption_values_min.append(float(statistic.min))
        return (
            median(consumption_values_max),
            median(consumption_values_avg),
            median(consumption_values_min),
        )

    def _initialize_interpolators(self) -> None:
        speed_statistics: Tuple[
            Union[float, None], Union[float, None], Union[float, None]
        ] = self._get_statistics(statistics=self._speed_statistics)
        consumption_statistics: Tuple[
            Union[float, None], Union[float, None], Union[float, None]
        ] = self._get_statistics(statistics=self._consumption_statistics)
        co2_statistics: Tuple[
            Union[float, None], Union[float, None], Union[float, None]
        ] = self._get_statistics(statistics=self._co2_statistics)
        if any(
            statistic == (None, None, None)
            for statistic in [speed_statistics, consumption_statistics, co2_statistics]
        ):
            return
        self._consumption_interpolator = interp1d(
            speed_statistics,
            consumption_statistics,
            kind="quadratic",
            bounds_error=False,
            fill_value="interpolate",
        )
        self._co2_interpolator = interp1d(
            speed_statistics,
            co2_statistics,
            kind="quadratic",
            bounds_error=False,
            fill_value="interpolate",
        )

    def _set_interpolators_fill_value(self, kmh: float) -> None:
        if self._consumption_interpolator is None or self._co2_interpolator is None:
            return
        if kmh > 0 and kmh > self._consumption_interpolator.x.max():
            self._consumption_interpolator.fill_value = "extrapolate"
            self._co2_interpolator.fill_value = "extrapolate"
        else:
            self._consumption_interpolator.fill_value = "interpolate"
            self._co2_interpolator.fill_value = "interpolate"

    def calculate_fuel(
        self, kmh: float, length_in_meter: float
    ) -> FuelCalculationResults:
        if kmh <= 0 or length_in_meter <= 0:
            return FuelCalculationResults(
                fuel_type=self._fuel_type,
                fuel_liter_total=0,
                fuel_liter_per_100km=0,
                co2_gram_total=0,
                co2_gram_per_km=0,
            )
        self._set_interpolators_fill_value(kmh=kmh)
        length_in_km = length_in_meter * 0.0010000
        consumption_liter_per_kmh: float = (
            self._consumption_interpolator(kmh)
            if self._consumption_interpolator is not None
            else 0.0
        )
        consumption_liter_per_km: float = consumption_liter_per_kmh / kmh

        co2_kg_per_kmh = (
            self._co2_interpolator(kmh) if self._co2_interpolator is not None else 0.0
        )
        co2_kg_per_km = co2_kg_per_kmh / kmh
        co2_gram_per_km = co2_kg_per_km * 1000

        result_consumption_liter_total: float = length_in_km * consumption_liter_per_km
        result_co2_gram_total: float = co2_gram_per_km * length_in_km
        return FuelCalculationResults(
            fuel_type=self._fuel_type,
            fuel_liter_total=result_consumption_liter_total,
            fuel_liter_per_100km=consumption_liter_per_km * 100,
            co2_gram_total=result_co2_gram_total,
            co2_gram_per_km=co2_gram_per_km,
        )
