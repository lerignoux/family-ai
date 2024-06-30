FROM lerignoux/base-ai-service

RUN mkdir /stt
WORKDIR /stt
COPY . /stt

COPY requirements.txt /stt/requirements.txt
RUN --mount=type=cache,target=/root/.cache python3 -m pip install -r /stt/requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]
