from pathlib import Path
from typing import Dict, Generator, List

import pytest
import responses
from sqlalchemy.orm import Session

from app.db.importer.envirocar.envirocar_reader import EnvirocarReader
from app.models import (
    EnvirocarPhenomenon,
    EnvirocarSensor,
    EnvirocarSensorStatistic,
    EnvirocarTrack,
    EnvirocarTrackMeasurement,
    EnvirocarTrackMeasurementPhenomenon,
    WikiCar,
)

track_ids = [
    "61d543bef4c3e97fbd560705",
    "61d543bef4c3e97fbd56072d",
    "619b972b7b277d59bd6537fc",
]


def test_get_track_measurements_and_phenomenons(
    db: Session,
    envirocar_mocked_responses: responses.RequestsMock,
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


def test_get_track_ids_and_sensors(
    db: Session,
    envirocar_mocked_responses: responses.RequestsMock,
) -> None:
    envirocar_reader: EnvirocarReader = EnvirocarReader(
        db=db,
        file_or_url=Path(""),
        threads=None,
    )
    sensors, tracks, tracks_ids = envirocar_reader.get_track_ids_and_sensors()
    # Check sensors and track_ids response
    assert len(sensors) == 2
    assert isinstance(sensors[0], EnvirocarSensor)
    sensor: EnvirocarSensor = sensors[0]
    assert sensor.id == "5fd9d14e05fa792e88dc8b7b"
    assert sensor.constructionyear == 2006
    assert sensor.enginedisplacement == 1595
    assert sensor.fueltype == "gasoline"
    assert sensor.manufacturer == "VW"
    assert sensor.model == "Golf V Plus 1.6"
    assert sensor.type == "car"

    assert len(tracks_ids) == 3
    assert [track_id in tracks_ids for track_id in tracks_ids]

    assert len(tracks) == 3
    track: EnvirocarTrack
    for track in tracks:
        assert track.id in tracks_ids
        assert track.sensor_id == sensor.id or track.sensor_id == sensors[1].id
        assert track.begin
        assert track.end
        assert track.length


def test_get_track_ids_and_sensors_2(
    db: Session,
    envirocar_mocked_responses: responses.RequestsMock,
) -> None:
    envirocar_reader: EnvirocarReader = EnvirocarReader(
        db=db,
        file_or_url=Path(""),
        threads=None,
    )
    sensors, tracks, tracks_ids = envirocar_reader.get_track_ids_and_sensors()
    # Check sensors and track_ids response
    assert len(sensors) == 2
    assert isinstance(sensors[1], EnvirocarSensor)
    sensor: EnvirocarSensor = sensors[1]
    assert sensor.id == "616010fb0bd6756ea3a9aea7"
    assert sensor.constructionyear == 2009
    assert sensor.enginedisplacement == 1398
    assert sensor.fueltype == "diesel"
    assert sensor.manufacturer == "OPEL"
    assert sensor.model == "Corsa"
    assert sensor.type == "car"

    assert len(tracks_ids) == 3
    assert [track_id in tracks_ids for track_id in tracks_ids]

    assert len(tracks) == 3
    track: EnvirocarTrack
    for track in tracks:
        assert track.id in tracks_ids
        assert track.sensor_id == sensor.id or track.sensor_id == sensors[0].id
        assert track.begin
        assert track.end
        assert track.length


def test_get_phenomenons(
    db: Session, envirocar_mocked_responses: responses.RequestsMock
) -> None:
    envirocar_reader: EnvirocarReader = EnvirocarReader(
        db=db,
        file_or_url=Path(""),
        threads=None,
    )

    phenomenons = envirocar_reader.get_phenomenons()
    # Check sensors and track_ids response
    assert len(phenomenons) == 32
    for phenomenon in phenomenons:
        assert isinstance(phenomenon, EnvirocarPhenomenon)
        assert phenomenon.name
        assert phenomenon.unit


def test_get_sensors(
    db: Session, envirocar_mocked_responses: responses.RequestsMock
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


def test_get_sensor_statistics(
    db: Session, mock_all_responses: responses.RequestsMock
) -> None:
    envirocar_reader: EnvirocarReader = EnvirocarReader(
        db=db,
        file_or_url=Path(""),
        threads=None,
    )
    sensors, tracks, track_ids = envirocar_reader.get_track_ids_and_sensors()
    sensor_ids: List = [sensor.id for sensor in sensors]
    sensors_statistics = envirocar_reader.get_sensor_statistics(sensor_ids)
    assert len(sensors_statistics) == 44
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
    mock_wikipedia_cars: Generator[WikiCar, None, None],
    envirocar_mocked_responses: responses.RequestsMock,
) -> None:
    envirocar_reader: EnvirocarReader = EnvirocarReader(
        db=db,
        file_or_url=Path(""),
        threads=None,
    )
    # TODO remove all sensors except one a wikicar is available for.#
    sensors, tracks, track_ids = envirocar_reader.get_track_ids_and_sensors()
    # Check sensors and track_ids response
    assert len(sensors)
    matched_sensors = await envirocar_reader.match_sensors_to_wikicar(
        sensors=sensors, accuracy=0.2
    )
    assert len(matched_sensors) == 2


def test_fetch_and_process_data(
    db: Session,
    envirocar_mocked_responses: responses.RequestsMock,
) -> None:
    envirocar_reader: EnvirocarReader = EnvirocarReader(
        db=db,
        file_or_url=None,
        threads=None,
    )
    envirocar_reader.fetch_and_process_data()
    # Check sensors and track_ids response
    assert len(envirocar_reader.objects_ordered) == 7
    assert (
        sum([len(objects) for objects in envirocar_reader.objects_ordered.values()])
        == 1249
    )
    for i in range(0, len(envirocar_reader.objects_ordered)):
        for envirocar_object in envirocar_reader.objects_ordered[i]:
            assert type(envirocar_object) in [
                EnvirocarPhenomenon,
                EnvirocarTrack,
                EnvirocarSensor,
                EnvirocarTrackMeasurementPhenomenon,
                EnvirocarTrackMeasurement,
            ]


def test_match(
    db: Session,
    envirocar_mocked_responses: responses.RequestsMock,
) -> None:
    envirocar_reader: EnvirocarReader = EnvirocarReader(
        db=db,
        file_or_url=None,
        threads=None,
    )
    envirocar_reader.fetch_and_process_data()
    # Check sensors and track_ids response
    assert len(envirocar_reader.objects_ordered) == 6
    assert (
        sum([len(objects) for objects in envirocar_reader.objects_ordered.values()])
        == 1249
    )
    for i in range(0, len(envirocar_reader.objects_ordered)):
        for envirocar_object in envirocar_reader.objects_ordered[i]:
            assert type(envirocar_object) in [
                EnvirocarPhenomenon,
                EnvirocarTrack,
                EnvirocarSensor,
                EnvirocarTrackMeasurementPhenomenon,
                EnvirocarTrackMeasurement,
            ]
