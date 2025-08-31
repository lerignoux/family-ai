FROM lerignoux/base-ai-service

RUN mkdir /app/argos-translate
WORKDIR /app/argos-translate
COPY . /app/argos-translate

RUN --mount=type=cache,target=/root/.cache/uv uv pip install -r /app/argos-translate/requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]
