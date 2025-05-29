# Build stage:
FROM python:3.12-slim AS build

ARG DEBIAN_FRONTEND=noninteractive
RUN --mount=type=cache,target=/root/.cache/apt apt-get update && apt-get install -y build-essential gcc gnupg2 git python-is-python3 python3-opencv
RUN python -m pip install uv

# setup Comfy
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /ComfyUI --depth 1
WORKDIR /ComfyUI

RUN uv venv
ENV PATH=/ComfyUI/.venv/bin:$PATH
COPY custom_nodes /ComfyUI/custom_nodes

RUN --mount=type=cache,target=/root/.cache/pip find /ComfyUI/custom_nodes -maxdepth 2 -name requirements.txt -type f | xargs | sed "s/ / -r /g" | xargs uv pip install -r /ComfyUI/requirements.txt -r

# Run stage:
FROM python:3.12-slim
LABEL authors="Laurent Erignoux lerignoux@gmail.com"

ARG DEBIAN_FRONTEND=noninteractive
RUN --mount=type=cache,target=/root/.cache/apt apt-get update && apt-get install -y --no-install-recommends git python3-opencv

# Copy the virtual environment and ComfyUI from the first stage.
COPY --from=build /ComfyUI /ComfyUI
WORKDIR /ComfyUI
ENV PATH=/ComfyUI/.venv/bin:$PATH

CMD ["python", "main.py", "--listen", "0.0.0.0", "--multi-user", "--enable-cors-header"]
