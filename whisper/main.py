import aiofiles
import logging
import os
import sys
from typing import Union, Annotated

from bson import ObjectId
from fastapi import FastAPI, File, UploadFile
import whisper

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
log = logging.getLogger(__name__)

app = FastAPI()

# FIXME Need to check the quality/speed we want.
DEFAULT_MODEL = "small"
STT_MODEL = whisper.load_model(DEFAULT_MODEL)
"""
@app.post("/")
def transcribe(file: UploadFile):
    if model != DEFAULT_MODEL:
        raise Exception("Custom models not supported")
    result = STT_MODEL.transcribe(file.file)
    log.debug(f"transcription result: {result['text']}")
    return {"result": result["text"]}

@app.post("/files/")
async def create_file(file: Annotated[bytes, File()]):
    return {"file_size": len(file)}
"""


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    temp_file = f"/stt/output/output_{ObjectId()}_{file.filename}"

    async with aiofiles.open(temp_file, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    result = STT_MODEL.transcribe(temp_file)
    os.remove(temp_file)
    return {"result": result["text"]}