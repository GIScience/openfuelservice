from pathlib import Path
from typing import List

import pytest

from app.core.config import settings
from app.matching.manufacturer_matching import (
    ManufacturerAnnCollection,
    ManufacturerAnnModel,
)


@pytest.mark.parametrize(
    "model_name,classes_size,words_size",
    (("Abarth", 14, 2350), ("Tesla", 5, 3271), ("", 0, 0), (None, 0, 0)),
)
@pytest.mark.asyncio
async def test_initialize_model(
    model_name: str, classes_size: int, words_size: int
) -> None:
    model_collection = ManufacturerAnnCollection(
        models_path=settings.UNCOMPRESSED_MATCHING_DATA
    )
    assert len(model_collection._loaded_models) == 0
    model_names_intents: Path = model_collection._models_intents[model_name] if model_name else None  # type: ignore
    model_names_training_data: Path = (
        model_collection._models_training_data[model_name] if model_name else None  # type: ignore
    )  # type: ignore
    model = ManufacturerAnnModel(
        model_name=model_name,
        old_intents=model_names_intents,
        old_training_data=model_names_training_data,
    )
    await model.initialize_model()
    assert len(model._classes) == classes_size
    assert len(model._words) == words_size


@pytest.mark.parametrize(
    "model_names,number_of_exptected_models",
    (
        (["Abarth"], 1),
        (["Tesla"], 1),
        (["Abarth", "Tesla"], 2),
        (["Abarth", "Tesla", "", None], 2),
        ([], 0),
        (None, 0),
    ),
)
@pytest.mark.asyncio
async def test__initialize_models(
    model_names: List, number_of_exptected_models: int
) -> None:
    model_collection = ManufacturerAnnCollection(
        models_path=settings.UNCOMPRESSED_MATCHING_DATA
    )
    assert len(model_collection._loaded_models) == 0
    await model_collection.initialize_models(model_names)
    assert model_collection._models_path == Path(settings.UNCOMPRESSED_MATCHING_DATA)
    assert len(model_collection._models_training_data) == 52
    assert len(model_collection._models_intents) == 52
    assert len(model_collection._loaded_models) == number_of_exptected_models
    if model_names:
        for model_name in model_names:
            if not model_name or not len(model_name):
                continue
            assert model_name in model_collection._loaded_models
            assert model_name in model_collection._models_intents
            assert model_name in model_collection._models_training_data


@pytest.mark.asyncio
async def test__initialize_models_must_be_empty() -> None:
    model_collection = ManufacturerAnnCollection(models_path="foo")
    await model_collection.initialize_models(["foo"])
    assert len(model_collection._models_training_data) == 0
    assert len(model_collection._models_intents) == 0
    assert len(model_collection._loaded_models) == 0


@pytest.mark.parametrize(
    "model_names,manufacturer,car_name,expected_result,min_certainty",
    (
        (["Abarth"], "Abarth", "Abarth 695 Biposto", "Abarth 695 Biposto", 0.96),
        (["Abarth"], "Abarth", "695 Biposto", "Abarth 695 Biposto", 0.97),
        (
            ["Abarth", "Tesla"],
            "Abarth",
            "Abarth 695 Biposto",
            "Abarth 695 Biposto",
            0.96,
        ),
        (["Abarth", "Tesla"], "Tesla", "Model X", "Tesla Model X", 0.99),
        ([], "Tesla", "Model X", "Tesla Model X", 0.99),
        (["Abarth", ""], "Abarth", "Abarth 695 Biposto", "Abarth 695 Biposto", 0.96),
        (["Abarth", None], "Abarth", "Abarth 695 Biposto", "Abarth 695 Biposto", 0.96),
    ),
)
@pytest.mark.asyncio
async def test_classify(
    model_names: List[str],
    manufacturer: str,
    car_name: str,
    expected_result: str,
    min_certainty: float,
) -> None:
    model_collection = ManufacturerAnnCollection(
        models_path=settings.UNCOMPRESSED_MATCHING_DATA
    )
    assert len(model_collection._loaded_models) == 0
    await model_collection.initialize_models(model_names)
    result: List[tuple] = await model_collection.classify(
        model_name=manufacturer, car_name=car_name, accuracy=min_certainty
    )
    assert len(result) == 1
    assert result[0][0] == expected_result
    assert result[0][1] >= min_certainty


@pytest.mark.parametrize(
    "model_names,car_name,expected_result,min_certainty",
    (
        (["Abarth"], "", None, None),
        ([""], "Abarth 695 Biposto", None, None),
        ([None], "Abarth 695 Biposto", None, None),
        (None, "Abarth 695 Biposto", None, None),
        (["Abarth"], None, None, None),
        (["Abarth"], "foo", None, None),
        (["foo"], "Abarth 695 Biposto", None, None),
        (["foo"], "foo", None, None),
        (["foo"], "", None, None),
        ([""], "", None, None),
    ),
)
@pytest.mark.asyncio
async def test_classify_must_fail(
    model_names: List[str], car_name: str, expected_result: str, min_certainty: float
) -> None:
    model_collection = ManufacturerAnnCollection(
        models_path=settings.UNCOMPRESSED_MATCHING_DATA
    )
    assert len(model_collection._loaded_models) == 0
    await model_collection.initialize_models(model_names)
    result: List[tuple] = await model_collection.classify(
        model_name=model_names[0] if model_names else None, car_name=car_name
    )
    assert not len(result)
