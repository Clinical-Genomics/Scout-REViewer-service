# Scout-REViewer-service

A rest service for generating [REViewer](https://github.com/Illumina/REViewer) and [trgt](https://github.com/PacificBiosciences/trgt) output.

Send in json/bed catalog with bam-let and vcf file, plus a reference genome. Get a SVG with graph alignments.

## Getting started

### To make it run (a bit more) quickly

Run with docker

#### Setup

``` bash
git clone <project>
cd <project>
```

Settings are read from environment variables. The image ships with
`cg.env.docker` as its `.env` file, whose values are used as defaults for any
setting not given in the environment. The `trgt` and `REViewer` binaries are
included in the image and on its `PATH`, so `REV_PATH` and `TRGT_PATH` can be
left as they are.

Create a docker specific env file called `.env.docker` in the root folder to
override the defaults for your setup, for example:

```
HOST_DATA=<absolute_path_to_host_machine_folder_with_reference_files>

REV_REF_PATH=/host_data/<reference_file_in_the_host_data_folder>.fasta
REV_CATALOG_PATH=data/catalog_test.json
TRGT_REF_PATH=/host_data/<reference_file_in_the_host_data_folder>.fasta
TRGT_CATALOG_PATH=/host_data/<trgt_repeat_catalog_in_the_host_data_folder>.bed
```

`HOST_DATA` is the host folder mounted (read-only) at `/host_data` in the
container. The reference and catalog paths are used when a request does not
provide its own. `REV_CATALOG_PATH` can point to a custom file in the
`host_data` folder, but a test catalog is included in the image.

#### run

``` bash
docker compose --env-file .env.docker up
```

`--env-file` provides `HOST_DATA` for the volume mount, and the compose
`env_file` passes the settings into the container. The service listens on port
5050; change the host side of `ports` in `docker-compose.yml` to expose it on
another port.

With plain `docker run`, pass settings with `-e` or `--env-file`:

``` bash
docker run --env-file .env.docker -v <host_data_folder>:/host_data:ro -p 5050:5050 clinicalgenomics/scout-reviewer-service
```

### To develop locally

#### Setup

``` bash
git clone <project>
cd <project>
```

Settings can be given as environment variables, or in a file called `.env` in
the folder you run the service from, for example:

```
REV_PATH=/Users/<User>/bin/REViewer/build/install/bin/REViewer
REV_REF_PATH=../my_host_data/human_g1k_v37_decoy.fasta
REV_CATALOG_PATH=data/catalog_test.json
```

2 changes that needs to be made are:

1. Update the `REV_PATH` value to point towards your instance of REViewer. See
   https://github.com/Illumina/REViewer for installation instructions.
2. Update the file name in the `REV_REF_PATH` to point towards a reference
   file.

`REV_CATALOG_PATH` can be changed to point to another catalog file but this is
not required as one is provided as default.

For the `/trgt` endpoint, also set `TRGT_PATH`, `TRGT_REF_PATH` and
`TRGT_CATALOG_PATH` (see `cg.env.docker` for an example). trgt release binaries
are available at https://github.com/PacificBiosciences/trgt/releases.

Dependencies are managed with [uv](https://docs.astral.sh/uv/). Install them
into a local virtual environment with:

``` bash
uv sync
```

#### Run (development)

``` bash
uv run uvicorn main:app --reload
```

### API

#### Example requests

Notice that the first time REViewer runs with a new reference file it will take
a bit longer since it will generate a `fasta.fai` file. You can avoid this by
adding a corresponding (same name, different file extension) `fasta.fai` file
to the same location as your fasta file (or provide one with the API request –
TBD) – if you already have one.

##### Files accessible from another server

If running in docker use `host.docker.internal` instead of `localhost` to
access your own server.

``` bash
curl --location --request POST 'http://127.0.0.1:8000/reviewer' \
--header 'Content-Type: application/json' \
--data-raw '{
  "reads": "http://localhost:5010/justhusky_exphun_hugelymodelbat_realigned.bam",
  "reads_index": "http://localhost:5010/justhusky_exphun_hugelymodelbat_realigned.bam.bai",
  "vcf": "http://localhost:5010/justhusky_exphun_hugelymodelbat.vcf",
  "catalog": "http://localhost:5010/catalog_test.json",
  "locus": "TCF4"
}'
```

##### Files from locally accessible file system

This will avoid copying the files and instead use the already existing files.
This is preferred if possible as it should be faster and reduce writes.

``` bash
curl --location --request POST 'http://127.0.0.1:8000/reviewer' \
--header 'Content-Type: application/json' \
--data-raw '{
  "reads": "/<path_to_file>/justhusky_exphun_hugelymodelbat_realigned.bam",
  "reads_index": "/<path_to_file>/justhusky_exphun_hugelymodelbat_realigned.bam.bai",
  "vcf": "/<path_to_file>/justhusky_exphun_hugelymodelbat.vcf",
  "catalog": "/<path_to_file>/catalog_test.json",
  "locus": "TCF4"
}'
```


##### Visualise with trgt

The `trgt` endpoint will instead run `trgt`. Note that trgt is under a restrictive license.

``` bash
curl --location --request POST 'http://127.0.0.1:8000/trgt' \
--header 'Content-Type: application/json' \
--data-raw '{
  "reads": "/<path_to_file>/justhusky_hugelymodelbat.trgt.bam",
  "reads_index": "/<path_to_file>/justhusky_hugelymodelbat.trgt.bam.bai",
  "vcf": "/<path_to_file>/justhusky_hugelymodelbat.trgt.vcf",
  "catalog": "/<path_to_file>/catalog_test.trgt.bed",
  "locus": "TCF4"
}'
```

Optional plot options are passed on to `trgt plot`:

| Field | Values | Default | trgt flag |
|---|---|---|---|
| `plot_type` | `allele`, `waterfall` | `allele` | `--plot-type` |
| `show` | `motifs`, `meth` (needs MM/ML methylation tags in the reads) | `motifs` | `--show` |
| `squished` | `true`, `false` | `false` | `--squished` |

For example, add `"plot_type": "waterfall", "squished": true` to the request
above for a compact waterfall plot. Other values are rejected with status 422.

#### Docs

Automatically generated API docs can be accessed at
`http://<server-address>:<port>/docs` when running the server. But the content
of this `README.md` is more extensive.

## Testing

The REViewer integration tests run when the `REViewer` binary is on `PATH` (Linux
x86_64 only, so they are skipped on e.g. macOS). They don't need `.env` or a full
reference: they use a small bgzipped stub of GRCh37 chromosome 18 with only the
TCF4 region, rebuilt with `tests/test_data/make_stub_reference.py`. CI installs the
REViewer version pinned in the `Dockerfile`.

The trgt tests run when `trgt` is on `PATH`. They download the small example
from the trgt repository at a pinned commit (checksums verified, cached in
`.pytest_cache`) and run `trgt genotype` on it. CI installs the pinned trgt too.

```
uv run pytest
```

Lint with

```
uv run --only-group lint black --check .
uv run --only-group lint isort --check-only .
```

The Docker image bundles statically linked trgt and REViewer release binaries
(x86_64 only), pinned by version and checksum in the `Dockerfile`.
