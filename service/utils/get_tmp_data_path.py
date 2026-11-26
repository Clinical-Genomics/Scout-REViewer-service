import os

from service.utils.get_root_path import get_root_path


def get_tmp_data_path():
    root_path = get_root_path()

    return f"{root_path}/tmp_data"


def get_request_tmp_path(file_id: str) -> str:
    """Return (and create) a per-request scratch directory under tmp_data.

    Everything a request downloads or generates lives here, so cleanup is a
    single directory removal that can never touch user-supplied local files.
    """
    path = f"{get_tmp_data_path()}/{file_id}"
    os.makedirs(path, exist_ok=True)

    return path
