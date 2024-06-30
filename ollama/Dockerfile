FROM lerignoux/base-ai-service

RUN mkdir /ollama
WORKDIR /ollama
COPY . /ollama

COPY requirements.txt /ollama/requirements.txt
RUN --mount=type=cache,target=/root/.cache python -m pip install --upgrade -r /ollama/requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]
