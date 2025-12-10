FROM lerignoux/base-ai-service as build

ARG DEBIAN_FRONTEND=noninteractive
RUN --mount=type=cache,target=/root/.cache/apt apt-get install -y cmake libcairo2-dev
# setup Comfy
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /app/ComfyUI --depth 1

COPY custom_nodes /app/ComfyUI/custom_nodes

RUN --mount=type=cache,target=/root/.cache/uv find /app/ComfyUI/custom_nodes -maxdepth 2 -name requirements.txt -type f | xargs | sed "s/ / -r /g" | xargs uv pip install -r /app/ComfyUI/requirements.txt -r

# Run stage:
FROM python:3.12-slim
LABEL authors="Laurent Erignoux lerignoux@gmail.com"

ARG DEBIAN_FRONTEND=noninteractive
RUN --mount=type=cache,target=/root/.cache/apt apt-get update && apt-get install -y --no-install-recommends git python3-opencv

# Copy the virtual environment and ComfyUI from the first stage.
COPY --from=build /app/ComfyUI /app/ComfyUI
COPY --from=build /app/.venv /app/.venv
WORKDIR /app/ComfyUI
ENV PATH=/app/.venv/bin:$PATH

CMD ["python", "main.py", "--listen", "0.0.0.0", "--multi-user", "--enable-cors-header"]
