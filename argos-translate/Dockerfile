FROM lerignoux/base-ai-service

RUN mkdir /argos-translate
WORKDIR /argos-translate
COPY . /argos-translate

RUN git config --global http.proxy http://192.168.2.3:6665
RUN --mount=type=cache,target=/root/.cache/pip python3 -m pip install -r /argos-translate/requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]
