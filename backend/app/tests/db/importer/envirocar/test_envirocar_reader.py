from pathlib import Path
from typing import Dict, List

import responses

from app.db.importer.envirocar.envirocar_reader import EnvirocarReader
from app.models import (
    EnvirocarPhenomenon,
    EnvirocarSensor,
    EnvirocarTrack,
    EnvirocarTrackMeasurement,
    EnvirocarTrackMeasurementPhenomenon,
)


def test_get_track_measurements_and_phenomenons(
    envirocar_mocked_responses: responses.RequestsMock,
) -> None:
    envirocar_reader: EnvirocarReader = EnvirocarReader(
        file_or_url=Path(""), envirocar_base_url="https://test.com", threads=None
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
    envirocar_mocked_responses: responses.RequestsMock,
) -> None:
    envirocar_reader: EnvirocarReader = EnvirocarReader(
        file_or_url=Path(""), envirocar_base_url="https://test.com", threads=None
    )
    sensors, tracks, track_ids = envirocar_reader.get_track_ids_and_sensors()
    # Check sensors and track_ids response
    assert len(sensors) == 1
    assert isinstance(sensors[0], EnvirocarSensor)
    sensor: EnvirocarSensor = sensors[0]
    assert sensor.id == "5fd9d14e05fa792e88dc8b7b"
    assert sensor.constructionyear == 2006
    assert sensor.enginedisplacement == 1595
    assert sensor.fueltype == "gasoline"
    assert sensor.manufacturer == "VW"
    assert sensor.model == "Golf V Plus 1.6"
    assert sensor.type == "car"

    assert len(track_ids) == 2
    assert [
        track_id in ["61d543bef4c3e97fbd560705", "61d543bef4c3e97fbd56072d"]
        for track_id in track_ids
    ]

    assert len(tracks) == 2
    track: EnvirocarTrack
    for track in tracks:
        assert track.id in ["61d543bef4c3e97fbd560705", "61d543bef4c3e97fbd56072d"]
        assert track.sensor_id == sensor.id
        assert track.begin
        assert track.end
        assert track.length


def test_get_phenomenons(envirocar_mocked_responses: responses.RequestsMock) -> None:
    envirocar_reader: EnvirocarReader = EnvirocarReader(
        file_or_url=Path(""), envirocar_base_url="https://test.com", threads=None
    )

    phenomenons = envirocar_reader.get_phenomenons()
    # Check sensors and track_ids response
    assert len(phenomenons) == 32
    for phenomenon in phenomenons:
        assert isinstance(phenomenon, EnvirocarPhenomenon)
        assert phenomenon.name
        assert phenomenon.unit


def test_get_sensors(envirocar_mocked_responses: responses.RequestsMock) -> None:
    envirocar_reader: EnvirocarReader = EnvirocarReader(
        file_or_url=Path(""), envirocar_base_url="https://test.com", threads=None
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


def test_fetch_and_process_data(
    envirocar_mocked_responses: responses.RequestsMock,
) -> None:
    envirocar_reader: EnvirocarReader = EnvirocarReader(
        file_or_url=None, envirocar_base_url="https://test.com", threads=None
    )
    envirocar_reader.fetch_and_process_data()
    # Check sensors and track_ids response
    assert len(envirocar_reader.objects_list) == 1247
    for envirocar_object in envirocar_reader.objects_list:
        assert type(envirocar_object) in [
            EnvirocarPhenomenon,
            EnvirocarTrack,
            EnvirocarSensor,
            EnvirocarTrackMeasurementPhenomenon,
            EnvirocarTrackMeasurement,
        ]
