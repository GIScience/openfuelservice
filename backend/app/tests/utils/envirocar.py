import datetime
import random
from typing import Dict

from sqlalchemy.orm import Session

from app import crud, models
from app.schemas.envirocar_sensor import SensorCreate
from app.schemas.track import TrackCreate
from app.schemas.track_measurement import TrackMeasurementCreate


def create_random_sensor(
    db: Session,
    sensor_type: str = None,
    sensor_model: str = None,
    manufacturer: str = None,
    fueltype: str = None,
    constructionyear: int = None,
    enginedisplacement: int = None,
) -> models.EnvirocarSensor:
    unique_number = random.randint(1000, 9999)
    sensor_in = SensorCreate(
        id=unique_number,
        type=f"type_{unique_number}" if sensor_type is None else sensor_type,
        model=f"model_{unique_number}" if sensor_model is None else sensor_model,
        manufacturer=f"manufacturer_{unique_number}"
        if manufacturer is None
        else manufacturer,
        fueltype=f"fueltype_{unique_number}" if fueltype is None else fueltype,
        constructionyear=unique_number
        if constructionyear is None
        else constructionyear,
        enginedisplacement=unique_number
        if enginedisplacement is None
        else enginedisplacement,
    )

    return crud.sensor.create(db=db, obj_in=sensor_in)


def create_random_track(
    db: Session, sensor: models.EnvirocarSensor
) -> models.EnvirocarTrack:
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
    item = crud.track.create(db=db, obj_in=track_in)

    return item


def create_random_track_measurement(
    db: Session, track: models.EnvirocarTrack
) -> models.EnvirocarTrackMeasurement:
    unique_number = random.randint(1000, 9999)
    track_measurement_geometry: Dict = {"type": "Point", "coordinates": [30, 10]}
    track_in = TrackMeasurementCreate(
        id=unique_number,
        geom=track_measurement_geometry,
        track_id=track.id,
        time=datetime.datetime.now(),
    )
    item = crud.track_measurement.create(db=db, obj_in=track_in)

    return item
