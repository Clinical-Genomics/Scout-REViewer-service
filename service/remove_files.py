import asyncio
import shutil

from service.utils.get_tmp_data_path import get_tmp_data_path


async def remove_files(file_id: str):
    """Remove the per-request scratch directory, with all fetched inputs and tool outputs.

    Besides the SVG, REViewer also writes e.g. .metrics.tsv and .phasing.tsv next to it,
    so the whole directory is removed rather than a list of known files.
    """
    await asyncio.to_thread(shutil.rmtree, f"{get_tmp_data_path()}/{file_id}", ignore_errors=True)
