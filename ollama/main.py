import logging
import os
import requests
from typing import Union
import subprocess
import sys
from bson import ObjectId

from fastapi import FastAPI, File
from fastapi.middleware.cors import CORSMiddleware
from langchain_community.llms import Ollama
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
log = logging.getLogger(__name__)

app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:9000",
    "https://ai.shanghai.laurent.erignoux.fr:9443",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Chat(BaseModel):
    prompt: str
    model: str
    stream: bool


MODELS_FOLDER = "/root/.local/share/tts"
DEFAULT_MODEL = "tts_models/en/ljspeech/fast_pitch"
BASE_URL = "http://ollama:11434"
current_model="phi"

llm = Ollama(model=current_model, base_url=BASE_URL)

template = """
You are a helpful and friendly AI assistant. You are polite, respectful, and aim to provide concise responses of less
than 20 words.

The conversation transcript is as follows:
{history}

And here is the user's follow-up: {input}

Your response:
"""

prompt_template = PromptTemplate(input_variables=["history", "input"], template=template)
chain = ConversationChain(
    prompt=prompt_template,
    verbose=False,
    memory=ConversationBufferMemory(ai_prefix="Assistant:"),
    llm=Ollama(),
)

def get_llm_response(text: str) -> str:
    """
    Generates a response to the given text using the Llama-2 language model.

    Args:
        text (str): The input text to be processed.

    Returns:
        str: The generated response.
    """
    response = chain.predict(input=text)
    if response.startswith("Assistant:"):
        response = response[len("Assistant:") :].strip()
    return response


@app.post("/ollama")
def read(chat: Chat):
    """
    Process the given input into audio convert in mp3 and returns it as a file.
    """
    global current_model
    global llm

    if chat.model != current_model:
        current_model = chat.model
        llm = Ollama(model=current_model, base_url=BASE_URL)

    response = llm(chat.prompt)

    return {"response": response}


@app.get("/models")
@app.get("/ollama/models")
def read_item():
    """
    List the currently available models on the llm.
    """
    response = requests.get(f"{BASE_URL}/api/tags")
    model_data = response.json()
    model_list = [model['model'] for model in model_data.get('models', [])]
    return model_list
