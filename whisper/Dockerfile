FROM pytorch/pytorch:2.2.2-cuda11.8-cudnn8-runtime

RUN apt-get update && apt-get install -y ffmpeg

RUN mkdir /stt
WorkDir /stt
COPY . /stt

RUN pip install --upgrade pip

COPY requirements.txt /stt/requirements.txt
RUN pip install -r /stt/requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]
