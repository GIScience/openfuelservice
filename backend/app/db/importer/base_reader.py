import shutil
import tempfile
from pathlib import Path


class BaseReader:
    def __init__(self) -> None:
        self.tempfolder: Path = Path(tempfile.mkdtemp())

    def close(self) -> None:
        shutil.rmtree(self.tempfolder)