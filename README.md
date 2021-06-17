# Scout-REViewer-service

A rest service for generating REViewer output.

## Getting started

### To test quickly

run with docker

#### Setup

``` bash
git clone <project>
cd <project>
```

#### run

``` bash
# docker build -t mybuild .
# docker run --rm --name mycontainer -p 5000:5000 mybuild
docker compose up
```

For file system access mount accordingly.

ex.

``` bash
docker build -t mybuild .
docker run --rm -v /Users/<User>/mydata:/mnt/mydata --name mycontainer -p 5000:5000 mybuild
```

For accessing locally hosted files on server see the API instructions.

### To develop locally

#### Prerequisites

Have access to files you want to run with/through REViewer.

Make sure ~conda is installed.

Add a reference (.fasta) file to data folder. (after cloning)

#### Setup

``` bash
git clone <project>
cd <project>
```

Set the path to your instance of REViewer and a the reference and cataolog
files that should be used as default. See https://github.com/Illumina/REViewer
for info about what a reference file and a catalog file is.

Notice that the first time REViewer runs with a new reference file it will take
a bit longer since it will generate a `fasta.fai` file. You can avoid this by
adding a corresponding (same name) `fasta.fai` file to the same location as your
fasta file.

``` bash
export REV_PATH="/Users/<User>/bin/REViewer/build/install/bin/REViewer"
export REV_REF_PATH="/Users/<User>/Scout-REViewer-service/reference_file_name.fasta"
export REV_CATALOG_PATH="/Users/<User>/Scout-REViewer-service/catalog.json"
```

``` bash
conda env create
```

#### Run (development)

``` bash
conda activate Scout-REViewer-service
```

``` bash
uvicorn main:app --reload
```

### API

Example requests

#### files accessible from another server

if running in docker use `host.docker.internal` instead of `localhost` to
access your own server

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

#### files from locally accessible file system

``` bash
curl --location --request POST 'http://127.0.0.1:8000/reviewer' \
--header 'Content-Type: application/json' \
--data-raw '{
  "reads": "/path_to_file/justhusky_exphun_hugelymodelbat_realigned.bam",
  "reads_index": "/path_to_file/justhusky_exphun_hugelymodelbat_realigned.bam.bai",
  "vcf": "/path_to_file/justhusky_exphun_hugelymodelbat.vcf",
  "catalog": "/path_to_file/catalog_test.json",
  "locus": "TCF4"
}'
```

## Testing

needs a `.fasta` reference file to run

```
pytest
```

## TODO

- [x] get files from remote
- [x] store files on server
- [x] run REViewer with local file path as arguments
- [x] send back REViewer generated SVG
- [x] bundle REViewer
- [X] Dockerize
- [ ] make smaller docker build
- [ ] delete tmp files, maybe it's good if this also runs as some kind of chron job
- [ ] think about if this is secure (enough)
- [x] tests
- [ ] more tests
- [ ] make sure to check if all files are created correctly after fetching
- [ ] validate urls – add helpful error messages if wrong file input
- [ ] prettify && DRY up
- [ ] handle files that are too large


### Ideas

- [ ] file uploader
- [ ] rate limiting
