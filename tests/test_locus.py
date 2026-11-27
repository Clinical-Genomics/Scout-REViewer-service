"""Test that the locus can't be used to write files outside the request scratch dir."""

import subprocess

import pytest
from fastapi.testclient import TestClient

import service.generate_svg
from main import app
from service.utils.get_tmp_data_path import get_tmp_data_path

client = TestClient(app)

REQUEST = {
    "reads": "/data/reads.bam",
    "reads_index": "/data/reads.bam.bai",
    "vcf": "/data/calls.vcf",
    "catalog": "/data/catalog",
    "reference": "/data/reference.fasta",
}


@pytest.fixture
def fake_tool(monkeypatch):
    """Replace the REViewer/trgt call with one that records the command and writes an svg."""
    commands = []

    def run(cmd, **kwargs):
        commands.append(cmd)
        if "--image" in cmd:
            svg = cmd[cmd.index("--image") + 1]
        else:
            prefix = cmd[cmd.index("--output-prefix") + 1]
            svg = f"{prefix}.{cmd[cmd.index('--locus') + 1]}.svg"
        with open(svg, "w") as handle:
            handle.write('<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>')
        return subprocess.CompletedProcess(cmd, 0, stdout=b"")

    monkeypatch.setattr(service.generate_svg.subprocess, "run", run)
    return commands


@pytest.mark.parametrize("endpoint", ["/reviewer", "/trgt"])
@pytest.mark.parametrize("locus", ["../../evil", "a/b", "a\\b", "-h", ""])
def test_unsafe_locus_is_rejected(fake_tool, endpoint, locus):
    # WHEN requesting a plot for a locus with a path separator or a leading "-"
    res = client.post(endpoint, json={**REQUEST, "locus": locus})

    # THEN the request is rejected without running the tool
    assert res.status_code == 422
    assert fake_tool == []


@pytest.mark.parametrize("endpoint", ["/reviewer", "/trgt"])
@pytest.mark.parametrize("locus", ["TCF4", "C9ORF72", "chr4_3074876_3074968", "DMD.1", "ATXN8OS-1"])
def test_catalog_locus_ids_are_accepted(fake_tool, endpoint, locus):
    # WHEN requesting a plot for a typical catalog locus id
    res = client.post(endpoint, json={**REQUEST, "locus": locus})

    # THEN the plot is made
    assert res.status_code == 200
    assert (
        fake_tool[0][
            fake_tool[0].index("--locus" if endpoint == "/reviewer" else "--repeat-id") + 1
        ]
        == locus
    )


def test_trgt_output_file_does_not_use_locus(fake_tool):
    # WHEN requesting a trgt plot
    res = client.post("/trgt", json={**REQUEST, "locus": "TR1"})

    # THEN trgt writes to a fixed file name in the request scratch dir
    assert res.status_code == 200
    image = fake_tool[0][fake_tool[0].index("--image") + 1]
    assert image.startswith(f"{get_tmp_data_path()}/")
    assert image.endswith("/trgt.svg")
