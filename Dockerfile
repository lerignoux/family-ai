FROM python:3.10-slim
LABEL authors="Laurent Erignoux lerignoux@gmail.com"

ARG DEBIAN_FRONTEND=noninteractive
RUN  --mount=type=cache,target=/root/.cache/apt apt-get update && apt-get install -y build-essential gcc gnupg2 wget curl ffmpeg git python-is-python3

RUN --mount=type=cache,target=/root/.cache/pip python3 -m pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
RUN --mount=type=cache,target=/root/.cache/pip python3 -m pip install --upgrade pip
COPY ./requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip python3 -m pip install -r requirements.txt
