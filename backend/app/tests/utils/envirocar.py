import datetime
import random
from typing import Dict, List

from sqlalchemy.orm import Session

from app import crud
from app.db.importer.mappings import FuelMappings
from app.models import (
    CarFuelDataCar,
    EnvirocarSensor,
    EnvirocarTrack,
    EnvirocarTrackMeasurement,
)
from app.schemas.envirocar_sensor import SensorCreate
from app.schemas.track import TrackCreate
from app.schemas.track_measurement import TrackMeasurementCreate


def create_sensors_by_cfd(
    db: Session, cfd_cars: List[CarFuelDataCar]
) -> List[EnvirocarSensor]:
    cfd_car: CarFuelDataCar
    random_ids: List = random.sample(range(1, len(cfd_cars) + 1), len(cfd_cars))  # type: ignore
    sensors: List = []
    for cfd_car in cfd_cars:
        unique_id = random_ids.pop()
        fuel_type = FuelMappings.from_value(cfd_car.fuel_type)
        if fuel_type is None or cfd_car.engine_capacity is None:
            pass
        sensor_in: SensorCreate = SensorCreate(
            id=unique_id,
            type=f"type_{unique_id}",
            model=cfd_car.model,
            manufacturer=cfd_car.manufacturer,
            fueltype=fuel_type.name.lower(),  # type: ignore
            constructionyear=cfd_car.year,
            enginedisplacement=0
            if fuel_type == FuelMappings.ELECTRIC or cfd_car.engine_capacity is None
            else cfd_car.engine_capacity,
        )
        sensors.append(sensor_in)

    return crud.envirocar_sensor.create_many(db=db, objs_in=sensors)


def create_random_sensor(
    db: Session,
    unique_id: int = random.randint(1000, 9999),
    sensor_type: str = None,
    sensor_model: str = None,
    manufacturer: str = None,
    fueltype: str = "",
    constructionyear: int = None,
    enginedisplacement: int = None,
) -> EnvirocarSensor:
    fuel_type = FuelMappings.from_value(fueltype)
    sensor_in = SensorCreate(
        id=unique_id,
        type=f"type_{unique_id}" if sensor_type is None else sensor_type,
        model=f"model_{unique_id}" if sensor_model is None else sensor_model,
        manufacturer=f"manufacturer_{unique_id}"
        if manufacturer is None
        else manufacturer,
        fueltype=f"fueltype_{unique_id}"
        if fuel_type is None
        else fuel_type.name.lower(),
        constructionyear=unique_id if constructionyear is None else constructionyear,
        enginedisplacement=unique_id
        if enginedisplacement is None
        else enginedisplacement,
    )

    return crud.envirocar_sensor.create(db=db, obj_in=sensor_in)


def create_random_track(db: Session, sensor: EnvirocarSensor) -> EnvirocarTrack:
    unique_number = random.randint(1000, 9999)
    track_geometry: Dict = {
        "type": "LineString",
        "coordinates": [[30, 10], [10, 30], [40, 40]],
    }
    track_in = TrackCreate(
        id=unique_number,
        sensor_id=sensor.id,
        length=100,
        begin=datetime.datetime.now(),
        end=datetime.datetime.now() + +datetime.timedelta(hours=1),
        geom=track_geometry,
    )
    item = crud.envirocar_track.create(db=db, obj_in=track_in)

    return item


def create_random_track_measurement(
    db: Session, track: EnvirocarTrack
) -> EnvirocarTrackMeasurement:
    unique_number = random.randint(1000, 9999)
    track_measurement_geometry: Dict = {"type": "Point", "coordinates": [30, 10]}
    track_in = TrackMeasurementCreate(
        id=unique_number,
        geom=track_measurement_geometry,
        track_id=track.id,
        time=datetime.datetime.now(),
    )
    item = crud.envirocar_track_measurement.create(db=db, obj_in=track_in)

    return item
