import asyncio
import logging
import os
import requests
import sys
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from langchain_ollama import ChatOllama
from langchain_mistralai import ChatMistralAI
from pydantic import BaseModel
from typing import Dict


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

current_model="llama3.2"
llm_handler = ChatOllama(model=current_model, base_url=BASE_URL, temperature=0, timeout=300)

custom_llm_handlers = {
    'mistral-large-latest': ChatMistralAI(api_key=read_secret("mistral_api_key"), model="mistral-large-latest")
}

def get_default_llm_handler(model):
    global current_model
    global llm_handler
    if model != current_model:
        llm_handler = ChatOllama(model="llama3.2", base_url=BASE_URL, temperature=0, timeout=300)
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


# Store for ongoing story generations
active_stories: Dict[str, dict] = {}

@app.post("/ollama/story")
async def start_story(story: Story):
    """
    Start a story generation process and return a story ID for WebSocket connection
    """
    story_id = str(uuid.uuid4())
    active_stories[story_id] = {
        "status": "initializing",
        "model": story.model,
        "subject": story.subject,
        "chapter_count": story.chapter_count,
        "current_chapter": 0,
        "chapters": {},
        "title": None,
        "summary": None
    }

    # Start the story generation process
    asyncio.create_task(generate_story(story_id, story))

    return {"story_id": story_id}


async def generate_story(story_id: str, story: Story):
    """
    Generate the story in the background and update the story state
    """
    try:
        llm = custom_llm_handlers.get(story.model, get_default_llm_handler(story.model))

        # First pass: Generate story structure
        story_schema = {
            "title": "story",
            "description": f"A kid story about {story.subject}",
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "The title of the story.",
                },
                "summary": {
                    "type": "string",
                    "description": "A brief summary of the story's plot and main events.",
                }
            },
            "required": ["title", "summary"],
        }

        # Add chapter properties to schema
        for chapter_index in range(story.chapter_count):
            chapter_name = f"chapter_{chapter_index}"
            story_schema["properties"][chapter_name] = {
                "type": "string",
                "description": f"The content of chapter {chapter_index + 1}"
            }
            story_schema["required"].append(chapter_name)

        structured_llm = llm.with_structured_output(schema=story_schema)
        initial_story = await structured_llm.ainvoke(
            f"""Please write a kid story in {story.chapter_count} chapters about {story.subject}.
            First, create a title and a brief summary of the story.
            Then, write each chapter with a few sentences that outline the main events.
            Make sure the story has a clear beginning, middle, and end."""
        )

        # Update story state with initial structure
        active_stories[story_id].update({
            "title": initial_story["title"],
            "summary": initial_story["summary"],
            "status": "generating_chapters"
        })

        # Second pass: Polish each chapter
        for chapter_index in range(story.chapter_count):
            log.info(f"Polishing chapter {chapter_index} of {story.chapter_count}")
            chapter_name = f"chapter_{chapter_index}"
            chapter_content = initial_story[chapter_name]

            # Create a prompt for polishing the chapter
            polish_prompt = f"""Please polish and expand this chapter of a children's story to make it more engaging and detailed.
            Keep the same main events but add more descriptive language, dialogue, and emotional depth.
            Make it suitable for children while being interesting and educational.

            Chapter {chapter_index + 1} of "{initial_story['title']}":
            {chapter_content}

            Story summary for context:
            {initial_story['summary']}
            """

            # Get the polished version
            polished_chapter = await llm.ainvoke(polish_prompt)
            active_stories[story_id]["chapters"][f"chapter {chapter_index}"] = polished_chapter.content
            active_stories[story_id]["current_chapter"] = chapter_index + 1

        # Mark story as complete
        active_stories[story_id]["status"] = "complete"

    except Exception as e:
        active_stories[story_id]["status"] = "error"
        active_stories[story_id]["error"] = str(e)

@app.websocket("/ollama/ws/story/{story_id}")
async def websocket_endpoint(websocket: WebSocket, story_id: str):
    """
    WebSocket endpoint for story generation progress
    """
    await websocket.accept()
    last_chapter = None
    last_status = None
    try:
        while True:
            if story_id not in active_stories:
                await websocket.send_json({"status": "error", "message": "Story not found"})
                break

            story_state = active_stories[story_id]

            if last_status is None or last_status != story_state["status"]:
                await websocket.send_json(story_state)
                last_status = story_state["status"]
                last_chapter = story_state.get("current_chapter")
            elif story_state["status"] == "generating_chapters":
                if last_chapter is None or last_chapter != story_state["current_chapter"]:
                    log.info(f"Sending story state {story_state}")
                    await websocket.send_json(story_state)
                    last_chapter = story_state["current_chapter"]

            if story_state["status"] in ["complete", "error"]:
                break

            await asyncio.sleep(1)  # Poll every second

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"status": "error", "message": str(e)})


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
