# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Botty McBotface is a Gradio-powered AI travel assistant with location awareness, memory persistence, and integrated Google Maps tools. The chatbot uses Claude AI (or OpenRouter as an alternative) to provide personalized travel recommendations based on user preferences and location context.

**Key Architecture:**
- **main.py**: Gradio interface and conversation loop with tool execution orchestration
- **tools.py**: Tool definitions (specs + functions) for memory, geocoding, places search, and place details
- **prompts/system.txt**: System prompt that emphasizes location context accuracy and preference storage
- **utils/logger.py**: Rotating file logger for debugging

## Environment Setup

**IMPORTANT**: This project uses Conda for environment management. Always activate the environment using:
```bash
source activate-env.sh
```

The script checks for Miniconda installation, creates the environment from `environment.yml` if needed, and activates it.

**Required API Keys** (in `.env`):
- `GOOGLE_MAPS_API_KEY` - For geocoding, place search, and place details
- `OPENROUTER_API_KEY` - For Claude AI model access
- `OPENROUTER_API_KEY` - (Optional) Alternative LLM provider currently used in code

## Running the Application

**Development mode with auto-reload:**
```bash
gradio main.py
```

**Production mode:**
```bash
python main.py
```

## Architecture Details

### Tool System Architecture

Tools are defined as tuples of `(TOOL_SPEC, tool_function)` in `tools.py`:
- **TOOL_SPEC**: Dictionary with `name`, `description`, and `input_schema` (JSON Schema)
- **tool_function**: Generator function that yields status updates and final result

**Tool execution flow** (main.py:101-214):
1. User message added to `claude_history`
2. LLM responds with text and/or tool_use blocks
3. For each tool_use:
   - Create pending ChatMessage with tool metadata
   - Execute tool function (generator)
   - Yield status updates to UI
   - Cache result in `tools_cache` for deduplication
   - Append tool_use + tool_result to `claude_history`
4. Loop continues until no more tool calls

**Tool caching**: Results cached by `{tool_name}_{json.dumps(tool_input)}` key to avoid redundant API calls.

### Memory System

The chatbot maintains a `system_memory` list (max 5 items) that gets injected into the system prompt on every turn:
- Memories stored via `tool_save_memory`
- Can update existing memory by index or append new
- Geocoded location + radius stored in memory to provide location context
- User preferences (food, music, arts) stored for personalization

**Memory in system prompt** (main.py:44-46):
```python
system_prompt_text += f"\n\nHere are the memories the user asked you to remember:\n{memory_string}"
```

### LLM Integration

**Current state**: Code uses OpenRouter API (main.py:66-94) instead of native Anthropic SDK. The native Anthropic code is commented out (lines 48-63) but shows the intended architecture with:
- Prompt caching on system prompt
- Tools passed as `tools` parameter
- Structured message history

**Note**: The OpenRouter implementation does NOT currently pass tools or system prompt, which means tool calling is likely broken in production.

### Conversation History

**Global state warning** (main.py:27-28): `claude_history` is a global list that stores all conversation turns. This means multiple concurrent users would share conversation history - a critical bug for multi-user deployment.

## Available Tools

1. **tool_save_memory**: Store user preferences or location context in persistent memory
2. **tool_delete_memory**: Remove memory by index
3. **tool_geocode**: Convert address to lat/lng coordinates and bounding box radius
4. **tool_places_nearby**: Search Google Places API with filters (type, radius, keyword, price, etc.)
5. **tool_place_details**: Get detailed info for a specific place_id
6. **tool_calculator**: Basic math operations (currently incomplete)

## Important Implementation Notes

- **README.md must be kept up to date** with any significant project changes
- The system prompt emphasizes always geocoding locations and saving them to memory before search queries
- Tool functions must be generators that yield `{"status": str}` for updates and `{"status": str, "result": any}` for completion
- The Gradio interface displays tool status in real-time using metadata ("pending" → "done")
- Error handling: Tool exceptions caught and displayed as failed tool calls (main.py:180-184)

## Known Issues (from TODO.md)

- BUG: Wrong radius extracted for "restaurants in porto"
- BUG: Loading mask not showing after tool call
- Tool system currently broken due to OpenRouter not receiving tool specs
- No test suite exists yet
- Response streaming not implemented
- Multiple chat sessions not supported due to global `claude_history`
