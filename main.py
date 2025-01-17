# https://docs.anthropic.com/en/docs/build-with-claude/tool-use
# TODO: add support for when tools fail
# TODO: ask what to improve
# TODO: add geocoding tool, tell to store geocode user's location and store in memory
# TODO: add tool result cache
# TODO: customize UI
# TODO: host in spaces
# TODO: add examples
# TODO: add multimodality
# TODO: gr.Image, gr.Video, gr.Audio, gr.File, gr.HTML, gr.Gallery, gr.Plot, gr.Map
# TODO: improve system prompt, make LLM use more markdown formatting and emojis
# TODO: https://www.gradio.app/guides/plot-component-for-maps
# TODO: trim down data from search results
# TODO: bug follow up user messages not recorded in history
# TODO: not all memories are being saved

from dotenv import load_dotenv
load_dotenv()

import time
import json
import anthropic
import gradio as gr
from gradio import ChatMessage

from tools import TOOLS_SPECS, TOOLS_FUNCTIONS

MODEL_ID = "claude-3-5-sonnet-20241022"
MAX_TOKENS = 1024

system_memory = []
APP_CONTEXT = {
    "system_memory" : system_memory,
    "system_memory_max_size" : 5
}

def load_system_prompt():
    with open('prompts/system.txt', 'r') as f:
        return f.read().strip()

client = anthropic.Anthropic()

# TODO: this is a hack, if I don't fix this, multiple chats won't be supported
claude_history = []

def get_memory_string():
    return "\n".join([f"{index}: {value}" for index, value in enumerate(list(system_memory))]).strip()

def get_memory_markdown():
    return "\n".join([f"{index}. {value}" for index, value in enumerate(list(system_memory))]).strip()

def prompt_claude():
    # Build the system prompt including all memories the user asked to remember
    system_prompt_memory_str = get_memory_string()
    system_prompt_text = load_system_prompt()
    if system_prompt_memory_str: system_prompt_text += f"\n\nHere are the memories the user asked you to remember:\n{system_prompt_memory_str}"
    
    # Send message to Claude
    message = client.messages.create(
        model=MODEL_ID,
        max_tokens=MAX_TOKENS,
        temperature=0.0, 
        tools=TOOLS_SPECS.values(),
        system=[{
            "type": "text", 
            "text": system_prompt_text, 
            "cache_control": {"type": "ephemeral"} # Prompt caching references the entire prompt - tools, system, and messages (in that order) up to and including the block designated with cache_control.
        }],
        messages=claude_history
    )
    return message

def chatbot(message, history):
    # Store in claude history
    claude_history.append({
        "role": "user",
        "content": message
    })

    done = False
    while not done:
        done = True
        claude_response = prompt_claude()
        for content in claude_response.content:
            if content.type == "text":
                # Show message in GUI
                _message = {
                    "role": "assistant",
                    "content": content.text
                }
                history.append(
                    ChatMessage(
                        role=_message["role"],
                        content=_message["content"]
                    )
                )
                yield history, get_memory_markdown()
                
                # Store in claude history
                claude_history.append({**_message})
            elif content.type == "tool_use":
                tool_id = content.id
                tool_name = content.name
                tool_input = content.input

                # Say that we're calling the tool
                start_time = time.time() # TODO: add timer
                response = ChatMessage(
                    content="Processing...",
                    metadata={"title": f"🛠️ Using tool `{tool_name}`", "id": 0, "status": "pending"} # TODO: id for what?
                )
                history.append(response)
                yield history, get_memory_markdown()

                # Call the tool
                print(f"Calling {tool_name}({json.dumps(tool_input, indent=2)})")
                tool_result = None
                tool_statuses = []
                tool_function = TOOLS_FUNCTIONS[tool_name]
                tool_generator = tool_function(APP_CONTEXT, **tool_input)
                for message in tool_generator:
                    # Update tool status
                    status = message.get("status")
                    status_type = message.get("status_type", "current")
                    if status_type == "step": tool_statuses.append(status)
                    else: tool_statuses = tool_statuses[:-1] + [status]
                    response.content = "\n".join(tool_statuses)

                    # In case the tool is done, mark it as done
                    if "result" in message:
                        tool_result = message["result"]
                        response.metadata["status"] = "done"
                        response.metadata["title"] = f"🛠️ Used tool `{tool_name}`"
                        
                    # Update the chat history
                    yield history, get_memory_markdown()

                # Store final result in claude history
                claude_history.extend([
                    {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "tool_use",
                                "id": tool_id,
                                "name" : tool_name,
                                "input" : tool_input
                        }
                        ]
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_id,
                                "content": str(tool_result)
                            }
                        ]
                    }
                ])

                done = False
            else:
                raise Exception(f"Unknown content type {type(content)}")

with gr.Blocks() as demo:
    memory = gr.Markdown(render=False)
    with gr.Row(equal_height=True):
        with gr.Column(scale=80, min_width=600):
            gr.Markdown("<center><h1>Botty McBotface</h1></center>")
            gr.ChatInterface(
                fn=chatbot,
                type="messages",
                description="Botty McBotFace is really just another chatbot.",
                additional_outputs=[memory],
            )
        with gr.Column(scale=20, min_width=150, variant="compact"):
            gr.Markdown("<center><h1>Memory</h1></center>")
            memory.render()

demo.launch()