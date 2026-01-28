from dotenv import load_dotenv
load_dotenv()

import os
import time
import json
from openai import OpenAI
import gradio as gr
from gradio import ChatMessage

from tools import TOOLS_SPECS, TOOLS_FUNCTIONS
from utils.logger import setup_logger

# Setup logger
logger = setup_logger()

system_memory = []

app_context = {
    "model_id" : "anthropic/claude-3.5-sonnet",
    "max_tokens" : 1024,
    "system_memory" : system_memory,
    "system_memory_max_size" : 5
}

tools_cache = {}

# TODO: this is a hack, if I don't fix this, multiple chats won't be supported
claude_history = []

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)

def load_system_prompt():
    with open('prompts/system.txt', 'r') as f:
        return f.read().strip()
    
def get_memory_string():
    return "\n".join([f"{index}: {value}" for index, value in enumerate(list(system_memory))]).strip()

def get_memory_markdown():
    return "\n".join([f"{index}. {value}" for index, value in enumerate(list(system_memory))]).strip()

def _convert_tools():
    """Convert Anthropic-format tool specs to OpenAI function-calling format."""
    return [
        {
            "type": "function",
            "function": {
                "name": spec["name"],
                "description": spec["description"],
                "parameters": spec["input_schema"]
            }
        }
        for spec in TOOLS_SPECS.values()
    ]

def prompt_claude():
    # Build the system prompt including all memories the user asked to remember
    system_prompt_memory_str = get_memory_string()
    system_prompt_text = load_system_prompt()
    if system_prompt_memory_str: system_prompt_text += f"\n\nHere are the memories the user asked you to remember:\n{system_prompt_memory_str}"

    model_id = app_context["model_id"]
    max_tokens = app_context["max_tokens"]

    messages = [{"role": "system", "content": system_prompt_text}] + claude_history

    response = client.chat.completions.create(
        model=model_id,
        max_tokens=max_tokens,
        temperature=0.0,
        tools=_convert_tools(),
        messages=messages
    )

    return response

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
            choice = claude_response.choices[0].message

            # Handle text content
            if choice.content:
                msg = ChatMessage(
                    role="assistant",
                    content=choice.content
                )
                messages.append(msg)
                yield messages, get_memory_markdown()

            # Handle tool calls
            if choice.tool_calls:
                # Store assistant message with tool calls in history
                assistant_msg = {"role": "assistant", "content": choice.content or ""}
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in choice.tool_calls
                ]
                claude_history.append(assistant_msg)

                for tool_call in choice.tool_calls:
                    tool_id = tool_call.id
                    tool_name = tool_call.function.name
                    tool_input = json.loads(tool_call.function.arguments)
                    tool_key = f"{tool_name}_{json.dumps(tool_input)}"
                    tool_cached_yield = tools_cache.get(tool_key)

                    # Say that we're calling the tool
                    msg = ChatMessage(
                        role="assistant",
                        content="...",
                        metadata={
                            "title" : f"🛠️ Using tool `{tool_name}`",
                            "status": "pending"
                        }
                    )
                    messages.append(msg)
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
                            status = tool_yield.get("status")
                            status_type = tool_yield.get("status_type", "current")
                            if status_type == "step": tool_statuses.append(status)
                            else: tool_statuses = tool_statuses[:-1] + [status]
                            msg.content = "\n".join(tool_statuses)

                            if "result" in tool_yield:
                                tool_result = tool_yield["result"]
                                print(f"Tool {tool_name} result: {json.dumps(tool_result, indent=2)}")
                                tools_cache[tool_key] = tool_yield
                                duration = time.time() - start_time
                                msg.metadata["status"] = "done"
                                msg.metadata["duration"] = duration
                                msg.metadata["title"] = f"🛠️ Used tool `{tool_name}`"

                            yield messages, get_memory_markdown()
                    except Exception as tool_exception:
                        tool_error = str(tool_exception)
                        msg.metadata["status"] = "done"
                        msg.content = tool_error
                        msg.metadata["title"] = f"💥 Tool `{tool_name}` failed"

                    # Store tool result in history
                    claude_history.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": str(tool_error) if tool_error else str(tool_result)
                    })

                done = False
            else:
                # No tool calls — store text-only assistant message
                if choice.content:
                    claude_history.append({
                        "role": "assistant",
                        "content": choice.content
                    })
        logger.debug(f"Generated response: {messages[-1].content[:50]}...")
        return messages, get_memory_markdown()
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        return "Sorry, an error occurred while processing your message."

with gr.Blocks(fill_height=True) as demo:
    memory = gr.Markdown(render=False)
    with gr.Row(equal_height=True):
        with gr.Column(scale=3, min_width=600):
            gr.Markdown("<center><h1>Botty McBotface</h1></center>")
            gr.ChatInterface(
                fn=chatbot,
                description="Botty McBotFace is really just another chatbot.",
                additional_outputs=[memory],
            )
        with gr.Column(scale=1, min_width=150, variant="compact"):
            gr.Markdown("<center><h1>Memory</h1></center>")
            memory.render()

if __name__ == "__main__":
    logger.info("Starting Botty McBotface...")
    demo.launch()