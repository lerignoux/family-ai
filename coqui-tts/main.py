import logging
import os
from typing import Union
import subprocess
import sys
from bson import ObjectId

import torch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from TTS.api import TTS


logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
log = logging.getLogger(__name__)


debug = os.getenv('DEBUG', '').lower() in ['1', 'true']


app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:5174",
    "https://ai.shanghai.laurent.erignoux.fr:5174",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODELS_FOLDER = "/root/.local/share/tts"
DEFAULT_MODEL = "tts_models/en/ljspeech/fast_pitch"

ApiTTS = TTS(model_name=DEFAULT_MODEL, progress_bar=False).to('cuda')


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


def clean_input(sentence):
    return sentence.replace("\"", "").replace("'", "").replace("\n", "")


class TTSRequest(BaseModel):
    sentence: str
    model: str = "tts_models/en/ljspeech/fast_pitch"
    vocoder: str = "vocoder_models/en/ljspeech/hifigan_v2"


@app.post("/tts")
def readPost(query: TTSRequest):
    """
    Process the given input into audio convert in mp3 and returns it as a file.
    """
    output_wav = f"/tts/output/output_{ObjectId()}.wav"
    sentence = clean_input(query.sentence)
    log.debug(f"Requested to voice: `{sentence}`")

    ApiTTS.tts_to_file(text=sentence, file_path=output_wav)
    output_mp3 = convert_to_mp3(output_wav)

    os.remove(output_wav)
    if not debug:
        os.remove(output_mp3)
    return FileResponse(output_mp3, media_type="audio/mpeg")


@app.get("/tts")
def readGet(
    sentence: str,
    model: str="tts_models/en/ljspeech/fast_pitch",
    vocoder="vocoder_models/en/ljspeech/hifigan_v2"
):
    """
    Process the given input into audio convert in mp3 and returns it as a file.
    """
    output_wav = f"/tts/output/output_{ObjectId()}.wav"
    sentence = clean_input(sentence)
    log.debug(f"Requested to voice: `{sentence}`")

    ApiTTS.tts_to_file(text=sentence, file_path=output_wav)
    output_mp3 = convert_to_mp3(output_wav)

    os.remove(output_wav)
    if not debug:
        os.remove(output_mp3)
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
