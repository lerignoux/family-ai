# Personal AI
a web app proposing multiple ai services.
the fefront end is plugged to various baarious backend services

## tldr:
setup secrets in `secrets` folder

```
docker compose up
```
open http://localhost:8080

## Personal AI:
The personal assistant web app.

## whisper:
A speech to text utility using [whisper](https://github.com/openai/whisper)

## tts:
A text to speech utility using [coqui TTS](https://github.com/coqui-ai/TTS)

### Api usage:
see Swagger available at `http://localhost:5174/docs#`

## ollama:
A LLM Ai assistant using various models locally and cloud.

## Build:
Base image building:
```
docker build . -f Dockerfile -t lerignoux/base-ai-service
```

## Multi-GPU
if you have multiple GPUs you can spread the load over them overriding the GPU id's
see `docker-compose.override.tpl.yml` for example:
```
cp docker-compose.override.tpl.yml docker-compose.override.yml
```
