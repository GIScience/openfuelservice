from datetime import datetime
from typing import Any, Dict, List, Union

import nltk
import pytest

from app.core.config import settings
from app.misc.data_handling import (
    check_brand_aliases,
    check_fixed_matches,
    check_manufacturer,
    check_name_for_year,
    check_static_vehicles_list,
    clean_vehicle_name,
    create_permutations,
    create_powerset,
    flatten_dictionary,
    get_brand_aliases,
    remove_double_words,
    vehicle_is_ignored,
)


@pytest.mark.parametrize(
    "bare_manufacturer,real_manufacturer",
    (
        ("3 GE", "3 GE"),
        ("ACAM", "ACAM"),
        ("Opel", "Opel"),
        ("azlk", "Moskvitch"),
        ("PSA / Fiat", "Fiat"),
        ("Foobar", None),
        ("", None),
        (None, None),
    ),
)
def test_check_manufacturer(bare_manufacturer: str, real_manufacturer: str) -> None:
    assert real_manufacturer == check_manufacturer(
        manufacturer_to_check=bare_manufacturer
    )


@pytest.mark.parametrize(
    "manufacturer,car_name,year,expected_result",
    (
        ("Fiat", "500", 2011, ["Fiat 500", "Fiat 500 (2007)"]),
        ("Fiat", "500", 2015, ["Fiat 500", "Fiat 500 (2007)"]),
        ("\u0161koda", "citigo", 2012, ["\u0160koda Citigo"]),
        (
            "\u0161koda",
            "roomster",
            2010,
            ["\u0160koda Fabia I", "\u0160koda Fabia II", "\u0160koda Fabia III"],
        ),
        ("Fiat", "500", "", ["Fiat 500", "Fiat 500 (2007)"]),
        ("Fiat", "500", None, ["Fiat 500", "Fiat 500 (2007)"]),
        ("Fiat", "500", 2007, []),
        (None, "500", 2011, []),
        ("Fiat", None, 2011, []),
        (None, "500", None, []),
        ("Fiat", None, None, []),
        (None, None, 2011, []),
    ),
)
def test_check_fixed_matches(
    manufacturer: str, car_name: str, year: int, expected_result: List
) -> None:
    test: List = check_fixed_matches(
        manufacturer=manufacturer, car_name=car_name, year=year
    )
    test.sort()
    expected_result.sort()
    assert test == expected_result


@pytest.mark.parametrize(
    "test_string,expected_size",
    (
        ("Mercedes 3 GE 2021", 24),
        ("Mercedes 3 2001", 6),
        ("Kei-Car Car 1969", 6),
        ("", 0),
        (None, 0),
    ),
)
def test_create_permutations(test_string: str, expected_size: int) -> None:
    test = create_permutations(string_to_permutation=test_string)
    assert isinstance(test, List)
    assert len(test) == expected_size
    assert len(set(test)) == len(test)
    if test_string is not None:
        test_string = test_string.replace("-", " ")
        words_in_test_string: List = list(set(nltk.word_tokenize(test_string)))
        for permutation in test:
            assert isinstance(permutation, str)
            words_in_permutation: List = nltk.word_tokenize(permutation)
            assert len(words_in_permutation) == len(words_in_test_string)
            for word in words_in_permutation:
                assert word in words_in_test_string


@pytest.mark.parametrize(
    "test_string,powerset_size",
    (
        (["3 GE 2021", "Mercedes"], 3),
        (["Mercedes", "3 GE 2001", '"Sub'], 7),
        (["Mercedes 3 GE"], 1),
        (["Mercedes Benz", 2000], 3),
        (["Mercedes Benz", 2000.0], 3),
        (["PSA / Fiat", "Foobar"], 3),
        (["Foobar", None], 1),
        ([None, "Foobar"], 1),
        ("Mercedes 3 GE", 0),
        ("", 0),
        ([None, None], 0),
        (None, 0),
    ),
)
def test_powerset(test_string: Union[List[Any], str], powerset_size: int) -> None:
    test: List = create_powerset(list_to_powerset=test_string)  # type: ignore
    assert len(test) == powerset_size


@pytest.mark.parametrize(
    "test_string,expected_result,caseless",
    (
        ("Mercedes 3 GE 2021", "Mercedes 3 GE 2021", False),
        ("Mercedes 3 GE 2021", "mercedes 3 ge 2021", True),
        ("Mercedes 3 Mercedes 2001", "mercedes 3 2001", True),
        ("Mercedes 3 GE GE 2000 2000 2000", "mercedes 3 ge 2000", True),
        ("Kei-Car Car 1969", "kei-car car 1969", True),
        ("", "", True),
        (None, "", True),
    ),
)
def test_remove_double_words(
    test_string: str, expected_result: str, caseless: bool
) -> None:
    test = remove_double_words(string=test_string, caseless=caseless)
    assert test == expected_result


@pytest.mark.parametrize(
    "input_dict,output_dict",
    (
        ({"a": "b"}, {"a": "b"}),
        ({"a": "b", "c": {"c1": "d1", "c2": "d2"}}, {"a": "b", "c1": "d1", "c2": "d2"}),
        ({}, {}),
        (None, {}),
        ("foobar", {}),
    ),
)
def test_flatten_dictionary(input_dict: Dict, output_dict: Dict) -> None:
    assert flatten_dictionary(input_dict) == output_dict


@pytest.mark.parametrize(
    "test_string,expected_result",
    (
        ("Mercedes 3 GE (2015)", 2015),
        ("Mercedes 3 GE (2016)", 2016),
        ("Mercedes 3 GE (1999)", 1999),
        ("Mercedes 3 GE 2021", 2021),
        ("Mercedes 3 GE 2001", 2001),
        ("Mercedes 3 GE 2000", 2000),
        ("Mercedes 3 GE 1999", 1999),
        (f"Mercedes 3 GE {datetime.today().year + 10}", None),
        ("Kei-Car 1969", None),
        (2000, None),
        ("Mercedes 3 GE", None),
        ("Opel Foobar", None),
        ("PSA / Fiat Foobar", None),
        ("Foobar", None),
        (None, None),
    ),
)
def test_check_name_for_year(test_string: str, expected_result: int) -> None:
    test: Union[int, None] = check_name_for_year(car_name=test_string)
    assert test == expected_result


@pytest.mark.parametrize(
    "test_string,expected_result",
    (
        ("Mercedes 3 GE \\\"'#@;*<>{}`+=~|.!?,'", "Mercedes 3 GE"),
        ("Mercedes 3 GE;*<>{}`+=~|.!?,", "Mercedes 3 GE"),
        ("Mercedes +#*'3 +#*'GE", "Mercedes 3 GE"),
        ("Opel Foobar (22?=)", "Opel Foobar (22)"),
        ("PSA / Fiat Foobar", "PSA / Fiat Foobar"),
        ("Kei-Car", "Kei-Car"),
        ("Foobar", "Foobar"),
        (None, None),
    ),
)
def test_clean_vehicle_name(test_string: str, expected_result: str) -> None:
    test = clean_vehicle_name(vehicle_name=test_string)
    assert test == expected_result


@pytest.mark.parametrize(
    "test_string", [s for s in settings.CAR_BRANDS["ignore_list"]][::100]
)
def test_vehicle_is_ignored(test_string: str) -> None:
    ignored: bool = vehicle_is_ignored(car_brand_or_name=test_string)
    assert ignored


@pytest.mark.parametrize(
    "test, expected",
    (
        (["azlk", "Foo"], ["Moskvitch", "Foo"]),
        (["daimler benz", "Foo"], ["Mercedes-Benz", "Foo"]),
        (["VW-Porsche", "Foo"], ["Porsche", "Foo"]),
        (["DS", "Foo"], ["Citroën", "Foo"]),
        ([None, "Foo"], [None, None]),
        (["Foo", "Foo"], [None, None]),
        (["DS", None], [None, None]),
        ([None, None], [None, None]),
    ),
)
def test_check_brand_aliases(test: tuple, expected: tuple) -> None:
    brand, name = check_brand_aliases(short_name=test[0], car_name=test[1])
    assert brand == expected[0]
    assert name == expected[1]


@pytest.mark.parametrize(
    "test, expected",
    (
        ("VW", ["volkswagen", "VW", "vw", "Volkswagen", "VOLKSWAGEN C.V."]),
        ("daimler-benz", []),
        ("Porsche", ["VW-Porsche", "Porsche", "porsche"]),
        ("DS", []),
        (None, []),
        ("Foo", []),
        ("DS", []),
        (None, []),
    ),
)
def test_get_brand_aliases(test: str, expected: List[str]) -> None:
    aliases: List = get_brand_aliases(brand_name=test)
    expected.sort()
    aliases.sort()
    assert aliases == expected


@pytest.mark.parametrize(
    "car_name, expected_brand, expected_car_name",
    (
        ("DS5 LS", "Citroën", "DS 5LS"),
        ("DS 5LS", "Citroën", "DS 5LS"),
        ("Abarth 500 SS", "Abarth", "500 SS"),
        ("Foo", None, None),
        (None, None, None),
    ),
)
def test_check_static_vehicles_list(
    car_name: str,
    expected_brand: str,
    expected_car_name: str,
) -> None:
    brand, name = check_static_vehicles_list(car_name=car_name)
    assert brand == expected_brand
    assert name == expected_car_name
