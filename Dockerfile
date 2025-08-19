FROM continuumio/miniconda3

COPY . /Scout-REViewer-service
COPY cg.env.docker .env

RUN conda env create -f /Scout-REViewer-service/environment.yml

WORKDIR /Scout-REViewer-service
RUN conda activate Scout-REViewer-service
RUN pip install .

ENTRYPOINT [\
    "conda", "run", "--no-capture-output", "-n", "Scout-REViewer-service", \
    "uvicorn", "main:app", "--app-dir", "/Scout-REViewer-service", "--host", "0.0.0.0", "--port", "5050" \
]
