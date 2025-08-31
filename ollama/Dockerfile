FROM lerignoux/base-ai-service

RUN mkdir /app/ollama
WORKDIR /app/ollama
COPY . /app/ollama

RUN --mount=type=cache,target=/root/.cache/uv uv pip install --upgrade -r /app/ollama/requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]
