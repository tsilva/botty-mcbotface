# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Chat Sandbox is a Gradio-powered configurable AI chat interface with a collapsible settings panel, tool toggles, memory persistence, and integrated Google Maps tools. It connects to multiple LLM providers via OpenRouter and lets users customize model, system prompt, enabled tools, and generation parameters at runtime.

**Key Architecture:**
- **main.py**: Gradio interface with settings accordion, chat interface, and tool execution orchestration
- **tools.py**: Tool definitions (specs + functions) for memory, geocoding, places search, calculator, and place details
- **prompts/system.txt**: Default generic assistant system prompt (editable via UI)
- **utils/logger.py**: Rotating file logger for debugging

## Environment Setup

**IMPORTANT**: This project uses Conda for environment management. Always activate the environment using:
```bash
source activate-env.sh
```

The script checks for Miniconda installation, creates the environment from `environment.yml` if needed, and activates it.

**Required API Keys** (in `.env`):
- `OPENROUTER_API_KEY` - For LLM model access (supports Claude, GPT-4, Gemini, Llama, Mistral)
- `GOOGLE_MAPS_API_KEY` - For geocoding, place search, and place details tools

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

### Settings Panel

A collapsible `gr.Accordion("Settings")` at the top of the UI containing:
- **Left column**: Model dropdown, system prompt textbox, tool checkboxes
- **Right column**: Sliders for max_tokens, temperature, top_p, frequency_penalty, presence_penalty

All settings are passed to `chatbot()` via `additional_inputs`.

### Tool System Architecture

Tools are defined as tuples of `(TOOL_SPEC, tool_function)` in `tools.py`:
- **TOOL_SPEC**: Dictionary with `name`, `description`, and `input_schema` (JSON Schema)
- **tool_function**: Generator function that yields status updates and final result

**Tool toggles**: Users enable/disable tools via `CheckboxGroup`. Disabled tools are filtered out of the API call and skipped during execution.

**Tool execution flow** (main.py):
1. User message added to `claude_history`
2. LLM responds with text and/or tool calls
3. For each tool call:
   - Skip if tool is disabled (returns "disabled" message to LLM)
   - Create pending ChatMessage with tool metadata
   - Execute tool function (generator)
   - Yield status updates to UI
   - Cache result in `tools_cache` for deduplication
   - Append tool result to `claude_history`
4. Loop continues until no more tool calls

**Tool caching**: Results cached by `{tool_name}_{json.dumps(tool_input)}` key to avoid redundant API calls.

### Memory System

The chatbot maintains a `system_memory` list (max 5 items) that gets injected into the system prompt on every turn:
- Memories stored via `tool_save_memory`
- Can update existing memory by index or append new
- Displayed in a sidebar panel

### LLM Integration

Uses OpenRouter API via the OpenAI SDK. The `prompt_claude()` function accepts all generation parameters (temperature, top_p, frequency_penalty, presence_penalty) and only sends enabled tools to the API.

### Conversation History

**Global state warning**: `claude_history` is a global list that stores all conversation turns. This means multiple concurrent users would share conversation history.

## Available Tools

1. **tool_save_memory**: Store user preferences or context in persistent memory
2. **tool_delete_memory**: Remove memory by index
3. **tool_geocode**: Convert address to lat/lng coordinates and bounding box radius
4. **tool_places_nearby**: Search Google Places API with filters (type, radius, keyword, price, etc.)
5. **tool_place_details**: Get detailed info for a specific place_id
6. **tool_calculator**: Basic math operations

## Important Implementation Notes

- **README.md must be kept up to date** with any significant project changes
- Tool functions must be generators that yield `{"status": str}` for updates and `{"status": str, "result": any}` for completion
- The Gradio interface displays tool status in real-time using metadata ("pending" -> "done")
- Error handling: Tool exceptions caught and displayed as failed tool calls
- Settings are passed as `additional_inputs` to `gr.ChatInterface` and forwarded through the call chain

## Known Issues

- BUG: Wrong radius extracted for "restaurants in porto"
- BUG: Loading mask not showing after tool call
- No test suite exists yet
- Response streaming not implemented
- Multiple chat sessions not supported due to global `claude_history`
