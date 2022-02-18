import json
import os
from os.path import basename
from pathlib import Path
from typing import Any, List, Optional
from zipfile import BadZipFile

import pytest
import responses

from app.core.config import settings
from app.misc.file_management import download_file_with_name, unzip_download


@pytest.mark.parametrize(
    "source_file,dest_file",
    (
        (settings.CARFUELDATA_TEST_PATH_OR_URL, "test1_output.zip"),
        (settings.CARFUELDATA_TEST_PATH_OR_URL, "test2_output.zip"),
        (None, None),
    ),
)
def test_download_file_with_name(
    source_file: str, dest_file: str, tmpdir: Path
) -> None:
    test: Optional[Path] = download_file_with_name(source_file, dest_file, tmpdir)
    if source_file and dest_file:
        assert isinstance(test, Path)
        assert basename(test) == dest_file
        assert test.exists()
    else:
        assert test is None


@pytest.mark.parametrize(
    "src_data,url,dest_file",
    (
        (
            settings.TEST_ENVIROCAR_PHENOMENONS_RESPONSE,
            "http://test.com/phenomenons.json",
            "phenomenons.json",
        ),
        (
            settings.TEST_ENVIROCAR_PHENOMENONS_RESPONSE,
            "https://test.com/phenomenons.json",
            "phenomenons.json",
        ),
    ),
)
def test_download_file_with_mock(
    src_data: str,
    url: str,
    dest_file: str,
    tmpdir: Path,
    json_download_mock: responses.RequestsMock,
) -> None:
    with open(src_data, mode="r") as f:
        phenomenons_response = json.load(f)
    with responses.RequestsMock() as rsps:
        rsps.add(
            method=responses.GET,
            url=url,
            json=phenomenons_response,
            status=200,
            content_type="application/json",
        )
        test: Optional[Path] = download_file_with_name(url, dest_file, tmpdir)
    assert isinstance(test, Path)
    assert basename(test) == dest_file
    assert test.exists()
    with open(test) as f:
        test_json = json.load(f)
        assert test_json
        assert test_json == phenomenons_response


@pytest.mark.parametrize(
    "src_data,url,dest_file",
    (
        (
            settings.TEST_ENVIROCAR_PHENOMENONS_RESPONSE,
            "http://mock.mock/wrong.json",
            "foo.json",
        ),
        (
            settings.TEST_ENVIROCAR_PHENOMENONS_RESPONSE,
            "https://mock.mock/wrong.json",
            "foo.json",
        ),
    ),
)
def test_download_file_with_mock_must_fail(
    src_data: str,
    url: str,
    dest_file: str,
    tmpdir: Path,
    json_download_mock: responses.RequestsMock,
) -> None:
    test: Optional[Path] = download_file_with_name(url, dest_file, tmpdir)
    assert Path("") == test


@pytest.mark.parametrize(
    "source_file,dest_file",
    (
        ("Foobar1", "foobar1_output.zip"),
        ("Foobar2", "foobar2_output.zip"),
    ),
)
def test_download_file_with_name_must_fail(
    source_file: str, dest_file: str, tmpdir: Path
) -> None:
    with pytest.raises(FileNotFoundError):
        download_file_with_name(source_file, dest_file, tmpdir)


@pytest.mark.parametrize(
    "source_file,return_values",
    ((settings.CARFUELDATA_TEST_PATH_OR_URL, ["Euro_6_latest.csv"]),),
)
def test_unzip_download(source_file: str, return_values: List, tmpdir: Path) -> None:
    test: List = unzip_download(Path(source_file), Path(tmpdir))
    file: Path
    for file in test:
        assert basename(file) in return_values
        assert file.exists()
    for return_value in return_values:
        assert Path(f"{tmpdir}/{return_value}").exists()
    # Test unzipping non-zip file returns just the file.
    for i in range(len(test)):
        test_non_zip: List = unzip_download(test[i], Path(""))
        assert len(test_non_zip) == 1
        assert test_non_zip[0].exists()
        assert test_non_zip[0] == test[i]


@pytest.mark.parametrize(
    "source_file, exception",
    (("Foobar.zip", FileNotFoundError), ("Foobar", FileNotFoundError)),
)
def test_unzip_download_file_doesnt_exist(
    source_file: str, exception: Any, tmpdir: Path
) -> None:
    with pytest.raises(exception):
        unzip_download(Path(source_file), Path(tmpdir))


def test_unzip_download_file_must_fail(
    tmpdir: Path,
) -> None:
    damaged_zip: Path = Path(os.path.join(tmpdir, "wrong.zip"))
    with open(damaged_zip, "w+") as f:
        f.write("This is not a zip file")
    with pytest.raises(BadZipFile):
        unzip_download(Path(damaged_zip), Path(tmpdir))
