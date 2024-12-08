# Build stage:
FROM python:3.10-slim AS build

ARG DEBIAN_FRONTEND=noninteractive
RUN --mount=type=cache,target=/root/.cache/apt apt-get update && apt-get install -y build-essential gcc gnupg2 git python-is-python3

# setup Comfy
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /ComfyUI --depth 1
RUN python3 -m venv /venv
ENV PATH=/venv/bin:$PATH

RUN --mount=type=cache,target=/root/.cache/pip python3 -m pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
RUN --mount=type=cache,target=/root/.cache/pip python3 -m pip install --upgrade pip
RUN --mount=type=cache,target=/root/.cache/pip python -m pip install -v -r /ComfyUI/requirements.txt

# Run stage:
FROM python:3.10-slim
LABEL authors="Laurent Erignoux lerignoux@gmail.com"

ARG DEBIAN_FRONTEND=noninteractive
RUN --mount=type=cache,target=/root/.cache/apt apt-get update && apt-get install -y --no-install-recommends git

# Copy the virtual environment and ComfyUI from the first stage.
COPY --from=build /ComfyUI /ComfyUI
COPY --from=build /venv /venv
ENV PATH=/venv/bin:$PATH
WORKDIR /ComfyUI
RUN cd /ComfyUI

CMD ["python", "main.py", "--listen", "0.0.0.0", "--multi-user", "--enable-cors-header"]
