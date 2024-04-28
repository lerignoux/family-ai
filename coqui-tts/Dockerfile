FROM python:3.10-slim

RUN apt-get update && apt-get install -y alsa-utils ffmpeg build-essential

COPY requirements.txt /tts/requirements.txt

RUN pip install --upgrade pip

RUN pip install --upgrade -r /tts/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

WorkDir /tts

COPY . /tts

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]
