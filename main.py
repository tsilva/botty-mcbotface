from dotenv import load_dotenv
load_dotenv()

import os
import time
import json
from openai import OpenAI
import gradio as gr
from gradio import ChatMessage

from tools import TOOLS, TOOLS_SPECS, TOOLS_FUNCTIONS
from utils.logger import setup_logger

# Setup logger
logger = setup_logger()

AVAILABLE_MODELS = [
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3-opus",
    "anthropic/claude-3-haiku",
    "openai/gpt-4-turbo",
    "openai/gpt-4",
    "openai/gpt-3.5-turbo",
    "google/gemini-pro-1.5",
    "meta-llama/llama-3.1-70b-instruct",
    "mistralai/mistral-large",
]

DEFAULT_SYSTEM_PROMPT = open('prompts/system.txt', 'r').read().strip()

ALL_TOOL_NAMES = [spec["name"] for spec in TOOLS_SPECS.values()]

system_memory = []

app_context = {
    "model_id": "anthropic/claude-3.5-sonnet",
    "max_tokens": 1024,
    "system_memory": system_memory,
    "system_memory_max_size": 5
}

tools_cache = {}

# TODO: this is a hack, if I don't fix this, multiple chats won't be supported
claude_history = []

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)

def get_memory_string():
    return "\n".join([f"{index}: {value}" for index, value in enumerate(list(system_memory))]).strip()

def get_memory_markdown():
    return "\n".join([f"{index}. {value}" for index, value in enumerate(list(system_memory))]).strip()

def _convert_tools(enabled_tools):
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
        if spec["name"] in enabled_tools
    ]

def prompt_claude(system_prompt, enabled_tools, temperature, top_p, frequency_penalty, presence_penalty):
    system_prompt_memory_str = get_memory_string()
    system_prompt_text = system_prompt
    if system_prompt_memory_str:
        system_prompt_text += f"\n\nHere are the memories the user asked you to remember:\n{system_prompt_memory_str}"

    model_id = app_context["model_id"]
    max_tokens = app_context["max_tokens"]

    messages = [{"role": "system", "content": system_prompt_text}] + claude_history

    converted_tools = _convert_tools(enabled_tools)

    kwargs = dict(
        model=model_id,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        messages=messages
    )
    if converted_tools:
        kwargs["tools"] = converted_tools

    response = client.chat.completions.create(**kwargs)
    return response

def get_tool_generator(cached_yield, tool_function, app_context, tool_input):
    """Helper function to either yield cached result or run tool function"""
    if cached_yield: yield cached_yield
    else: yield from tool_function(app_context, **tool_input)

def chatbot(message, history, model, system_prompt, enabled_tools, max_tokens, temperature, top_p, frequency_penalty, presence_penalty):
    logger.info(f"New message received: {message[:50]}...")

    # Update app_context with current settings
    app_context["model_id"] = model
    app_context["max_tokens"] = max_tokens

    try:
        claude_history.append({
            "role": "user",
            "content": message
        })

        messages = []

        done = False
        while not done:
            done = True

            claude_response = prompt_claude(system_prompt, enabled_tools, temperature, top_p, frequency_penalty, presence_penalty)
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

                    # Skip disabled tools
                    if tool_name not in enabled_tools:
                        claude_history.append({
                            "role": "tool",
                            "tool_call_id": tool_id,
                            "content": f"Tool '{tool_name}' is disabled."
                        })
                        continue

                    msg = ChatMessage(
                        role="assistant",
                        content="...",
                        metadata={
                            "title": f"🛠️ Using tool `{tool_name}`",
                            "status": "pending"
                        }
                    )
                    messages.append(msg)
                    yield messages, get_memory_markdown()

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

                    claude_history.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": str(tool_error) if tool_error else str(tool_result)
                    })

                done = False
            else:
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

    # Settings components (render=False for use as additional_inputs)
    model_dropdown = gr.Dropdown(
        choices=AVAILABLE_MODELS,
        value=AVAILABLE_MODELS[0],
        label="Model",
        render=False
    )
    system_prompt_box = gr.Textbox(
        value=DEFAULT_SYSTEM_PROMPT,
        label="System Prompt",
        lines=6,
        render=False
    )
    tools_checkbox = gr.CheckboxGroup(
        choices=ALL_TOOL_NAMES,
        value=ALL_TOOL_NAMES,
        label="Enabled Tools",
        render=False
    )
    max_tokens_slider = gr.Slider(
        minimum=64, maximum=4096, value=1024, step=64,
        label="Max Tokens",
        render=False
    )
    temperature_slider = gr.Slider(
        minimum=0.0, maximum=2.0, value=0.0, step=0.05,
        label="Temperature",
        render=False
    )
    top_p_slider = gr.Slider(
        minimum=0.0, maximum=1.0, value=1.0, step=0.05,
        label="Top P",
        render=False
    )
    freq_penalty_slider = gr.Slider(
        minimum=-2.0, maximum=2.0, value=0.0, step=0.1,
        label="Frequency Penalty",
        render=False
    )
    presence_penalty_slider = gr.Slider(
        minimum=-2.0, maximum=2.0, value=0.0, step=0.1,
        label="Presence Penalty",
        render=False
    )

    with gr.Accordion("Settings", open=False):
        with gr.Row():
            with gr.Column():
                model_dropdown.render()
                system_prompt_box.render()
                tools_checkbox.render()
            with gr.Column():
                max_tokens_slider.render()
                temperature_slider.render()
                top_p_slider.render()
                freq_penalty_slider.render()
                presence_penalty_slider.render()

    with gr.Row(equal_height=True):
        with gr.Column(scale=3, min_width=600):
            gr.Markdown("<center><h1>Chat Sandbox</h1></center>")
            gr.ChatInterface(
                fn=chatbot,
                description="A configurable AI chat sandbox with tools and memory.",
                additional_inputs=[
                    model_dropdown,
                    system_prompt_box,
                    tools_checkbox,
                    max_tokens_slider,
                    temperature_slider,
                    top_p_slider,
                    freq_penalty_slider,
                    presence_penalty_slider,
                ],
                additional_outputs=[memory],
            )
        with gr.Column(scale=1, min_width=150, variant="compact"):
            gr.Markdown("<center><h1>Memory</h1></center>")
            memory.render()

if __name__ == "__main__":
    logger.info("Starting Chat Sandbox...")
    demo.launch()
