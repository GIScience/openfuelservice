import json
from pathlib import Path
from typing import Dict, List, Tuple

import pytest
import responses
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.importer.envirocar.envirocar_reader import EnvirocarReader
from app.models import (
    EnvirocarPhenomenon,
    EnvirocarSensor,
    EnvirocarSensorStatistic,
    EnvirocarTrack,
    EnvirocarTrackMeasurement,
    EnvirocarTrackMeasurementPhenomenon,
    WikiCar,
    WikiCarCategory,
    WikicarEnvirocar,
)

track_ids = [
    "61d543bef4c3e97fbd560705",
    "61d543bef4c3e97fbd56072d",
    "619b972b7b277d59bd6537fc",
]


@pytest.mark.asyncio
async def test_get_track_measurements_and_phenomenons(
    db: Session,
    mock_all_responses: responses.RequestsMock,
) -> None:
    envirocar_reader: EnvirocarReader = EnvirocarReader(
        db=db,
        file_or_url=Path(""),
        threads=None,
    )
    track_ids: List = ["61d543bef4c3e97fbd560705", "61d543bef4c3e97fbd56072d"]
    (
        track_measurements,
        track_measurements_phenomenons,
    ) = envirocar_reader.fetch_track_measurements_and_phenomenons(track_ids=track_ids)

    # Check measurements
    assert len(track_measurements) == 101
    track_measurements_ids: Dict = {}
    track_measurement: EnvirocarTrackMeasurement
    for track_measurement in track_measurements:
        assert isinstance(track_measurement, EnvirocarTrackMeasurement)
        assert track_measurement.id
        assert track_measurement.track_id
        assert track_measurement.track_id in track_ids
        assert track_measurement.geom
        assert track_measurement.time
        assert track_measurement.id not in track_measurements_ids
        track_measurements_ids[track_measurement.id] = set()

    # Check phenomenons
    assert len(track_measurements_phenomenons) == 1111
    track_measurements_phenomenon: EnvirocarTrackMeasurementPhenomenon
    for track_measurements_phenomenon in track_measurements_phenomenons:
        assert isinstance(
            track_measurements_phenomenon, EnvirocarTrackMeasurementPhenomenon
        )
        assert track_measurements_phenomenon.id
        assert track_measurements_phenomenon.id in track_measurements_ids
        assert track_measurements_phenomenon.name
        assert track_measurements_phenomenon.unit
        assert track_measurements_phenomenon.value is not None

        phenomenon_primary_key = (
            f"{track_measurements_phenomenon.id}{track_measurements_phenomenon.name}"
        )
        assert (
            phenomenon_primary_key
            not in track_measurements_ids[track_measurements_phenomenon.id]
        )
        track_measurements_ids[track_measurements_phenomenon.id].add(
            phenomenon_primary_key
        )


@pytest.mark.asyncio
async def test_get_track_ids_and_sensors(
    db: Session,
    mock_all_responses: responses.RequestsMock,
) -> None:
    envirocar_reader: EnvirocarReader = EnvirocarReader(
        db=db,
        file_or_url=Path(""),
        threads=None,
    )
    with open(settings.TEST_ENVIROCAR_TRACKS_RESPONSE, mode="r") as f:
        tracks_response = json.load(f)
        number_of_tracks: int = len(tracks_response["tracks"])

    sensors, tracks, tracks_ids = envirocar_reader.fetch_track_ids_and_sensors()
    # Check sensors and track_ids response
    assert len(sensors) == 3
    assert isinstance(sensors[0], EnvirocarSensor)
    sensor: EnvirocarSensor = sensors[0]
    assert sensor.id == "5fd9d14e05fa792e88dc8b7b"
    assert sensor.constructionyear == 2006
    assert sensor.enginedisplacement == 1595
    assert sensor.fueltype == "gasoline"
    assert sensor.manufacturer == "VW"
    assert sensor.model == "Golf V Plus 1.6"
    assert sensor.type == "car"

    assert len(tracks_ids) == number_of_tracks
    assert [track_id in tracks_ids for track_id in tracks_ids]
    assert len(tracks) == number_of_tracks

    sensor_ids: List[str] = [sensor.id for sensor in sensors]
    track: EnvirocarTrack
    for track in tracks:
        assert track.id in tracks_ids
        assert track.sensor_id in sensor_ids
        assert track.begin
        assert track.end
        assert track.length

    assert isinstance(sensors[1], EnvirocarSensor)
    sensor = sensors[1]
    assert sensor.id == "616010fb0bd6756ea3a9aea7"
    assert sensor.constructionyear == 2009
    assert sensor.enginedisplacement == 1398
    assert sensor.fueltype == "diesel"
    assert sensor.manufacturer == "OPEL"
    assert sensor.model == "Corsa"
    assert sensor.type == "car"


@pytest.mark.asyncio
async def test_get_phenomenons(
    db: Session, mock_all_responses: responses.RequestsMock
) -> None:
    envirocar_reader: EnvirocarReader = EnvirocarReader(
        db=db,
        file_or_url=Path(""),
        threads=None,
    )

    phenomenons = envirocar_reader.fetch_phenomenons()
    # Check sensors and track_ids response
    assert len(phenomenons) == 32
    for phenomenon in phenomenons:
        assert isinstance(phenomenon, EnvirocarPhenomenon)
        assert phenomenon.name
        assert phenomenon.unit


@pytest.mark.asyncio
async def test_get_sensors(
    db: Session, mock_all_responses: responses.RequestsMock
) -> None:
    envirocar_reader: EnvirocarReader = EnvirocarReader(
        db=db,
        file_or_url=Path(""),
        threads=None,
    )
    sensors = envirocar_reader.get_sensors()
    # Check sensors and track_ids response
    assert len(sensors) == 172
    sensor: EnvirocarSensor
    for sensor in sensors:
        assert isinstance(sensor, EnvirocarSensor)
        assert sensor.id
        assert sensor.constructionyear
        if sensor.enginedisplacement:
            assert int(sensor.enginedisplacement)
        assert sensor.fueltype
        assert sensor.manufacturer
        assert sensor.model
        assert sensor.type


@pytest.mark.asyncio
async def test_get_sensor_statistics(db: Session) -> None:
    envirocar_reader: EnvirocarReader = EnvirocarReader(
        db=db,
        file_or_url=Path(""),
        threads=None,
    )
    sensors, tracks, track_ids = envirocar_reader.fetch_track_ids_and_sensors()
    sensor_ids: List = [sensor.id for sensor in sensors]
    sensors_statistics = envirocar_reader.fetch_sensor_statistics(sensor_ids)
    assert len(sensors_statistics) == 59
    sensor_statistic: EnvirocarSensorStatistic
    for sensor_statistic in sensors_statistics:
        assert isinstance(sensor_statistic, EnvirocarSensorStatistic)
        assert sensor_statistic.id
        assert any(sensor.id == sensor_statistic.id for sensor in sensors)
        assert sensor_statistic.min >= 0
        assert sensor_statistic.avg >= 0
        assert sensor_statistic.max >= 0
        assert sensor_statistic.measurements > 0
        assert sensor_statistic.sensors == 1
        assert sensor_statistic.tracks > 0


@pytest.mark.asyncio
async def test_match_sensors_to_wikicar(
    db: Session,
    mock_wikipedia_objects: Tuple[List[WikiCarCategory], List[WikiCar]],
    mock_all_responses: responses.RequestsMock,
) -> None:
    envirocar_reader: EnvirocarReader = EnvirocarReader(
        db=db,
        file_or_url=Path(""),
        threads=None,
    )
    # TODO remove all sensors except one a wikicar is available for.#
    sensors, tracks, track_ids = envirocar_reader.fetch_track_ids_and_sensors()
    # Check sensors and track_ids response
    assert len(sensors)
    matched_sensors = await envirocar_reader.match_sensors_to_wikicar(
        sensors=sensors, accuracy=0.2
    )
    assert len(matched_sensors) == 2


@pytest.mark.asyncio
async def test_fetch_and_process_data(
    db: Session,
    mock_wikipedia_objects: Tuple[List[WikiCarCategory], List[WikiCar]],
    mock_all_responses: responses.RequestsMock,
) -> None:
    envirocar_reader: EnvirocarReader = EnvirocarReader(
        db=db,
        file_or_url=None,
        threads=None,
    )
    await envirocar_reader.fetch_process_and_import_data(import_data=False)
    # Check sensors and track_ids response
    assert len(envirocar_reader.phenomenons) > 0
    for phenomenons_object in envirocar_reader.phenomenons:
        assert type(phenomenons_object) == EnvirocarPhenomenon
    assert len(envirocar_reader.sensors) > 0
    for sensors_object in envirocar_reader.sensors:
        assert type(sensors_object) == EnvirocarSensor
    assert len(envirocar_reader.sensor_statistics) > 0
    for sensor_statistics_object in envirocar_reader.sensor_statistics:
        assert type(sensor_statistics_object) == EnvirocarSensorStatistic
    assert len(envirocar_reader.tracks) > 0
    for tracks_object in envirocar_reader.tracks:
        assert type(tracks_object) == EnvirocarTrack
    assert len(envirocar_reader.track_measurements) > 0
    for track_measurements_object in envirocar_reader.track_measurements:
        assert type(track_measurements_object) == EnvirocarTrackMeasurement
    assert len(envirocar_reader.track_measurements_phenomenons) > 0
    for (
        track_measurements_phenomenons_object
    ) in envirocar_reader.track_measurements_phenomenons:
        assert (
            type(track_measurements_phenomenons_object)
            == EnvirocarTrackMeasurementPhenomenon
        )
    assert len(envirocar_reader.wikicar_envirocar_matches) > 0
    for wikicar_envirocar_matches_object in envirocar_reader.wikicar_envirocar_matches:
        assert type(wikicar_envirocar_matches_object) == WikicarEnvirocar
    assert (
        sum([len(objects) for objects in envirocar_reader.objects_ordered.values()])
        == 1312
    )
