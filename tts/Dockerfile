FROM lerignoux/base-ai-service

RUN --mount=type=cache,target=/root/.cache/apt apt-get update && apt-get install -y --no-install-recommends ffmpeg espeak-ng fonts-noto-color-emoji

RUN mkdir /app/tts
WORKDIR /app/tts
COPY . /app/tts

RUN --mount=type=cache,target=/root/.cache/uv uv pip install -r /app/tts/requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
