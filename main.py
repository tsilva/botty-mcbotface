# https://docs.anthropic.com/en/docs/build-with-claude/tool-use
# TODO: cache prompts
# TODO: add support for when tools fail
# TODO: ask what to improve
# TODO: add geocoding tool, tell to store geocode user's location and store in memory

from dotenv import load_dotenv
load_dotenv()

import os
import json
import anthropic

from tools import TOOLS_SPECS, TOOLS_FUNCTIONS

SYSTEM_MEMORY_MAX_SIZE = 5

system_memory = []


def add_to_history(message):
    global conversation_history
    print(json.dumps(message, indent=2))
    conversation_history.append(message)

def content_block_to_dict(content):
    if content.type == "text":
        return {
            "type": "text",
            "text": content.text
        }
    elif content.type == "tool_use":
        return {
            "type": "tool_use",
            "id": content.id,
            "name": content.name,
            "input": content.input
        }

print("ChatBot initialized. Type 'quit' to exit.")

client = anthropic.Anthropic()
conversation_history = []

while True:
    # In case the last message was from the assistant, prompt the user
    last_message = conversation_history[-1] if conversation_history else None
    if last_message is None or last_message["role"] == "assistant":
        user_input = input("You: ")
        if user_input.lower() == 'quit': break
        add_to_history({"role": "user", "content": user_input})

    # Build the system prompt including all memories the user asked to remember
    system_prompt_memory_str = "\n".join([f"{index}: {value}" for index, value in enumerate(list(system_memory))]).strip()
    system_prompt_text = f"""
You are a digital assistant that can help with a variety of tasks. You can provide information about the weather, perform mathematical calculations, and search for places nearby.

Important: When a user mentions any location or address in their message, you must:
1. Use the geocoding tool to get the coordinates
2. Save those coordinates in memory using the save_memory tool
3. Use those saved coordinates for any subsequent nearby searches

For example, if a user says "I'm in Porto", you should:
- First call geocode with "Porto, Portugal"
- Then save the coordinates in memory
- Use these coordinates when they later ask about nearby places

Never mention that you use tools or that you are a digital assistant. Just focus on solving the user's problem.
""".strip()
    if system_prompt_memory_str: system_prompt_text += f"\n\nHere are the memories the user asked you to remember:\n{system_prompt_memory_str}"

    # Send message to Claude
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        temperature=0.0, 
        tools=TOOLS_SPECS.values(),
        system=[{
            "type": "text", 
            "text": system_prompt_text, 
            "cache_control": {"type": "ephemeral"} # Prompt caching references the entire prompt - tools, system, and messages (in that order) up to and including the block designated with cache_control.
        }],
        messages=conversation_history
    )

    # Add response to history
    add_to_history({
        "role": "assistant",
        "content": [content_block_to_dict(x) for x in message.content]
    })
    
    # Process tool calls
    for content in message.content:
        if not content.type == "tool_use": continue

        tool_id = content.id
        func_name = content.name
        func_args = content.input
        print(f"Calling {func_name}({json.dumps(func_args, indent=2)})")
        tool_function = TOOLS_FUNCTIONS[func_name]
        func = tool_function[func_name]
        result = func(**func_args)

        add_to_history({
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": str(result)
                }
            ]
        })