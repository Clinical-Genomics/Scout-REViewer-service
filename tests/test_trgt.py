"""Test the /trgt endpoint and its plot options.

The integration tests use the small example from the trgt repository. It is downloaded
at a pinned commit and checked against known checksums, rather than copied into this
repository, since trgt is under a restrictive license. The tests run trgt genotype on
it to get the spanning reads and VCF that trgt plot needs.

The integration tests are skipped when trgt is not on PATH.
"""

import hashlib
import re
import shutil
import subprocess
import urllib.request

import pytest
from fastapi.testclient import TestClient

import service.generate_svg
from main import app

client = TestClient(app)

TRGT_EXAMPLE_URL = (
    "https://raw.githubusercontent.com/PacificBiosciences/trgt/"
    "b21c6217eeaef9a080205932fe29f730dc00e31f/example"
)
TRGT_EXAMPLE_FILES = {
    "reference.fasta": "c34cd2f0836586b767f9720c1959a12bc1d34aca57d17059092fcf10724f62af",
    "reference.fasta.fai": "20bce001e4a7d2c4b00dd6064cb96297a1835d59b377b9206c4f543060edf4b1",
    "repeat.bed": "eb7d35d9196bb3cf14d43b35209d9d8278e74c7ea834c4a0f76754bd20e8e7cc",
    "sample.bam": "b2774a6614316c8e38bda3fa2b59211f1c73e08efc83efadd787e38032b293d8",
    "sample.bam.bai": "1a2fca82cfa8bbed101a5f5ba1596ac6c8124ec81ff3bd2b68d5c50f00e1eae0",
}
TRGT_EXAMPLE_LOCUS = "TR1"

trgt_path = shutil.which("trgt")

requires_trgt = pytest.mark.skipif(
    trgt_path is None, reason="trgt integration tests need trgt on PATH"
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def svg_height(svg):
    return float(re.search(r'<svg[^>]*\bheight="([0-9.]+)', svg).group(1))


@pytest.fixture
def fake_trgt(monkeypatch):
    """Replace the trgt call with one that records the command and writes a dummy svg."""
    commands = []

    def run(cmd, **kwargs):
        commands.append(cmd)
        with open(cmd[cmd.index("--image") + 1], "w") as handle:
            handle.write("<svg></svg>")
        return subprocess.CompletedProcess(cmd, 0, stdout=b"")

    monkeypatch.setattr(service.generate_svg.subprocess, "run", run)
    return commands


FAKE_REQUEST = {
    "reads": "/data/sample.spanning.bam",
    "reads_index": "/data/sample.spanning.bam.bai",
    "vcf": "/data/sample.vcf.gz",
    "reference": "/data/reference.fasta",
    "catalog": "/data/repeat.bed",
    "locus": "TR1",
}


def test_trgt_default_plot_options(fake_trgt):
    # WHEN requesting a trgt plot without plot options
    res = client.post("/trgt", json=FAKE_REQUEST)

    # THEN trgt is asked for its default allele plot with motifs, not squished
    assert res.status_code == 200
    cmd = fake_trgt[0]
    assert cmd[cmd.index("--plot-type") + 1] == "allele"
    assert cmd[cmd.index("--show") + 1] == "motifs"
    assert "--squished" not in cmd


def test_trgt_plot_options_are_passed_on(fake_trgt):
    # WHEN requesting a squished waterfall plot showing methylation
    res = client.post(
        "/trgt",
        json={**FAKE_REQUEST, "plot_type": "waterfall", "show": "meth", "squished": True},
    )

    # THEN the options are passed on to trgt plot
    assert res.status_code == 200
    cmd = fake_trgt[0]
    assert cmd[cmd.index("--plot-type") + 1] == "waterfall"
    assert cmd[cmd.index("--show") + 1] == "meth"
    assert "--squished" in cmd


@pytest.mark.parametrize(
    "option", [{"plot_type": "--image=/tmp/x.svg"}, {"show": "everything"}, {"squished": "a lot"}]
)
def test_trgt_invalid_plot_options_are_rejected(fake_trgt, option):
    # WHEN requesting a plot with an unknown option value
    res = client.post("/trgt", json={**FAKE_REQUEST, **option})

    # THEN the request is rejected without running trgt
    assert res.status_code == 422
    assert fake_trgt == []


@pytest.fixture(scope="session")
def trgt_example(request):
    """Download the trgt example and genotype it, giving the files trgt plot needs."""
    pysam = pytest.importorskip("pysam")
    path = request.config.cache.mkdir("trgt_example")

    for name, checksum in TRGT_EXAMPLE_FILES.items():
        file = path / name
        if not file.exists() or sha256(file) != checksum:
            urllib.request.urlretrieve(f"{TRGT_EXAMPLE_URL}/{name}", file)
        assert sha256(file) == checksum, f"unexpected checksum for downloaded {name}"

    subprocess.run(
        [
            trgt_path,
            "genotype",
            "--genome",
            path / "reference.fasta",
            "--repeats",
            path / "repeat.bed",
            "--reads",
            path / "sample.bam",
            "--output-prefix",
            path / "sample",
        ],
        check=True,
    )
    # trgt plot needs the spanning reads sorted and indexed
    spanning = path / "sample.spanning.sorted.bam"
    pysam.sort("-o", str(spanning), str(path / "sample.spanning.bam"))
    pysam.index(str(spanning))

    return {
        "reads": str(spanning),
        "reads_index": f"{spanning}.bai",
        "vcf": str(path / "sample.vcf.gz"),
        "reference": str(path / "reference.fasta"),
        "catalog": str(path / "repeat.bed"),
        "locus": TRGT_EXAMPLE_LOCUS,
    }


@pytest.fixture
def trgt_settings(monkeypatch):
    monkeypatch.setenv("TRGT_PATH", trgt_path)


def plot(trgt_example, **options):
    res = client.post("/trgt", json={**trgt_example, **options})
    assert res.status_code == 200
    assert "<svg" in res.text
    return res.text


@requires_trgt
def test_trgt_plot_types(trgt_example, trgt_settings):
    # WHEN plotting the example as an allele plot (the default) and as a waterfall plot
    default = plot(trgt_example)
    allele = plot(trgt_example, plot_type="allele")
    waterfall = plot(trgt_example, plot_type="waterfall")

    # THEN the default is the allele plot, and the waterfall plot differs from it
    assert default == allele
    assert waterfall != allele


@requires_trgt
def test_trgt_squished(trgt_example, trgt_settings):
    # WHEN plotting the example squished
    allele = plot(trgt_example)
    squished = plot(trgt_example, squished=True)

    # THEN the plot is more compact (trgt draws the reads thinner, so it gets less tall)
    assert svg_height(squished) < svg_height(allele)


@requires_trgt
def test_trgt_show_meth(trgt_example, trgt_settings):
    # WHEN plotting methylation (the example reads have no methylation tags)
    motifs = plot(trgt_example, plot_type="waterfall")
    meth = plot(trgt_example, plot_type="waterfall", show="meth")

    # THEN trgt still makes a plot, which differs from the motif plot
    assert meth != motifs
