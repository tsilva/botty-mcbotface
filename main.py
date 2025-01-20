# https://docs.anthropic.com/en/docs/build-with-claude/tool-use
# https://www.gradio.app/guides/plot-component-for-maps
# TODO: ask LLM what to improve
# TODO: improve layout
# TODO: add starter examples
# TODO: add multimodality (input/ooutput): gr.Image, gr.Video, gr.Audio, gr.File, gr.HTML, gr.Gallery, gr.Plot, gr.Map
# TODO: add streaming support
# TODO: trim down data from nearby places results (filling up context too much)
# TODO: host in spaces

from dotenv import load_dotenv
load_dotenv()

import time
import json
import anthropic
import gradio as gr
from gradio import ChatMessage

from tools import TOOLS_SPECS, TOOLS_FUNCTIONS
from utils.logger import setup_logger

# Setup logger
logger = setup_logger()

system_memory = []

app_context = {
    "model_id" : "claude-3-5-sonnet-20241022",
    "max_tokens" : 1024,
    "system_memory" : system_memory,
    "system_memory_max_size" : 5
}

tools_cache = {}

# TODO: this is a hack, if I don't fix this, multiple chats won't be supported
claude_history = []

client = anthropic.Anthropic()

def load_system_prompt():
    with open('prompts/system.txt', 'r') as f:
        return f.read().strip()
    
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
    model_id = app_context["model_id"]
    max_tokens = app_context["max_tokens"]
    message = client.messages.create(
        model=model_id,
        max_tokens=max_tokens,
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

def get_tool_generator(cached_yield, tool_function, app_context, tool_input):
    """Helper function to either yield cached result or run tool function"""
    if cached_yield: yield cached_yield
    else: yield from tool_function(app_context, **tool_input)

def chatbot(message, history):
    logger.info(f"New message received: {message[:50]}...")
    try:
        # Store in claude history
        claude_history.append({
            "role": "user",
            "content": message
        })

        messages = []

        done = False
        while not done:
            done = True

            claude_response = prompt_claude()
            for content in claude_response.content:
                if content.type == "text":
                    message = ChatMessage(
                        role="assistant",
                        content=content.text
                    )
                    messages.append(message)
                    yield messages, get_memory_markdown()

                    # Store in claude history
                    claude_history.append({
                        "role": "assistant",
                        "content": content.text
                    })
                elif content.type == "tool_use":
                    tool_id = content.id
                    tool_name = content.name
                    tool_input = content.input
                    tool_key = f"{tool_name}_{json.dumps(tool_input)}" # TODO: sort input
                    tool_cached_yield = tools_cache.get(tool_key)

                    # Say that we're calling the tool
                    message = ChatMessage(
                        role="assistant",
                        content="...",
                        metadata={
                            "title" : f"🛠️ Using tool `{tool_name}`",
                            "status": "pending"
                        }
                    )
                    messages.append(message)
                    yield messages, get_memory_markdown()

                    # Call the tool
                    print(f"Calling {tool_name}({json.dumps(tool_input, indent=2)})")
                    tool_result = None
                    tool_statuses = []
                    tool_function = TOOLS_FUNCTIONS[tool_name]
                    tool_generator = get_tool_generator(tool_cached_yield, tool_function, app_context, tool_input)
                    tool_error = False
                    start_time = time.time()
                    try:
                        for tool_yield in tool_generator:
                            # Update tool status
                            status = tool_yield.get("status")
                            status_type = tool_yield.get("status_type", "current")
                            if status_type == "step": tool_statuses.append(status)
                            else: tool_statuses = tool_statuses[:-1] + [status]
                            message.content = "\n".join(tool_statuses)

                            # In case the tool is done, mark it as done
                            if "result" in tool_yield:
                                tool_result = tool_yield["result"]
                                
                                print(f"Tool {tool_name} result: {json.dumps(tool_result, indent=2)}")
                                tools_cache[tool_key] = tool_yield
                                duration = time.time() - start_time
                                message.metadata["status"] = "done"
                                message.metadata["duration"] = duration
                                message.metadata["title"] = f"🛠️ Used tool `{tool_name}`"

                            # Update the chat history
                            yield messages, get_memory_markdown()
                    except Exception as tool_exception:
                        tool_error = str(tool_exception)
                        message.metadata["status"] = "done"
                        message.content = tool_error
                        message.metadata["title"] = f"💥 Tool `{tool_name}` failed"

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
                                    "content": str(tool_error) if tool_error else str(tool_result),
                                    "is_error" : bool(tool_error)
                                }
                            ]
                        }
                    ])

                    done = False
                else:
                    raise Exception(f"Unknown content type {type(content)}")
        logger.debug(f"Generated response: {messages[-1].content[:50]}...")
        return messages, get_memory_markdown()
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        return "Sorry, an error occurred while processing your message."

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

if __name__ == "__main__":
    logger.info("Starting Botty McBotface...")
    demo.launch()