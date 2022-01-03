from os.path import basename
from pathlib import Path
from typing import Any, List

import pytest

from app.core.config import settings
from app.misc.file_management import download_file_with_name, unzip_download


@pytest.mark.parametrize(
    "source_file,dest_file",
    (
        (settings.CARFUELDATA_TEST_PATH_OR_URL, "test1_output.zip"),
        (settings.CARFUELDATA_TEST_PATH_OR_URL, "test2_output.zip"),
    ),
)
def test_download_file_with_name(
    source_file: str, dest_file: str, tmpdir: Path
) -> None:
    test: Path = download_file_with_name(source_file, dest_file, tmpdir)
    assert isinstance(test, Path)
    assert basename(test) == dest_file
    assert test.exists()


@pytest.mark.parametrize(
    "source_file,dest_file",
    (("Foobar1", "foobar1_output.zip"), ("Foobar2", "foobar2_output.zip"),),
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
def test_unzip_download_must_fail(
    source_file: str, exception: Any, tmpdir: Path
) -> None:
    with pytest.raises(exception):
        unzip_download(Path(source_file), Path(tmpdir))
