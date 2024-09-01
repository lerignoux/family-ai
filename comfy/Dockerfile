FROM lerignoux/base-ai-service

# Setup global requirements
RUN mkdir /comfy
WORKDIR /comfy
COPY . /comfy

RUN --mount=type=cache,target=/root/.cache/pip python3 -m pip install --upgrade -r requirements.txt


# setup Comfy
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /ComfyUI
WORKDIR /ComfyUI
RUN cd /ComfyUI
RUN --mount=type=cache,target=/root/.cache/pip python -m pip install -v -r /ComfyUI/requirements.txt

CMD ["python", "main.py", "--listen", "0.0.0.0", "--multi-user"]
