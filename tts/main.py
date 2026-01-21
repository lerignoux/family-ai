import logging
import os
import subprocess
import sys
from time import sleep
from typing import Annotated, Union

import aiofiles
import requests
import whisper
import whisper_timestamped
from bson import ObjectId
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from kokoro_tts import text_to_audio
from pydantic import BaseModel
from whisper_timestamped.make_subtitles import write_srt

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
log = logging.getLogger(__name__)

debug = os.getenv("DEBUG", "").lower() in ["1", "true"]

app = FastAPI()

origins = ["http://localhost", "http://localhost:9000", "https://localhost"]
if "HOST" in os.environ:
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
    "en": "English",
    "es": "Espanol",
    "fr": "French",
    "zh": "Chinese",
    "jp": "Janaese",
}

videos_types = {
    ".flv": {"mime": "video/x-flv"},
    ".mp4": {"mime": "video/mp4"},
    ".3gp": {"mime": "video/3gpp"},
    ".mov": {"mime": "video/quicktime"},
    ".avi": {"mime": "video/x-msvideo"},
    ".wmv": {"mime": "video/x-ms-wmv"},
    ".ogg": {"mime": "video/ogg"},
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
    command = (
        f"ffmpeg -hwaccel cuda -y -i {filename} -vn -ar 44100 -ac 2 -b:a 192k {output}"
    )
    log.info(f"Executing `{command}`")
    try:
        process = subprocess.Popen(command.split(" "))
        process.wait()
        if delete:
            os.remove(filename)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error converting audio to mp3: {e}")
    return output


def clean_input(sentence):
    return sentence.replace('"', "").replace("'", "").replace("\n", "")


subtitles_ids = {".en": "eng", ".fr": "fra", ".zh": "chi", ".sp": "spa"}


def get_subtitles_language(subtitles_file):
    ext = os.path.splitext(os.path.splitext(subtitles_file)[0])[1]
    return subtitles_ids.get(ext)


def embed_subtitles(video_file, subtitles_file, output_video_file):
    subtitle_options = f"-map 1:s"
    lang = get_subtitles_language(subtitles_file)
    if lang:
        subtitle_options += f" -metadata:s:s:0 language={lang}"
    command = f"ffmpeg -i {video_file} -i {subtitles_file} -map 0:v -map 0:a -c:v copy -c:a copy -c:s mov_text {subtitle_options} {output_video_file}"
    log.info(f"Executing `{command}`")
    try:
        subprocess.run(command.split(" "), check=True)
        log.debug("FFmpeg subtitles integration executed successfully.")
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error embedding subtitles in input video: {e}")
    return output_video_file


@app.post("/stt")
async def create_upload_file(file: UploadFile, language: str = ""):
    temp_file = f"/app/tts/input/input_{ObjectId()}_{file.filename}"

    async with aiofiles.open(temp_file, "wb") as out_file:
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

    async with aiofiles.open(temp_file, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    language_code = stt_language.get(language) if language else None
    result = STT_MODEL.transcribe(temp_file, language=language_code, task="translate")

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
    language = "en"
    if hasattr(query, "language"):
        language = query.language
    log.debug(f"Requested to voice: `{sentence}`")

    if query.model != "kokoro-82M":
        log.error(f"only kokoro TTS engine is supported")
        if query.language != "en":
            raise HTTPException(
                status_code=400, detail="Only kokoro TTS engine is supported."
            )

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


@app.post("/stt/subtitles")
async def get_subtitles(file: UploadFile, language: str | None = None, embed: bool = True):
    log.info(f"Requested subtitles in {language}.")
    filename, extension = os.path.splitext(file.filename)
    full_filename = f"{ObjectId()}_{filename}"
    temp_file = f"/app/tts/input/{full_filename}{extension}"
    output_video_file = f"/app/tts/output/{full_filename}{extension}"
    subtitles_file_en = f"/app/tts/output/{full_filename}.en.srt"
    subtitles_file = f"/app/tts/output/{full_filename}.{language}.srt"

    async with aiofiles.open(temp_file, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    audio = whisper_timestamped.load_audio(temp_file)
    model = whisper_timestamped.load_model("openai/whisper-large-v2", device="cuda")
    result = whisper_timestamped.transcribe(
        model, audio, task="translate"
    )

    segments = result["segments"]
    with open(subtitles_file_en, "w", encoding="utf-8") as f:
        write_srt(segments, file=f)

    if language != 'en':
        with open(subtitles_file_en, "rb") as f:
            files = {"file": f}
            response = requests.post(
                "http://argos-translate/translate_subtitles", files=files
            )
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed translating subtitles.")

        with open(subtitles_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    if embed and extension in videos_types.keys():
        subtitled_file = embed_subtitles(temp_file, subtitles_file, output_video_file)
        return FileResponse(subtitled_file)
    else:
        return FileResponse(subtitles_file, media_type="text")
