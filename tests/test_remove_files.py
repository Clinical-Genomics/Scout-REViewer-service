"""Test that per-request scratch files are cleaned up, also when plot generation fails."""

import asyncio
import os
import uuid

import pytest
from fastapi.testclient import TestClient

import main
from service.remove_files import remove_files
from service.utils.get_tmp_data_path import get_request_tmp_path, get_tmp_data_path

client = TestClient(main.app, raise_server_exceptions=False)


def test_remove_files_removes_request_dir_with_all_tool_outputs():
    file_id = str(uuid.uuid4())
    path = get_request_tmp_path(file_id)
    for name in ["reads.bam", "reviewer.TCF4.svg", "reviewer.metrics.tsv", "reviewer.phasing.tsv"]:
        with open(f"{path}/{name}", "w") as handle:
            handle.write("data")

    asyncio.run(remove_files(file_id))

    assert not os.path.exists(path)


def test_remove_files_missing_dir_is_ok():
    asyncio.run(remove_files(str(uuid.uuid4())))


def fake_tool_output(data, file_id, files):
    """Stand in for REViewer/trgt: write an SVG plus side outputs to the request dir."""
    path = get_request_tmp_path(file_id)
    for name in ["out.svg", "out.metrics.tsv", "out.phasing.tsv"]:
        with open(f"{path}/{name}", "w") as handle:
            handle.write('<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>')
    return f"{path}/out.svg"


def failing_tool(data, file_id, files):
    fake_tool_output(data, file_id, files)
    raise RuntimeError("tool failed")


def request_dirs():
    tmp_data = get_tmp_data_path()
    return set(os.listdir(tmp_data)) if os.path.isdir(tmp_data) else set()


@pytest.mark.parametrize(
    "endpoint, generator", [("/reviewer", "generate_svg"), ("/trgt", "generate_trgt_svg")]
)
@pytest.mark.parametrize("tool, status", [(fake_tool_output, 200), (failing_tool, 500)])
def test_endpoint_cleans_up(monkeypatch, tmp_path, endpoint, generator, tool, status):
    # GIVEN local input files, which must not be removed
    inputs = {}
    for key in ["reads", "reads_index", "vcf", "catalog"]:
        local_file = tmp_path / key
        local_file.write_text("data")
        inputs[key] = str(local_file)
    monkeypatch.setattr(main, generator, tool)
    before = request_dirs()

    # WHEN generating a plot, successfully or not
    res = client.post(endpoint, json={**inputs, "locus": "TCF4"})

    # THEN no request scratch dir is left behind, and the inputs are untouched
    assert res.status_code == status
    assert request_dirs() == before
    assert all(os.path.isfile(local_file) for local_file in inputs.values())
