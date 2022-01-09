import logging
from typing import TYPE_CHECKING

from geoalchemy2 import Geometry
from sqlalchemy import ARRAY, CHAR, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .wikipedia import WikiCarCategory  # noqa: F401

    hybrid_property = property
else:
    pass
logger = logging.getLogger(__name__)


class EnvirocarPhenomenon(Base):
    # EnvirocarPhenomenonModel
    # phenomenons

    unit = Column(String, primary_key=True, index=True)
    value = Column(String, nullable=False)

    sensors_statistics = relationship(
        "EnvirocarSensorStatistic",
        backref="{}".format("envirocarphenomenon"),
        lazy="dynamic",
    )
    tracks_measurements = relationship(
        "EnvirocarTrackMeasurement",
        backref="{}".format("envirocarphenomenon"),
        lazy="dynamic",
    )
    tracks_statistics = relationship(
        "EnvirocarTrackStatistic",
        backref="{}".format("envirocarphenomenon"),
        lazy="dynamic",
    )
    average_vehicle_type_statistics = relationship(
        "EnvirocarAverageVehicleTypeStatistic",
        backref="{}".format("envirocarphenomenon"),
        lazy="dynamic",
    )
    average_manufacturer_statistics = relationship(
        "EnvirocarAverageManufacturerStatistic",
        backref="{}".format("envirocarphenomenon"),
        lazy="dynamic",
    )
    average_category_statistics = relationship(
        "EnvirocarAverageCategoryStatistics",
        backref="{}".format("envirocarphenomenon"),
        lazy="dynamic",
    )


class EnvirocarSensor(Base):
    # EnvirocarSensorModel
    # sensors

    sensor_id = Column(String, unique=True, primary_key=True, index=True)
    sensor_type = Column(String, nullable=False)
    car_model = Column(String, nullable=False)
    car_manufacturer = Column(String, nullable=False)
    fuel_type = Column(String, nullable=False)
    construction_year = Column(Integer, nullable=False)
    wiki_hashes = Column(ARRAY(CHAR(length=32)), nullable=True)
    track_ids = relationship(
        "EnvirocarTrack", backref="{}".format("envirocarsensor"), lazy="dynamic"
    )
    sensors_statistics = relationship(
        "EnvirocarSensorStatistic",
        backref="{}".format("envirocarsensor"),
        lazy="dynamic",
    )
    tracks_measurements = relationship(
        "EnvirocarTrackMeasurement",
        backref="{}".format("envirocarsensor"),
        lazy="dynamic",
    )
    tracks_features = relationship(
        "EnvirocarTrackFeature", backref="{}".format("envirocarsensor"), lazy="dynamic",
    )


# TODO Always add the new agencies here to reference the correct cars
class MatchedWikiEnvirocar(Base):
    # MatchedWikiEnvirocarModel
    # wikipedia_envirocar_match_table

    object_hash = Column(CHAR(length=32), primary_key=True, index=True)
    envirocar_sensor_id = Column(String, nullable=True, index=True)
    car_hash_id = Column(CHAR(length=32), nullable=False, index=True)


class EnvirocarSensorStatistic(Base):
    # EnvirocarSensorStatisticModel
    # sensors_statistics

    hash_id = Column(CHAR(length=32), primary_key=True, index=True)
    sensor_id = Column(
        String,
        ForeignKey("{}.sensor_id".format("envirocarsensor")),
        nullable=False,
        index=True,
    )
    phenomenon_unit = Column(
        String,
        ForeignKey("{}.unit".format("envirocarphenomenon")),
        nullable=False,
        index=True,
    )
    max = Column(Float(asdecimal=True), nullable=True)
    avg = Column(Float(asdecimal=True), nullable=True)
    min = Column(Float(asdecimal=True), nullable=True)
    # Now some statistics --> numb = number of  … used for the statistics
    numb_measurements = Column(Integer, nullable=True)
    numb_tracks = Column(Integer, nullable=True)
    numb_users = Column(Integer, nullable=True)
    numb_sensors = Column(Integer, nullable=True)


class EnvirocarTrack(Base):
    # EnvirocarTrackModel
    # tracks

    track_id = Column(String, unique=True, primary_key=True, index=True)
    sensor_id = Column(
        String,
        ForeignKey("{}.sensor_id".format("envirocarsensor")),
        nullable=False,
        index=True,
    )
    track_length = Column(Float(asdecimal=True))
    geom = Column(
        Geometry(geometry_type="LINESTRING", srid=4326, spatial_index=True),
        nullable=True,
    )
    tracks_statistics = relationship(
        "EnvirocarTrackStatistic",
        backref="{}".format("envirocartrack"),
        lazy="dynamic",
    )
    tracks_measurements = relationship(
        "EnvirocarTrackMeasurement",
        backref="{}".format("envirocartrack"),
        lazy="dynamic",
    )
    tracks_features = relationship(
        "EnvirocarTrackFeature", backref="{}".format("envirocartrack"), lazy="dynamic",
    )


class EnvirocarTrackStatistic(Base):
    # EnvirocarTrackStatisticModel
    # tracks_statistics

    hash_id = Column(CHAR(length=32), primary_key=True, index=True)
    track_id = Column(
        String,
        ForeignKey("{}.track_id".format("envirocartrack")),
        nullable=False,
        index=True,
    )
    phenomenon_unit = Column(
        String,
        ForeignKey("{}.unit".format("envirocarphenomenon")),
        nullable=False,
        index=True,
    )
    max = Column(Float(asdecimal=True), nullable=True)
    avg = Column(Float(asdecimal=True), nullable=True)
    min = Column(Float(asdecimal=True), nullable=True)
    # Now some statistics --> numb = number of  … used for the statistics
    numb_measurements = Column(Integer, nullable=True)
    numb_tracks = Column(Float(asdecimal=True), nullable=True)
    numb_users = Column(Float(asdecimal=True), nullable=True)
    numb_sensors = Column(Float(asdecimal=True), nullable=True)


class EnvirocarTrackFeature(Base):
    # EnvirocarTrackFeatureModel
    # tracks_features

    track_measurement_id = Column(
        String, index=True, unique=True, nullable=False, primary_key=True
    )

    sensor_id = Column(
        String,
        ForeignKey("{}.sensor_id".format("envirocarsensor")),
        nullable=False,
        index=True,
    )
    track_id = Column(
        String,
        ForeignKey("{}.track_id".format("envirocartrack")),
        nullable=False,
        index=True,
    )

    geom = Column(Geometry(geometry_type="POINT", srid=4326, spatial_index=True))

    tracks_features = relationship(
        "EnvirocarTrackMeasurement",
        backref="{}".format("envirocartrackfeature"),
        lazy="dynamic",
    )


class EnvirocarTrackMeasurement(Base):
    # EnvirocarTrackMeasurementModel
    # tracks_measurements

    hash_id = Column(CHAR(length=32), primary_key=True, index=True)
    track_measurement_id = Column(
        String,
        ForeignKey("{}.track_measurement_id".format("envirocartrackfeature")),
        nullable=False,
        index=True,
    )

    track_id = Column(
        String,
        ForeignKey("{}.track_id".format("envirocartrack")),
        nullable=False,
        index=True,
    )
    sensor_id = Column(
        String,
        ForeignKey("{}.sensor_id".format("envirocarsensor")),
        nullable=False,
        index=True,
    )
    phenomenon_unit = Column(
        String,
        ForeignKey("{}.unit".format("envirocarphenomenon")),
        nullable=False,
        index=True,
    )
    phenomenon_value = Column(Float(asdecimal=True), nullable=True)
    date = Column(DateTime, nullable=False, index=True)


class EnvirocarAverageCategoryStatistics(Base):
    # EnvirocarAverageCategoryStatisticsModel
    # ec_average_category_statistics
    hash_id = Column(CHAR(length=32), primary_key=True, index=True)
    vehicle_type = Column(String, nullable=False, index=True)
    fuel_type = Column(String, nullable=False, index=True)
    phenomenon_unit = Column(
        String,
        ForeignKey("{}.unit".format("envirocarphenomenon")),
        nullable=False,
        index=True,
    )
    max = Column(Float(asdecimal=True))
    average = Column(Float(asdecimal=True))
    min = Column(Float(asdecimal=True))
    measurements = Column(Integer, nullable=False)
    numb_sensors = Column(Integer, nullable=False)
    category_short_eu = Column(
        String, ForeignKey("{}.category_short_eu".format("wikicarcategory"))
    )


class EnvirocarAverageVehicleTypeStatistic(Base):
    # EnvirocarAverageVehicleTypeStatisticModel
    # average_vehicle_type_statistics
    hash_id = Column(CHAR(length=32), primary_key=True, index=True)
    vehicle_type = Column(String, nullable=False, index=True)
    fuel_type = Column(String, nullable=False, index=True)
    phenomenon_unit = Column(
        String,
        ForeignKey("{}.unit".format("envirocarphenomenon")),
        nullable=False,
        index=True,
    )
    max = Column(Float(asdecimal=True))
    average = Column(Float(asdecimal=True))
    min = Column(Float(asdecimal=True))
    measurements = Column(Integer, nullable=False)
    numb_sensors = Column(Integer, nullable=False)


class EnvirocarAverageManufacturerStatistic(Base):
    # EnvirocarAverageManufacturerStatisticModel
    # average_manufacturer_statistics
    hash_id = Column(CHAR(length=32), primary_key=True, index=True)
    manufacturer = Column(String, nullable=False, index=True)
    vehicle_type = Column(String, nullable=False, index=True)
    fuel_type = Column(String, nullable=False, index=True)
    phenomenon_unit = Column(
        String,
        ForeignKey("{}.unit".format("envirocarphenomenon")),
        nullable=False,
        index=True,
    )
    max = Column(Float(asdecimal=True))
    average = Column(Float(asdecimal=True))
    min = Column(Float(asdecimal=True))
    measurements = Column(Integer, nullable=False)
    numb_sensors = Column(Integer, nullable=False)
