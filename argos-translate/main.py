import logging
import os
import sys
import torch
from bson import ObjectId

import argostranslate.package
import argostranslate.translate
from fastapi import FastAPI
from fastapi.responses import FileResponse

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
log = logging.getLogger(__name__)

debug = os.getenv('DEBUG', '').lower() in ['1', 'true']

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:9000",
    "https://ai.shanghai.laurent.erignoux.fr:9000",
]
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
