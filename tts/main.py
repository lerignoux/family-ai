import aiofiles
import logging
import os
import subprocess
import sys
from typing import Union, Annotated

from bson import ObjectId
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from kokoro_tts import text_to_audio
from pydantic import BaseModel
import whisper
import whisper_timestamped
from whisper_timestamped.make_subtitles import write_srt


logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
log = logging.getLogger(__name__)

debug = os.getenv('DEBUG', '').lower() in ['1', 'true']

app = FastAPI()

origins = ["http://localhost", "https://localhost"]
if 'HOST' in os.environ:
    origins.append(f"{os.environ['HOST']}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# FIXME Need to check the quality/speed we want.
DEFAULT_MODEL = "small"
log.info(f"Loading whisper model {DEFAULT_MODEL}")
STT_MODEL = whisper.load_model(DEFAULT_MODEL).to("cuda")
MODELS_FOLDER = "/root/.local/share/tts"
DEFAULT_MODEL = "tts_models/en/ljspeech/fast_pitch"


stt_language = {
    'en': "English",
    'es': "Espanol",
    'fr': "French",
    'zh': "Chinese",
    'jp': "Janaese"
}


class TTSRequest(BaseModel):
    sentence: str
    model: str = "kokoro-82M"  # "tts_models/en/ljspeech/fast_pitch"
    vocoder: str = "vocoder_models/en/ljspeech/hifigan_v2"
    language: str = "en"


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


@app.post("/stt")
async def create_upload_file(file: UploadFile, language: str = ""):
    temp_file = f"/app/tts/input/input_{ObjectId()}_{file.filename}"

    async with aiofiles.open(temp_file, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    language_code = stt_language.get(language) if language else None
    result = STT_MODEL.transcribe(temp_file, language=language_code)

    if not debug:
        os.remove(temp_file)
    return {"result": result["text"]}


@app.post("/transcribe")
async def transcribe_file(file: UploadFile, language: str = ""):
    temp_file = f"/app/tts/input/input_{ObjectId()}_{file.filename}"

    async with aiofiles.open(temp_file, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    language_code = stt_language.get(language) if language else None
    result = STT_MODEL.transcribe(temp_file, language=language_code, task='translate')

    if not debug:
        os.remove(temp_file)
    return {"result": result["text"]}


@app.post("/tts")
def readPost(query: TTSRequest):
    """
    Process the given input into audio convert in mp3 and returns it as a file.
    """
    output_wav = f"/app/tts/output/output_{ObjectId()}.wav"
    sentence = clean_input(query.sentence)
    language = 'en'
    if hasattr(query, 'language'):
        language = query.language
    log.debug(f"Requested to voice: `{sentence}`")

    if query.model != "kokoro-82M":
        log.error(f"only kokoro TTS engine is supported")
        if query.language != 'en':
            raise HTTPException(status_code=400, detail="Only kokoro TTS engine is supported.")

    text_to_audio(text=sentence, file_path=output_wav, language=language)
    output_mp3 = convert_to_mp3(output_wav)

    return FileResponse(output_mp3, media_type="audio/mpeg")


@app.get("/tts")
def readGet(query: TTSRequest):
    """
    Process the given input into audio convert in mp3 and returns it as a file.
    """
    return readPost(query)


@app.get("/models")
def read_item():
    """
    List the currently available models.
    """
    return [{"hexgrad/Kokoro-82M": True}]


@app.post("/subtitles")
async def get_subtitles(file: UploadFile, language: str = ""):
    temp_file = f"/app/tts/input/input_{ObjectId()}_{file.filename}"

    async with aiofiles.open(temp_file, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    audio = whisper_timestamped.load_audio(temp_file)
    model = whisper_timestamped.load_model("openai/whisper-large-v2", device="cuda")
    result = whisper_timestamped.transcribe(model, audio, language="fr")
    log.info(result)
    subtitles_file = f"/tts/output/subtitles_{ObjectId()}_{file.filename}.srt"

    segments = result["segments"]
    with open(subtitles_file, "w", encoding="utf-8") as f:
        write_srt(segments, file=f)

    return FileResponse(subtitles_file, media_type="text")
