import shutil
import tempfile
from pathlib import Path


class BaseReader:
    def __init__(self):
        self.tempfolder: Path = Path(tempfile.mkdtemp())

    def close(self):
        shutil.rmtree(self.tempfolder)
