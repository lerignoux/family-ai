# Build stage:
FROM python:3.10-slim AS build

ARG DEBIAN_FRONTEND=noninteractive
RUN --mount=type=cache,target=/root/.cache/apt apt-get update && apt-get install -y build-essential gcc gnupg2 wget curl python-is-python3

# Create the virtual environment.
RUN python3 -m venv /venv
ENV PATH=/venv/bin:$PATH
COPY ./requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip python3 -m pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
RUN --mount=type=cache,target=/root/.cache/pip python3 -m pip install --upgrade pip setuptools wheel
RUN --mount=type=cache,target=/root/.cache/pip python3 -m pip install -r requirements.txt

# Run stage:
FROM python:3.10-slim
LABEL authors="Laurent Erignoux lerignoux@gmail.com"

ARG DEBIAN_FRONTEND=noninteractive
RUN --mount=type=cache,target=/root/.cache/apt apt-get update && apt-get install -y --no-install-recommends ffmpeg

# Copy the virtual environment from the first stage.
COPY --from=build /venv /venv
ENV PATH=/venv/bin:$PATH

RUN mkdir /tts
WORKDIR /tts
COPY . /tts

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]
