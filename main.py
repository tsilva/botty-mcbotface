# https://docs.anthropic.com/en/docs/build-with-claude/tool-use
# TODO: cache prompts
# TODO: add support for when tools fail
# TODO: ask what to improve
# TODO: add geocoding tool, tell to store geocode user's location and store in memory
# TODO: show current memory in GUI

from dotenv import load_dotenv
load_dotenv()

import os
import json
import anthropic

from tools import TOOLS_SPECS, TOOLS_FUNCTIONS

system_memory = []
EXTERNALS = {
    "system_memory" : system_memory,
    "system_memory_max_size" : 5
}

def add_to_history(history, message):
    print(json.dumps(message, indent=2))
    history.append(message)

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

def load_system_prompt():
    with open('prompts/system.txt', 'r') as f:
        return f.read().strip()


client = anthropic.Anthropic()

history_metadata = {}
def gradio_history_to_claude(history):
    anthropic_history = []
    for index, x in enumerate(history):
        metadata = x.get("metadata", {})
        metadata = history_metadata.get(index, {})
        if metadata.get("tool_id"):
            anthropic_history.append({
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": metadata["tool_id"],
                        "name" : metadata["tool_name"],
                        "input" : metadata["tool_input"]
                   }
                ]
            })
            anthropic_history.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": metadata["tool_id"],
                        "content": str(metadata["tool_result"])
                    }
                ]
            })
        else:
            anthropic_history.append({
                "role": x["role"],
                "content": [
                    {
                        "type": "text",
                        "text": x["content"]
                    }
                ]
            })
    return anthropic_history

def chatbot(message, history):
    # Build the system prompt including all memories the user asked to remember
    system_prompt_memory_str = "\n".join([f"{index}: {value}" for index, value in enumerate(list(system_memory))]).strip()
    system_prompt_text = load_system_prompt()
    if system_prompt_memory_str: system_prompt_text += f"\n\nHere are the memories the user asked you to remember:\n{system_prompt_memory_str}"
    
    # Convert gradio history to Claude format, add new user message
    messages = gradio_history_to_claude([*history, {"role": "user", "content": message}])

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
        messages=messages
    )

    response = []

    # Process tool calls
    for content in message.content:
        if content.type == "tool_use":
            tool_id = content.id
            tool_name = content.name
            tool_input = content.input
            print(f"Calling {tool_name}({json.dumps(tool_input, indent=2)})")
            tool_function = TOOLS_FUNCTIONS[tool_name]
            result = tool_function(EXTERNALS, **tool_input)

            response.append({
                "role": "assistant",
                "content": str(result),
                "metadata": {
                    "title": f"🛠️ Used {tool_name}"
                }
            })
            # TODO: figure out a better way to store metadata,
            # remember that history can be rewritten, making this obsolete
            history_metadata[len(response) - 1] = {
                "tool_name": tool_name,
                "tool_id": tool_id,
                "tool_result" : result,
                "tool_input" : tool_input
            }
        else:
            response.append({
                "role": "assistant",
                "content": content.text
            })

    return response

def main():
    while True:
        # In case the last message was from the assistant, prompt the user
        last_message = conversation_history[-1] if conversation_history else None
        if last_message is None or last_message["role"] == "assistant":
            user_input = input("You: ")
            if user_input.lower() == 'quit': break
            add_to_history({"role": "user", "content": user_input})
        chatbot(user_input, conversation_history)

if __name__ == "__main__":
    main()