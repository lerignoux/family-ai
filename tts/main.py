import asyncio
import logging
import os
import subprocess
import sys
from time import sleep
from typing import Annotated, Union
import uuid

import aiofiles
import requests
import whisper
import whisper_timestamped
from bson import ObjectId
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from kokoro_tts import text_to_audio
from pydantic import BaseModel
from whisper_timestamped.make_subtitles import write_srt

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
log = logging.getLogger(__name__)

debug = os.getenv("DEBUG", "").lower() in ["1", "true"]

app = FastAPI()

tasks = {}

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


def burn_subtitles(video_file, subtitles_file, output_video_file):
    command = f"ffmpeg -i {video_file} -vf subtitles={subtitles_file} -map 0:v -map 0:a -c:a copy {output_video_file}"
    log.info(f"Executing `{command}`")
    try:
        subprocess.run(command.split(" "), check=True)
        log.debug("FFmpeg subtitles burning executed successfully.")
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error burning subtitles in input video: {e}")
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

def _run_subtitling_sync(
    task_id: str,
    temp_file: str,
    language: str,
    integration: str,
    extension: str,
) -> None:
    """Sync CPU-bound work (Whisper, FFmpeg) - runs in thread to keep event loop responsive."""
    filename_base = os.path.splitext(os.path.basename(temp_file))[0]
    output_video_file = f"/app/tts/output/{filename_base}{extension}"
    subtitles_file_en = f"/app/tts/output/{filename_base}.en.srt"
    subtitles_file = f"/app/tts/output/{filename_base}.{language}.srt"

    # 1. Whisper Transcription (Heavy CUDA Task)
    audio = whisper_timestamped.load_audio(temp_file)
    model = whisper_timestamped.load_model("openai/whisper-large-v2", device="cuda")
    result = whisper_timestamped.transcribe(model, audio, task="translate")

    with open(subtitles_file_en, "w", encoding="utf-8") as f:
        write_srt(result["segments"], file=f)

    # 2. Translation logic (Argos)
    target_file = subtitles_file_en
    if language != "en":
        with open(subtitles_file_en, "rb") as f:
            response = requests.post(
                "http://argos-translate/translate_subtitles",
                files={"file": f},
                timeout=60,
            )
        if response.status_code == 200:
            with open(subtitles_file, "wb") as f:
                f.write(response.content)
            target_file = subtitles_file
        else:
            raise Exception("Translation failed")

    # 3. Integration logic (Embed/Burn)
    final_path = target_file
    if integration and extension in videos_types:
        if integration == "embed":
            final_path = embed_subtitles(temp_file, target_file, output_video_file)
        elif integration == "burn":
            final_path = burn_subtitles(temp_file, target_file, output_video_file)

    tasks[task_id] = {"status": "completed", "file_path": final_path}


async def process_subtitling_task(
    task_id: str,
    temp_file: str,
    language: str,
    integration: str,
    extension: str,
) -> None:
    """Run heavy processing in thread so WebSocket can send updates (mirrors story-teller)."""
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(
            None,
            lambda: _run_subtitling_sync(
                task_id, temp_file, language, integration, extension
            ),
        )
    except Exception as e:
        log.error(f"Task {task_id} failed: {str(e)}")
        tasks[task_id] = {"status": "failed", "error": str(e)}

@app.post("/stt/subtitles")
async def get_subtitles(background_tasks: BackgroundTasks, file: UploadFile, language: str = 'en', integration: str = None):
    task_id = str(uuid.uuid4())
    _, extension = os.path.splitext(file.filename)
    temp_file = f"/app/tts/input/{task_id}_{file.filename}"

    async with aiofiles.open(temp_file, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    tasks[task_id] = {"status": "processing"}
    background_tasks.add_task(process_subtitling_task, task_id, temp_file, language, integration, extension)
    return {"task_id": task_id, "status": "accepted"}

@app.get("/stt/status/{task_id}")
async def check_status(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task["status"] == "completed":
        # Return the file once processing is finished
        return FileResponse(task["file_path"])

    return task


@app.websocket("/stt/ws/{task_id}")
async def subtitles_websocket(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint to wait for subtitle task completion.
    sends status updates until complete or error.
    """
    await websocket.accept()
    last_status = None

    try:
        while True:
            if task_id not in tasks:
                await websocket.send_json(
                    {"status": "error", "message": "Task not found"}
                )
                break

            task = tasks[task_id]
            status = task["status"]

            # Send update when status changes
            if last_status is None or last_status != status:
                if status == "completed":
                    await websocket.send_json({"status": "complete"})
                elif status == "failed":
                    await websocket.send_json(
                        {
                            "status": "error",
                            "error": task.get("error", "Unknown error"),
                        }
                    )
                else:
                    await websocket.send_json(
                        {"status": status, "message": "Processing..."}
                    )
                last_status = status

            if status in ["completed", "failed"]:
                break

            await asyncio.sleep(1)
    except WebSocketDisconnect:
        log.debug(f"WebSocket disconnected for task {task_id}")
    except Exception as e:
        log.exception(f"WebSocket error for task {task_id}")
        await websocket.send_json({"status": "error", "message": str(e)})
