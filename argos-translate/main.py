import aiofiles
import logging
import os
import requests
import sys
import torch
from bson import ObjectId

import argostranslate.package
import argostranslate.translate
from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

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

argostranslate.package.update_package_index()
available_packages = argostranslate.package.get_available_packages()
languages = os.getenv('ARGOS_LANGUAGES', "").split(',')

log.info(f"Loading translation packages for {languages}.")
for from_code in languages:
    for to_code in languages:
        if from_code == to_code:
            continue
        try:
            log.info(f"installing translation {from_code}->{to_code}")
            package_to_install = next(
                filter(
                    lambda x: x.from_code == from_code and x.to_code == to_code, available_packages
                )
            )
            argostranslate.package.install_from_path(package_to_install.download())
        except StopIteration:
            log.error(f"Could not install translation {from_code}->{to_code}, skipping.")


@app.post("/translate")
def translate(sentence: str, from_code='en', to_code='fr'):
    """
    Process the given input into audio convert in mp3 and returns it as a file.
    """
    translatedText = argostranslate.translate.translate(sentence, from_code, to_code)
    return {"result": translatedText}


@app.post("/translate_audio")
async def translate_audio(file: UploadFile, from_code='en', to_code='fr'):
    temp_file = f"/argos-translate/input/input_{ObjectId()}_{file.filename}"
    """
    Process the given input into audio convert in mp3 and returns it as a file.
    """
    async with aiofiles.open(temp_file, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    multipart_form_data = {
        'file': content,
        'language': from_code
    }
    response = requests.post("http://192.168.2.10:8186/stt", files=multipart_form_data)
    data = response.json()
    translatedText = argostranslate.translate.translate(data.get('result'), from_code, to_code)


    post_data = {
        'sentence': translatedText,
        'model': 'kokoro-82M',
        'language': to_code
    }
    response = requests.post("http://192.168.2.10:8186/tts", json=post_data)
    if response.status_code == 200:
        temp_file = f"/argos-translate/output/output_{ObjectId()}_{file.filename}"
        with open(temp_file, 'wb') as f:
            f.write(response.content)
    else:
        raise Exception(f"Failed translating audio file tts response {response.status_code}")
    return FileResponse(temp_file, media_type="audio/mpeg")
