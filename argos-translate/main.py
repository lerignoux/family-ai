import base64
import json
import logging
import os
import sys
from pathlib import Path

import aiofiles
import argostranslate.package
import argostranslate.translate
import requests
import srt
from bson import ObjectId
from fastapi import FastAPI, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

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

argostranslate.package.update_package_index()
available_packages = argostranslate.package.get_available_packages()
languages = os.getenv("ARGOS_LANGUAGES", "").split(",")

log.info(f"Loading translation packages for {languages}.")
for from_code in languages:
    for to_code in languages:
        if from_code == to_code:
            continue
        try:
            log.info(f"installing translation {from_code}->{to_code}")
            package_to_install = next(
                filter(
                    lambda x: x.from_code == from_code and x.to_code == to_code,
                    available_packages,
                )
            )
            argostranslate.package.install_from_path(package_to_install.download())
        except StopIteration:
            log.error(
                f"Could not install translation {from_code}->{to_code}, skipping."
            )


output_directory = Path("/argos-translate/output")
output_directory.mkdir(parents=True, exist_ok=True)
input_directory = Path("/argos-translate/output")
input_directory.mkdir(parents=True, exist_ok=True)

# Create the directory and any necessary parent directories
# exist_ok=True prevents an error if the directory already exists
# parents=True creates any missing parent directories


@app.post("/translate")
def translate(sentence: str, from_code="en", to_code="fr"):
    """
    Process the given input into audio convert in mp3 and returns it as a file.
    """
    translatedText = argostranslate.translate.translate(sentence, from_code, to_code)
    return {"result": translatedText}


@app.post("/translate_subtitles")
async def translate_subtitles(file: UploadFile, from_code="en", to_code="fr"):
    """
    Process the given input subtitles file into the given language.
    """
    str_content = await file.read()
    log.info(str_content)
    subtitle_generator = srt.parse(str_content.decode("utf-8"))
    subtitles_data = list(subtitle_generator)
    for sub in subtitles_data:
        sub.content = argostranslate.translate.translate(
            sub.content, from_code, to_code
        )
        log.info(f"Translated sub: {sub.content}")

    temp_file = f"/argos-translate/output/output_{ObjectId()}_{file.filename}"
    with open(temp_file, "wb") as f:
        f.write(srt.compose(subtitles_data).encode("utf-8"))

    return FileResponse(temp_file, media_type="text")


@app.websocket("/translate_text_stream")
async def translate_text_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time text translation streaming with progress updates.
    Skips the speech-to-text step and starts directly with translation.
    """
    await websocket.accept()

    try:
        # Extract query parameters from the WebSocket URL
        query_params = websocket.query_params
        from_code = query_params.get("from_code", "en")
        to_code = query_params.get("to_code", "fr")

        log.info(
            f"WebSocket connection established for text translation {from_code}->{to_code}"
        )

        # Send initial progress
        await websocket.send_text(
            json.dumps(
                {
                    "type": "translation",
                    "message": "Starting translation...",
                    "progress": 0,
                }
            )
        )

        # Wait for text input from client
        text_input = await websocket.receive_text()
        log.info(f"Received text input: {text_input}")

        if not text_input:
            await websocket.send_text(
                json.dumps({"type": "error", "message": "No text received"})
            )
            return

        # Step 1: Translation
        try:
            translated_text = argostranslate.translate.translate(
                text_input, from_code, to_code
            )
            log.info(f"Translated text: {translated_text}")

            # Send progress update
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "translation",
                        "translatedText": translated_text,
                        "message": f"Translated: {translated_text}",
                        "progress": 50,
                    }
                )
            )

        except Exception as e:
            log.error(f"Translation error: {e}")
            await websocket.send_text(
                json.dumps(
                    {"type": "error", "message": f"Translation failed: {str(e)}"}
                )
            )
            return

        # Step 2: Text to Speech
        try:
            post_data = {
                "sentence": translated_text,
                "model": "kokoro-82M",
                "language": to_code,
            }
            response = requests.post("http://tts/tts", json=post_data)

            if response.status_code != 200:
                raise Exception(f"TTS failed with status {response.status_code}")

            # Convert audio to base64 for WebSocket transmission
            audio_base64 = base64.b64encode(response.content).decode("utf-8")

            # Send completion with base64 audio
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "complete",
                        "message": "Translation completed successfully",
                        "progress": 100,
                        "data": audio_base64,
                    }
                )
            )

            log.info("WebSocket text translation completed successfully")

        except Exception as e:
            log.error(f"Text-to-speech error: {e}")
            await websocket.send_text(
                json.dumps(
                    {"type": "error", "message": f"Text-to-speech failed: {str(e)}"}
                )
            )
            return

    except WebSocketDisconnect:
        log.info("WebSocket client disconnected")
    except Exception as e:
        log.error(f"WebSocket text translation error: {str(e)}")
        try:
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "error",
                        "message": f"Translation failed: {str(e)}",
                        "progress": 0,
                    }
                )
            )
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


@app.post("/translate_audio")
async def translate_audio(file: UploadFile, from_code="en", to_code="fr"):
    temp_file = f"/argos-translate/input/input_{ObjectId()}_{file.filename}"
    """
    Process the given input into audio convert in mp3 and returns it as a file.
    """
    async with aiofiles.open(temp_file, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    multipart_form_data = {"file": content, "language": from_code}
    response = requests.post("http://192.168.2.10:8186/stt", files=multipart_form_data)
    data = response.json()
    translatedText = argostranslate.translate.translate(
        data.get("result"), from_code, to_code
    )

    post_data = {"sentence": translatedText, "model": "kokoro-82M", "language": to_code}
    response = requests.post("http://tts/tts", json=post_data)
    if response.status_code == 200:
        temp_file = f"/argos-translate/output/output_{ObjectId()}_{file.filename}"
        with open(temp_file, "wb") as f:
            f.write(response.content)
    else:
        raise Exception(
            f"Failed translating audio file tts response {response.status_code}"
        )
    return FileResponse(temp_file, media_type="audio/mpeg")


@app.websocket("/translate_audio_stream")
async def translate_audio_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time translation streaming with progress updates.
    """
    await websocket.accept()

    try:
        # Extract query parameters from the WebSocket URL
        query_params = websocket.query_params
        from_code = query_params.get("from_code", "en")
        to_code = query_params.get("to_code", "fr")
        audio_type = query_params.get("type", "ogg")

        log.info(
            f"WebSocket connection established for translation {from_code}->{to_code}"
        )

        # Wait for audio blob from client
        audio_blob = await websocket.receive_bytes()
        log.info(f"Received audio blob of size: {len(audio_blob)} bytes")

        # Save audio to temporary file for STT processing
        temp_file = (
            f"/app/argos-translate/input/input_{ObjectId()}_websocket.{audio_type}"
        )
        with open(temp_file, "wb") as f:
            f.write(audio_blob)

        # Speech to Text
        multipart_form_data = {"file": audio_blob, "language": from_code}
        response = requests.post("http://tts/stt", files=multipart_form_data)

        if response.status_code != 200:
            raise Exception(f"STT failed with status {response.status_code}")

        data = response.json()
        transcribed_text = data.get("result", "")
        log.info(f"Transcribed text: {transcribed_text}")
        # Send speech-to-text progress
        await websocket.send_text(
            json.dumps(
                {
                    "type": "speech_to_text",
                    "transcribedText": transcribed_text,
                    "message": f"Transcribed: {transcribed_text}",
                    "progress": 33,
                }
            )
        )

        # Translate text
        translated_text = argostranslate.translate.translate(
            transcribed_text, from_code, to_code
        )
        log.info(f"Translated text: {translated_text}")
        # Send translation progress
        await websocket.send_text(
            json.dumps(
                {
                    "type": "translation",
                    "translatedText": translated_text,
                    "message": f"Translating from {from_code} to {to_code}...",
                    "progress": 66,
                }
            )
        )

        # Text to Speech
        post_data = {
            "sentence": translated_text,
            "model": "kokoro-82M",
            "language": to_code,
        }
        response = requests.post("http://tts/tts", json=post_data)

        if response.status_code != 200:
            raise Exception(f"TTS failed with status {response.status_code}")

        # Convert audio to base64 for WebSocket transmission
        audio_base64 = base64.b64encode(response.content).decode("utf-8")

        # Send completion with base64 audio
        await websocket.send_text(
            json.dumps(
                {
                    "type": "complete",
                    "message": "Translation completed successfully",
                    "progress": 100,
                    "data": audio_base64,
                }
            )
        )

        log.info("WebSocket translation completed successfully")

        # Clean up temporary file
        if not debug:
            try:
                os.remove(temp_file)
            except:
                pass

    except WebSocketDisconnect:
        log.info("WebSocket client disconnected")
    except Exception as e:
        log.error(f"WebSocket translation error: {str(e)}")
        try:
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "error",
                        "message": f"Translation failed: {str(e)}",
                        "progress": 0,
                    }
                )
            )
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
