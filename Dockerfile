###########
# BUILDER #
###########
FROM ghcr.io/astral-sh/uv:python3.14-trixie AS builder

# Statically linked x86_64 release binaries, pinned by version and checksum
ARG TRGT_VERSION=5.1.0
ARG TRGT_SHA256=2ab9ddb0f52516ea92de66c336c151dc3bd5bb22494e2b9dcb8bffa9eb710f63
ARG REVIEWER_VERSION=0.2.7
ARG REVIEWER_SHA256=7b77536f6c3cda16e08f53eba44d3329bb9bc44356f04644a765b6fc79fdbd31

WORKDIR /tmp/bin
RUN curl -fsSL -o trgt.tar.gz \
        "https://github.com/PacificBiosciences/trgt/releases/download/v${TRGT_VERSION}/trgt-v${TRGT_VERSION}-x86_64-unknown-linux-gnu.tar.gz" && \
    echo "${TRGT_SHA256}  trgt.tar.gz" | sha256sum -c && \
    tar -xzf trgt.tar.gz --strip-components=1 && \
    curl -fsSL -o REViewer.gz \
        "https://github.com/Illumina/REViewer/releases/download/v${REVIEWER_VERSION}/REViewer-v${REVIEWER_VERSION}-linux_x86_64.gz" && \
    echo "${REVIEWER_SHA256}  REViewer.gz" | sha256sum -c && \
    gunzip REViewer.gz && \
    install -m 755 trgt REViewer /usr/local/bin/

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project
COPY main.py ./
COPY service ./service
COPY data ./data
RUN uv sync --frozen --no-dev

#########
# FINAL #
#########
FROM python:3.14-slim-trixie

LABEL about.home="https://github.com/Clinical-Genomics/Scout-REViewer-service"
LABEL about.license="MIT License (MIT)"

RUN groupadd --gid 1000 worker && \
    useradd -g worker --uid 1000 --shell /usr/sbin/nologin --create-home worker

COPY --from=builder /usr/local/bin/trgt /usr/local/bin/REViewer /usr/local/bin/
COPY --from=builder /app /app
COPY cg.env.docker /app/.env

WORKDIR /app
RUN mkdir -p /app/tmp_data && chown worker:worker /app/tmp_data

ENV PATH="/app/.venv/bin:$PATH"
USER worker

EXPOSE 5050
ENTRYPOINT ["uvicorn", "main:app", "--app-dir", "/app", "--host", "0.0.0.0", "--port", "5050"]
