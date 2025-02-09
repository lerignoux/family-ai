# Family AI
A web app proposing multiple ai services enhanced with a text to speech and speech to text interface.
The application is plugged to various "Ai" APIs to provide the following local hosted services:
* Chat discussion
* Translation
* Image generation
* Kid story creation

A CUDA enabled GPU is necessary to be able to perform the different API generations.

## tldr:
setup secrets in `secrets` folder
```shell
cp .env.tpl .env
docker compose up
```
open [http://localhost:9000](http://localhost:9000)

## Family Ai:
The personal assistant web app.

## APIs
see different APIs documentations are available at `http://localhost:8187/docs#` (replace the port depending on the services)

### Argos-translate:
a neural translation service cf [ArgosOpenTech](https://www.argosopentech.com/)

### Comfy
A GenAi tool to generate pictures but not only. cf [comfy.org](https://docs.comfy.org)

### Ollama:
A LLM Ai assistant using various models locally and cloud based. based on [Ollama](https://ollama.com/) and [LangChain](https://www.langchain.com/)

### TTS:
A text to speech utility using [coqui TTS](https://github.com/coqui-ai/TTS) and [kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)
A speech to text utility using [whisper](https://github.com/openai/whisper)

## Build:
Base image building:
```
docker build . -f Dockerfile -t lerignoux/base-ai-service
```

## hosting
To deploy the app on your own host,
* update the `HOST` variable in `.env`.
* update `app/family-ai/.env` file using the `family-ai/.env.prod` template, updating the relevant `<YourHost>`

## Multi-GPU
if you have multiple GPUs you can spread the load over them overriding the GPU id's
see `docker-compose.override.tpl.yml` for example:
```
cp docker-compose.override.tpl.yml docker-compose.override.yml
```

## Contributions:
* Contributions and bugs are welcome, please follow the standard open source procedure.

## License:
* Different services and code parts have their own licenses.
* The rest of the code follows a GPL v3 license. cf `./License.md`
