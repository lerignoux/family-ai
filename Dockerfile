FROM dhi.io/python:3.14-debian13-dev
LABEL authors="Laurent Erignoux lerignoux@gmail.com"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/venv/bin:$PATH"

WORKDIR /app

RUN python -m venv /app/venv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENV UV_LINK_MODE=copy
RUN  --mount=type=cache,target=/root/.cache/apt apt-get update && apt-get install -y build-essential gcc gnupg2 wget curl ffmpeg git curl python-is-python3 pkg-config cmake
RUN python -m pip install uv wheel

RUN --mount=type=cache,target=/root/.cache/pip python3 -m pip install --upgrade pip setuptools wheel

COPY ./requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/uv uv pip install -r requirements.txt
