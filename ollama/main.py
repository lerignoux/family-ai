import logging
import os
import requests
from typing import Union
import subprocess
import sys
from bson import ObjectId

from fastapi import FastAPI, File
from fastapi.middleware.cors import CORSMiddleware
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_mistralai import ChatMistralAI
from pydantic import BaseModel, Field
from typing import Optional

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
log = logging.getLogger(__name__)

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


BASE_URL = "http://ollama:11434"
current_model="llama3.1"
llm_handler = ChatOllama(model=current_model, base_url=BASE_URL, temperature=0)

custom_llm_handlers = {
    'mistral-large-latest': ChatMistralAI(api_key=read_secret("mistral_api_key"), model="mistral-large-latest")
}

def get_default_llm_handler(model):
    global current_model
    global llm_handler
    if model != current_model:
        llm_handler = ChatOllama(model="llama3.1", base_url=BASE_URL, temperature=0)
    return llm_handler


@app.post("/ollama/chat")
def chat(chat: Chat):
    """
    Request the ai model to answer to a user query.
    """
    llm = custom_llm_handlers.get(chat.model, get_default_llm_handler(chat.model))

    messages = [
        (
            "system",
            "You are a helpful assistant trying to politely answer and help the user as much as possible. Answer to the user request in a concise manner.",
        ),
        ("human", chat.prompt),
    ]

    response = llm.invoke(messages)

    return {"response": response.content}


@app.post("/ollama/story")
def story(story: Story):
    """
    Request generating a kid story.
    """
    global current_model
    global llm

    llm = custom_llm_handlers.get(story.model, get_default_llm_handler(story.model))

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

    structured_llm = llm.with_structured_output(schema=story_schema)
    response = structured_llm.invoke(f"Please write a kid story in {story.chapter_count} short chapters of a few sentences each about {story.subject}")
    return {"response": response}


@app.get("/ollama/models")
def models():
    """
    List the currently available models on the llm.
    """
    model_list = [
            {'name': "Mistral Lage", 'value': 'mistral-large-latest', "description":"European Mistral model, non free.", 'type': 'api'}
    ]

    response = requests.get(f"{BASE_URL}/api/tags")
    model_data = response.json()
    for model in model_data.get('models', []):
        model_name = model['name']
        try:
          model_name = model['name'].split(':')[0]
        except KeyError:
            pass
        model_name = model_name.replace('-', ' ' ).title()
        model_list.append({
            'name': model_name,
            'value': model['model'],
            'description': f"{model['model']} \"open source\" model hosted locally.",
            'type': 'local',
        })

    return model_list
