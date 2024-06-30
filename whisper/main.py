import aiofiles
import logging
import os
import sys
from typing import Union, Annotated

from bson import ObjectId
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import whisper

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
log = logging.getLogger(__name__)


debug = os.getenv('DEBUG', '').lower() in ['1', 'true']


app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:5176",
    "https://ai.shanghai.laurent.erignoux.fr:5176",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# FIXME Need to check the quality/speed we want.
DEFAULT_MODEL = "small"
STT_MODEL = whisper.load_model(DEFAULT_MODEL).to("cuda")


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    temp_file = f"/stt/input/input_{ObjectId()}_{file.filename}"

    async with aiofiles.open(temp_file, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    result = STT_MODEL.transcribe(temp_file)

    if not debug:
        os.remove(temp_file)
    return {"result": result["text"]}
