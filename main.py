import uuid
from typing import Literal

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from service.generate_svg import generate_svg, generate_trgt_svg
from service.get_files import get_files
from service.get_svg_as_string import get_svg_as_string
from service.get_versions import get_versions
from service.modify_svg import modify_svg
from service.remove_files import remove_files

tags_metadata = [
    {
        "name": "root",
        "description": "Just a convenient way to check if the server is running.",
    },
    {
        "name": "reviewer",
        "description": "Generates a REViewer svg. See README.md for setup instructions.",
    },
    {
        "name": "trgt",
        "description": "Generates a trgt plot svg. See README.md for setup instructions.",
    },
    {
        "name": "version",
        "description": "Returns versions of REViewer and trgt binaries.",
    },
]

app = FastAPI(openapi_tags=tags_metadata)


@app.get("/", tags=["root"])
async def root():
    return {"message": "Scout-REViewer-service is running!"}


class Reviewer(BaseModel):
    reads: str
    reads_index: str
    vcf: str
    reference: str | None = None
    reference_index: str | None = None
    catalog: str | None = None
    # The locus ends up in REViewer's output file name, so no path separators, and no
    # leading "-" that the tools could read as an option.
    locus: str = Field(pattern=r"^[^/\\-][^/\\]*$", description="Locus/repeat id in the catalog")


@app.post("/reviewer", response_class=PlainTextResponse, tags=["reviewer"])
async def reviewer(request_data: Reviewer):
    file_id = str(uuid.uuid4())
    data = request_data.model_dump()
    try:
        files = await get_files(data, file_id)
        path_to_svg = generate_svg(data, file_id, files)
        modify_svg(path_to_svg)
        return get_svg_as_string(path_to_svg)
    finally:
        await remove_files(file_id)


class Trgt(Reviewer):
    plot_type: Literal["allele", "waterfall"] = Field(
        "allele",
        description="trgt plot --plot-type: allele (default) or waterfall.",
    )
    show: Literal["motifs", "meth"] = Field(
        "motifs",
        description="trgt plot --show: motifs (default) or meth, which needs MM/ML methylation tags.",
    )
    squished: bool = Field(False, description="trgt plot --squished: a more compact plot.")


@app.post("/trgt", response_class=PlainTextResponse, tags=["trgt"])
async def trgt(request_data: Trgt):
    file_id = str(uuid.uuid4())
    data = request_data.model_dump()
    try:
        files = await get_files(data, file_id)
        path_to_svg = generate_trgt_svg(data, file_id, files)
        return get_svg_as_string(path_to_svg)
    finally:
        await remove_files(file_id)


@app.get("/version", response_class=PlainTextResponse, tags=["version"])
async def version():
    return get_versions()
