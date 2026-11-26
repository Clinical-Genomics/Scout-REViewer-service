"""
Test REViewer svg generation.

Integration tests that test the whole stack:
  * The API
  * Data storage, retrieval and deletion.
  * Running the REViewer binary with real data

Instead of a full GRCh37 reference, the tests use a small stub reference with only
the TCF4 region of chromosome 18 (see tests/test_data/make_stub_reference.py) and a
catalog with only TCF4, since REViewer rejects catalog contigs missing from the
reference. The expected SVG was generated with REViewer v0.2.7 and the full hs37d5
reference, and is identical to the stub output.

The tests are skipped when REViewer is not on PATH.
"""

import os
import shutil

import pytest
from fastapi.testclient import TestClient

from main import app
from service.utils.get_root_path import get_root_path
from tests.test_data.example_svg import SVG

client = TestClient(app)

test_data = f"{get_root_path()}/tests/test_data"
reads = f"{test_data}/justhusky_exphun_hugelymodelbat_realigned.bam"
reads_index = f"{test_data}/justhusky_exphun_hugelymodelbat_realigned.bam.bai"
vcf = f"{test_data}/justhusky_exphun_hugelymodelbat.vcf"
reference = f"{test_data}/stub_grch37_chr18.fa.gz"
reference_index = f"{reference}.fai"
catalog = f"{test_data}/catalog_tcf4.json"
locus = "TCF4"

reviewer_path = shutil.which("REViewer")

requires_reviewer = pytest.mark.skipif(
    reviewer_path is None, reason="REViewer integration tests need REViewer on PATH"
)


@pytest.fixture
def settings(monkeypatch):
    """Service settings pointing at the test data, overriding the environment and .env."""
    monkeypatch.setenv("REV_PATH", reviewer_path)
    monkeypatch.setenv("REV_REF_PATH", reference)
    monkeypatch.setenv("REV_CATALOG_PATH", catalog)


def test_files_has_data():
    assert os.path.getsize(reads) != 0
    assert os.path.getsize(reads_index) != 0
    assert os.path.getsize(vcf) != 0
    assert os.path.getsize(reference) != 0
    assert os.path.getsize(reference_index) != 0
    assert os.path.getsize(catalog) != 0


def test_root():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json() == {"message": "Scout-REViewer-service is running!"}


@requires_reviewer
def test_path_api_with_no_optional_values(settings):
    json = {"reads": reads, "reads_index": reads_index, "vcf": vcf, "locus": locus}

    res = client.post(
        "/reviewer",
        json=json,
    )
    assert res.status_code == 200
    assert res.text == SVG


@requires_reviewer
def test_path_api_with_optional_values(settings, monkeypatch):
    # Defaults that would fail, so the test only passes if the request's files are used
    monkeypatch.setenv("REV_REF_PATH", "/nonexistent/reference.fasta")
    monkeypatch.setenv("REV_CATALOG_PATH", "/nonexistent/catalog.json")
    json = {
        "reads": reads,
        "reads_index": reads_index,
        "vcf": vcf,
        "reference": reference,
        "reference_index": reference_index,
        "catalog": catalog,
        "locus": locus,
    }

    res = client.post(
        "/reviewer",
        json=json,
    )
    assert res.status_code == 200
    assert res.text == SVG
