import asyncio
import urllib

import aiofiles
from aiohttp import ClientSession

from service.utils.get_tmp_data_path import get_request_tmp_path


async def save(data, file_name_suffix, file_id, file_type):
    path = get_request_tmp_path(file_id)
    # The bam-index file need to have the same filename as the read-bam file
    # for REViewer to recognize it. So we have this check here and change the
    # suffix acordingly.
    suffix = "reads" if file_name_suffix == "reads_index" else file_name_suffix
    file_name = f"{path}/{suffix}.{file_type}"

    async with aiofiles.open(file_name, "wb") as out:
        await out.write(data)
        await out.flush()

    return {file_name_suffix: file_name}


async def get_data(session, data, data_type, url, file_id, file_type):
    # optional input not given: leave it out, the tool's configured default is used
    if not url:
        return {}

    # if path (non url) we don't need to fetch and store the file and can just
    # use the file directly
    if urllib.parse.urlparse(url).scheme == "":
        return {data_type: url}

    respone = await session.get(url)
    file_name = await save(await respone.read(), data_type, file_id, file_type)

    return file_name


async def get_files(data, file_id):
    async with ClientSession() as session:

        results = await asyncio.gather(
            asyncio.create_task(
                get_data(
                    session,
                    data,
                    "catalog",
                    data.get("catalog"),
                    file_id,
                    "json",
                )
            ),
            asyncio.create_task(
                get_data(session, data, "reads", data.get("reads", ""), file_id, "bam")
            ),
            asyncio.create_task(
                get_data(
                    session,
                    data,
                    "reads_index",
                    data.get("reads_index", ""),
                    file_id,
                    "bam.bai",
                )
            ),
            asyncio.create_task(
                get_data(session, data, "vcf", data.get("vcf", ""), file_id, "vcf")
            ),
        )

        return {**results[0], **results[1], **results[2], **results[3]}
