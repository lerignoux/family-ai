import logging
import os
from typing import Union
import subprocess
import sys
from bson import ObjectId

import torch
from fastapi import FastAPI
from fastapi.responses import FileResponse
from TTS.api import TTS

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
log = logging.getLogger(__name__)

app = FastAPI()

device = "cuda" if torch.cuda.is_available() else "cpu"

MODELS_FOLDER = "/root/.local/share/tts"
DEFAULT_MODEL = "tts_models/en/ljspeech/fast_pitch"

ApiTTS = TTS(model_name=DEFAULT_MODEL, progress_bar=False).to(device)


def convert_to_mp3(filename, delete=True):
    """
    ffmpeg -i input.wav -vn -ar 44100 -ac 2 -b:a 192k output.mp3
    """
    output = filename.replace(".wav", ".mp3")
    command = f"ffmpeg -hwaccel cuda -y -i {filename} -vn -ar 44100 -ac 2 -b:a 192k {output}"
    log.info(f"Executing `{command}`")
    process = subprocess.Popen(command.split(" "))
    process.wait()
    if delete:
        os.remove(filename)
    return output


@app.get("/tts")
def read(sentence: str, model_name: str="tts_models/en/ljspeech/fast_pitch", vocoder_name="vocoder_models/en/ljspeech/hifigan_v2"):
    """
    Process the given input into audio convert in mp3 and returns it as a file.
    """
    output = f"/tts/output/output_{ObjectId()}.wav"

    if model_name != DEFAULT_MODEL:
        raise Exception("Custom models not supported")

    ApiTTS.tts_to_file(text=sentence, file_path=output)
    output_mp3 = convert_to_mp3(output)
    return FileResponse(output_mp3, media_type="audio/mpeg")


@app.get("/models")
def read_item():
    """
    List the currently available models.
    """
    tts_manager = TTS().list_models()
    models = { model:False for model in tts_manager.list_models()}
    for root, dirs, files in os.walk(MODELS_FOLDER):
        for directory in dirs:
            model_name = directory.replace("--", "/")
            log.info(models)
            if model_name in models:
                models[model_name] = True
            else:
                log.warning(f"Unknown model {model_name}")
    return models
