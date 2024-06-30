FROM lerignoux/base-ai-service

RUN mkdir /tts
WORKDIR /tts
COPY . /tts

RUN --mount=type=cache,target=/root/.cache python3 -m pip install --upgrade -r /tts/requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]
