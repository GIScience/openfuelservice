import logging
from typing import TYPE_CHECKING

from geoalchemy2 import Geometry
from sqlalchemy import (
    ARRAY,
    CHAR,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    tuple_,
)
from sqlalchemy.orm import Session, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .wikipedia import WikiCarCategory  # noqa: F401

    hybrid_property = property
else:
    from sqlalchemy.ext.hybrid import hybrid_property

logger = logging.getLogger(__name__)


class EnvirocarPhenomenon(Base):
    # EnvirocarPhenomenonModel
    # phenomenons

    id = Column(String, primary_key=True, index=True)

    @hybrid_property
    def name(self) -> str:
        return self.id

    @name.setter
    def name(self, value: str) -> None:
        self.id = value

    unit = Column(String, nullable=False)

    sensor_statistics = relationship(
        "EnvirocarSensorStatistic",
        backref="{}".format("envirocarphenomenon"),
        lazy="dynamic",
    )
    track_measurement_phenomenon = relationship(
        "EnvirocarTrackMeasurementPhenomenon",
        backref="{}".format("envirocarphenomenon"),
        lazy="dynamic",
    )
    # track_statistics = relationship(
    #     "EnvirocarTrackStatistic",
    #     backref="{}".format("envirocarphenomenon"),
    #     lazy="dynamic",
    # )
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

    id = Column(String, unique=True, primary_key=True, index=True)
    type = Column(String, nullable=False)
    model = Column(String, nullable=True)
    manufacturer = Column(String, nullable=True)
    fueltype = Column(String, nullable=False)

    constructionyear = Column(Integer, nullable=False)

    enginedisplacement = Column(Integer, nullable=True)

    wiki_hashes = Column(ARRAY(CHAR(length=32)), nullable=True)
    tracks = relationship("EnvirocarTrack", back_populates="sensor", lazy="dynamic")
    sensors_statistics = relationship(
        "EnvirocarSensorStatistic",
        backref="{}".format("envirocarsensor"),
        lazy="dynamic",
    )
    # TODO override with hybrid_property and a corresponding query.
    # on the other hand EnvirocarSensorStatistic delivers this already.
    # tracks_measurements = relationship(
    #     "EnvirocarTrackMeasurement",
    #     backref="{}".format("envirocarsensor"),
    #     lazy="dynamic",
    # )
    # tracks_features = relationship(
    #     "envirocartrackmeasurement", backref="{}".format("envirocarsensor"), lazy="dynamic",
    # )


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

    id = Column(
        String,
        ForeignKey("{}.id".format("envirocarsensor")),
        index=True,
        primary_key=True,
    )
    phenomenon_unit = Column(
        String,
        ForeignKey("{}.id".format("envirocarphenomenon")),
        index=True,
        primary_key=True,
    )
    max = Column(Float(asdecimal=True), nullable=True)
    avg = Column(Float(asdecimal=True), nullable=True)
    min = Column(Float(asdecimal=True), nullable=True)
    # Now some statistics --> numb = number of  … used for the statistics
    measurements = Column(Integer, nullable=True)
    tracks = Column(Integer, nullable=True)
    users = Column(Integer, nullable=True)
    sensors = Column(Integer, nullable=True)


class EnvirocarTrack(Base):
    # EnvirocarTrackModel
    # tracks

    id = Column(String, unique=True, primary_key=True, index=True)
    sensor_id = Column(String, ForeignKey("envirocarsensor.id"), nullable=False)
    sensor = relationship("EnvirocarSensor", back_populates="tracks")
    length = Column(Float(asdecimal=True))
    begin = Column(DateTime, nullable=False, index=True)
    end = Column(DateTime, nullable=False, index=True)
    # track_statistics = relationship(
    #     "EnvirocarTrackStatistic",
    #     backref="{}".format("envirocartrack"),
    #     lazy="dynamic",
    # )
    track_measurements = relationship(
        "EnvirocarTrackMeasurement",
        backref="{}".format("envirocartrack"),
        lazy="dynamic",
    )


# class EnvirocarTrackStatistic(Base):
#     # EnvirocarTrackStatisticModel
#     # tracks_statistics
#
#     id = Column(
#         String,
#         ForeignKey("{}.id".format("envirocartrack")),
#         index=True,
#         primary_key=True
#     )
#     phenomenon_name = Column(
#         String,
#         ForeignKey("{}.id".format("envirocarphenomenon")),
#         primary_key=True,
#         index=True,
#     )
#     max = Column(Float(asdecimal=True), nullable=True)
#     avg = Column(Float(asdecimal=True), nullable=True)
#     min = Column(Float(asdecimal=True), nullable=True)
#     # Now some statistics --> numb = number of  … used for the statistics
#     measurements = Column(Integer, nullable=True)
#     tracks = Column(Float(asdecimal=True), nullable=True)
#     users = Column(Float(asdecimal=True), nullable=True)
#     sensors = Column(Float(asdecimal=True), nullable=True)


class EnvirocarTrackMeasurement(Base):
    # EnvirocarTrackMeasurementModel
    # tracks_measurements

    id = Column(String, primary_key=True, index=True)

    geom = Column(Geometry(geometry_type="POINT", srid=4326, spatial_index=True))

    track_id = Column(
        String,
        ForeignKey("{}.id".format("envirocartrack")),
        nullable=False,
        index=True,
    )

    time = Column(DateTime, nullable=False, index=True)


class EnvirocarTrackMeasurementPhenomenon(Base):
    id = Column(
        String,
        ForeignKey("{}.id".format("envirocartrackmeasurement")),
        primary_key=True,
        unique=False,
    )
    name = Column(
        String,
        ForeignKey("{}.id".format("envirocarphenomenon")),
        primary_key=True,
        index=True,
    )
    unit = Column(String, nullable=False)
    value = Column(Float(asdecimal=True), nullable=True)

    @classmethod
    def get_all_by_filter(
        cls, db: Session, filter_ids: list, id_only: bool = False
    ) -> list:
        if id_only:
            return (
                db.query(cls.id, cls.name)
                .filter(tuple_(cls.id, cls.name).in_(filter_ids))
                .all()
            )
        else:
            return db.query(cls).filter(tuple_(cls.id, cls.name).in_(filter_ids)).all()


class EnvirocarAverageCategoryStatistics(Base):
    # EnvirocarAverageCategoryStatisticsModel
    # ec_average_category_statistics
    hash_id = Column(CHAR(length=32), primary_key=True, index=True)
    vehicle_type = Column(String, nullable=False, index=True)
    fuel_type = Column(String, nullable=False, index=True)
    phenomenon_name = Column(
        String,
        ForeignKey("{}.id".format("envirocarphenomenon")),
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
    phenomenon_name = Column(
        String,
        ForeignKey("{}.id".format("envirocarphenomenon")),
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
    phenomenon_name = Column(
        String,
        ForeignKey("{}.id".format("envirocarphenomenon")),
        nullable=False,
        index=True,
    )
    max = Column(Float(asdecimal=True))
    average = Column(Float(asdecimal=True))
    min = Column(Float(asdecimal=True))
    measurements = Column(Integer, nullable=False)
    numb_sensors = Column(Integer, nullable=False)
