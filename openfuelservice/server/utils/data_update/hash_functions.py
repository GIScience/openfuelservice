import hashlib
from pathlib import Path


def file_hash(file: Path) -> str:
    """
    Gets the sha1 hash from any file provided.

    :param file:
    :return: A string holding the sha1 hash
    :rtype: str
    :exception: A FileNotFoundError is raised.
    """
    try:
        blocksize = 65536
        hasher = hashlib.sha1()
        with open(file, 'rb') as f:
            buf = f.read(blocksize)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(blocksize)
        return hasher.hexdigest()
    except FileNotFoundError as err:
        print(err)
