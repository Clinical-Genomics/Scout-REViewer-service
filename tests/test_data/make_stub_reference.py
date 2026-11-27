"""Build the small stub GRCh37 reference used by the REViewer integration tests.

REViewer only reads the reference around the locus it plots, so instead of a full
GRCh37 fasta the tests use contig "18" with the real sequence for TCF4 and its
flanks (18:53233387-53273458), and N everywhere before it. bgzip-compressed, the
mostly-N contig is about 200 KB. REViewer output from this stub is identical to
output from the full hs37d5 reference.

Requires bgzip and samtools on PATH. Run from the repository root:

    python tests/test_data/make_stub_reference.py
"""

import subprocess
import urllib.request
from pathlib import Path

CONTIG = "18"
START = 53233387  # 1-based, inclusive
END = 53273458
LINE_WIDTH = 60
ENSEMBL_URL = (
    "https://grch37.rest.ensembl.org/sequence/region/human/"
    f"{CONTIG}:{START}..{END}:1?content-type=text/plain"
)
OUT = Path(__file__).parent / "stub_grch37_chr18.fa"


def main():
    with urllib.request.urlopen(ENSEMBL_URL) as response:
        sequence = response.read().decode().strip()
    assert len(sequence) == END - START + 1, f"unexpected sequence length {len(sequence)}"

    contig = "N" * (START - 1) + sequence
    with open(OUT, "w") as handle:
        handle.write(f">{CONTIG}\n")
        for i in range(0, len(contig), LINE_WIDTH):
            handle.write(contig[i : i + LINE_WIDTH] + "\n")

    subprocess.run(["bgzip", "--force", str(OUT)], check=True)
    subprocess.run(["samtools", "faidx", f"{OUT}.gz"], check=True)


if __name__ == "__main__":
    main()
