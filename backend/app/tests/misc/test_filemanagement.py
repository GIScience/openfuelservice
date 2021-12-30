from os.path import basename
from pathlib import Path
from typing import Any, List

import pytest

from app.core.config import settings
from app.misc.file_management import download_file_with_name, unzip_download


@pytest.mark.parametrize(
    "source_file,dest_file,return_type",
    (
        (settings.CARFUELDATA_TEST_PATH_OR_URL, "test1_output.zip", Path),
        (settings.CARFUELDATA_TEST_PATH_OR_URL, "test2_output.zip", Path),
        ("Foobar", "test3_output.zip", FileNotFoundError),
    ),
)
def test_download_file_with_name(
    source_file: str, dest_file: str, return_type: Any, tmpdir: Path
) -> None:
    test: Path | FileNotFoundError = download_file_with_name(
        source_file, dest_file, tmpdir
    )
    assert isinstance(test, return_type)
    if not isinstance(test, FileNotFoundError):
        assert basename(test) == dest_file
        assert test.exists()


@pytest.mark.parametrize(
    "source_file,return_values",
    ((settings.CARFUELDATA_TEST_PATH_OR_URL, ["Euro_6_latest.csv"]), ("Foobar", []),),
)
def test_unzip_download(source_file: str, return_values: List, tmpdir: Path) -> None:
    test: List = unzip_download(Path(source_file), Path(tmpdir))
    if not len(test):
        assert len(test) == len(return_values)
    else:
        for return_value in return_values:
            assert Path(f"{tmpdir}/{return_value}").exists()
