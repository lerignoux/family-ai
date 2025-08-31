FROM python:3.12-slim
LABEL authors="Laurent Erignoux lerignoux@gmail.com"

ARG DEBIAN_FRONTEND=noninteractive
RUN  --mount=type=cache,target=/root/.cache/apt apt-get update && apt-get install -y build-essential gcc gnupg2 wget curl ffmpeg git curl python-is-python3
RUN python -m pip install uv wheel

RUN --mount=type=cache,target=/root/.cache/pip python3 -m pip install --upgrade pip setuptools wheel

RUN mkdir /app
WORKDIR /app
RUN uv venv
ENV PATH=/app/.venv/bin:$PATH

COPY ./requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/uv uv pip install -r requirements.txt
