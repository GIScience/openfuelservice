from typing import TYPE_CHECKING

from sqlalchemy import ARRAY, Column, Float, ForeignKey, Integer, String, tuple_
from sqlalchemy.orm import Session, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .carfueldata import CarFuelDataAverageCategoryStatistics  # noqa: F401
    from .envirocar import EnvirocarAverageCategoryStatistics  # noqa: F401
    from .envirocar import EnvirocarSensor  # noqa: F401

    hybrid_property = property
else:
    from sqlalchemy.ext.hybrid import hybrid_property


class WikiCarCategory(Base):
    # CarCategoryModel
    # wikicarcategory
    id = Column(String, primary_key=True, nullable=False, index=True)

    @hybrid_property
    def category_short_eu(self) -> str:
        return self.id

    @category_short_eu.setter
    def category_short_eu(self, value: str) -> None:
        self.id = value

    category_name_de = Column(String, unique=True, nullable=False, index=True)
    category_name_en = Column(String, unique=True, nullable=False, index=True)

    category_wiki_names = Column(ARRAY(String), nullable=False)

    car_models = relationship(
        "WikiCar", backref="{}".format("{}".format("wikicarcategory")), lazy="dynamic"
    )
    wiki_car_page_texts = relationship(
        "WikiCarPageText", backref="{}".format("wikicarcategory"), lazy="dynamic"
    )

    carfueldata_av_statistics = relationship(
        "CarFuelDataAverageCategoryStatistics",
        backref="{}".format("wikicarcategory"),
        lazy="dynamic",
    )

    average_category_statistics = relationship(
        "EnvirocarAverageCategoryStatistics",
        backref="{}".format("wikicarcategory"),
        lazy="dynamic",
    )


class WikiCar(Base):
    # WikiCarModel
    # wiki_car_table
    id = Column(Integer, primary_key=True)

    @hybrid_property
    def page_id(self) -> int:
        return self.id

    @page_id.setter
    def page_id(self, value: int) -> None:
        self.id = int(value)

    wiki_name = Column(String, nullable=False, index=True, unique=True)
    category_short_eu = Column(
        String, ForeignKey("{}.id".format("wikicarcategory")), nullable=True, index=True
    )
    category = relationship(WikiCarCategory, back_populates="car_models")

    brand_name = Column(String, nullable=False, index=True)
    car_name = Column(String, nullable=False, index=True)
    page_language = Column(String, nullable=True)

    envirocars = relationship(
        "WikicarEnvirocar",
        uselist=True,
        back_populates="wikicar"
    )


class WikiCarPageText(Base):
    # WikiCarPageTextModel
    # wikicar_page_texts
    id = Column(
        Integer,
        ForeignKey("{}.id".format(WikiCar.__tablename__)),
        index=True,
        primary_key=True,
    )

    @hybrid_property
    def page_id(self) -> int:
        return self.id

    @page_id.setter
    def page_id(self, value: int) -> None:
        self.id = value

    brand_name = Column(String, nullable=False, index=True)
    car_name = Column(String, nullable=False, index=True)
    page_language = Column(String, nullable=False, index=True)
    page_text = Column(String, nullable=True)
    category_short_eu = Column(
        String,
        ForeignKey("{}.id".format(WikiCarCategory.__tablename__)),
        nullable=True,
        index=True,
    )


class WikicarEnvirocar(Base):
    # MatchedWikiEnvirocarModel
    # wikipedia_envirocar_match_table

    envirocar_sensor_id = Column(
        String,
        ForeignKey(
            "{}.id".format("envirocarsensor"), onupdate="CASCADE", ondelete="CASCADE"
        ),
        index=True,
        primary_key=True,
    )
    envirocar = relationship("EnvirocarSensor", back_populates="wiki_cars")

    wikicar_id = Column(
        Integer,
        ForeignKey("{}.id".format("wikicar")),
        index=True,
        primary_key=True,
    )
    wikicar = relationship("WikiCar", back_populates="envirocars")

    matching_accuracy = Column(Float, index=True, nullable=False)

    @classmethod
    def get_all_by_filter(
            cls, db: Session, filter_ids: list, id_only: bool = False
    ) -> list:
        if id_only:
            return (
                db.query(cls.envirocar_sensor_id, cls.wikicar_id)
                    .filter(tuple_(cls.envirocar_sensor_id, cls.wikicar_id).in_(filter_ids))
                    .all()
            )
        else:
            return (
                db.query(cls)
                    .filter(tuple_(cls.envirocar_sensor_id, cls.wikicar_id).in_(filter_ids))
                    .all()
            )
