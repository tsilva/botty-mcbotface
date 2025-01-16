# https://docs.anthropic.com/en/docs/build-with-claude/tool-use
# TODO: add support for when tools fail
# TODO: ask what to improve
# TODO: add geocoding tool, tell to store geocode user's location and store in memory
# TODO: show current memory in GUI
# TODO: customize UI
# TODO: host in spaces
# TODO: add examples
# TODO: add multimodality
# TODO: gr.Image, gr.Video, gr.Audio, gr.File, gr.HTML, gr.Gallery, gr.Plot, gr.Map
# TODO: https://www.gradio.app/guides/plot-component-for-maps

from dotenv import load_dotenv
load_dotenv()

import os
import time
import json
import anthropic
import gradio as gr

from tools import TOOLS_SPECS, TOOLS_FUNCTIONS

MODEL_ID = "claude-3-5-sonnet-20241022"
MAX_TOKENS = 1024

system_memory = []
EXTERNALS = {
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
                yield _message, get_memory_markdown()
                
                # Store in claude history
                claude_history.append({**_message})
            elif content.type == "tool_use":
                tool_id = content.id
                tool_name = content.name
                tool_input = content.input

                # Say that we're calling the tool
                start_time = time.time()
                response = gr.ChatMessage(
                    content="Processing...",
                    metadata={"title": f"🛠️ Calling {tool_name}", "id": 0, "status": "pending"}
                )
                yield response, get_memory_markdown()

                # Call the tool
                print(f"Calling {tool_name}({json.dumps(tool_input, indent=2)})")
                tool_function = TOOLS_FUNCTIONS[tool_name]
                tool_result = tool_function(EXTERNALS, **tool_input)

                # Say that we're done calling the tool
                response.content = str(tool_result) if tool_result else "Done."
                response.metadata["title"] = f"🛠️ Called {tool_name}"
                response.metadata["status"] = "done"
                response.metadata["duration"] = time.time() - start_time
                yield response, get_memory_markdown()
                
                # Store in claude history
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
    with gr.Row():
        with gr.Column():
            gr.Markdown("<center><h1>Botty McBotface</h1></center>")
            gr.ChatInterface(
                fn=chatbot,
                type="messages",
                description="Botty McBotFace is really just another chatbot.",
                #examples=["Hello!", "What's the weather like?", "Tell me a joke"],
                #additional_inputs=[system_prompt, slider],
                #retry_btn=True,
                #undo_btn=True,
                #clear_btn=True,
                additional_outputs=[memory],
            )
        with gr.Column():
            gr.Markdown("<center><h1>Memory</h1></center>")
            memory.render()

demo.launch()
