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
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_mistralai import ChatMistralAI
from pydantic import BaseModel, Field
from typing import Optional

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


class Story(BaseModel):
    subject: str=""
    model: str=""
    stream: bool=False
    chapter_count: int=3


def read_secret(name):
    with open(f"/run/secrets/{name}") as f:
        return f.read().strip()


MODELS_FOLDER = "/root/.local/share/tts"
DEFAULT_MODEL = "tts_models/en/ljspeech/fast_pitch"
BASE_URL = "http://ollama:11434"
#current_model="phi"
current_model="llama"

llm = Ollama(model=current_model, base_url=BASE_URL)

ollama = ChatOllama(model="llama3.1", base_url=BASE_URL, temperature=0)
mistral = ChatMistralAI(api_key=read_secret("mistral_api_key"), model="mistral-large-latest")

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


@app.post("/ollama/chat")
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


@app.post("/ollama/story")
def read(story: Story):
    """
    """
    global mistral
    global ollama

    model = ollama
    if story.model == 'mistral':
        model = mistral

    story_schema = {
        "title": "story",
        "description": f"A kid story about {story.subject}",
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "The title of the story.",
            },
        },
        "required": ["title"],
    }


    for chapter_index in range(story.chapter_count):
        chapter_name = f"chapter {chapter_index}"
        chapter_description = f"The {chapter_index} chapter"
        story_schema['required'] += [chapter_name]
        story_schema[chapter_name] = {
            "type": "string",
            "description": chapter_description
        }

    structured_llm = model.with_structured_output(schema=story_schema)
    response = structured_llm.invoke(f"Please write a kid story in {story.chapter_count} short chapters of a few sentences each about {story.subject}")
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
