---
title: chat-sandbox
app_file: main.py
sdk: gradio
sdk_version: 6.5.0
license: mit
emoji: 🧪
colorTo: blue
pinned: true
short_description: A configurable AI chat sandbox with tools and memory
---

<div align="center">
  <img src="logo.png" alt="chat-sandbox" width="512"/>

  [![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
  [![Python](https://img.shields.io/badge/Python-3.11-3776AB.svg)](https://python.org)
  [![Gradio](https://img.shields.io/badge/Gradio-6.5.0-orange.svg)](https://gradio.app)
  [![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97-Spaces-yellow)](https://huggingface.co/spaces/tsilva/botty-mcbotface)

  **A configurable AI chat sandbox with toggleable tools, memory, and LLM parameter controls**

  [Live Demo](https://huggingface.co/spaces/tsilva/botty-mcbotface)
</div>

## Overview

Chat Sandbox is a Gradio-powered AI chat interface that lets you configure the model, system prompt, enabled tools, and generation parameters on the fly. It connects to multiple LLM providers via OpenRouter and includes built-in tools for memory, geocoding, place search, and math.

## Features

- **Model Selection** - Choose from Claude, GPT-4, Gemini, Llama, Mistral, and more via OpenRouter
- **Custom System Prompt** - Edit the system prompt directly in the UI
- **Tool Toggles** - Enable/disable individual tools (memory, geocoding, places, calculator)
- **LLM Parameters** - Adjust temperature, top_p, frequency penalty, presence penalty, and max tokens
- **Memory System** - Persistent memory sidebar for storing preferences and context
- **Place Search** - Google Maps integration for geocoding, nearby search, and place details
- **Real-time Tool Feedback** - Visual status updates as tools execute

## Quick Start

```bash
# Clone and setup
git clone https://github.com/tsilva/botty-mcbotface.git
cd botty-mcbotface
source activate-env.sh

# Configure API keys
cp .env.example .env
# Edit .env with your keys

# Run
python main.py
```

## Installation

### Prerequisites

- [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or Anaconda
- OpenRouter API key (for LLM access)
- Google Maps API key (optional, for geocoding and place search tools)

### Environment Setup

```bash
# This script checks for Miniconda, creates the env if needed, and activates it
source activate-env.sh
```

### API Keys

Create a `.env` file with your API keys:

```bash
OPENROUTER_API_KEY=your_openrouter_key
GOOGLE_MAPS_API_KEY=your_google_maps_key  # Optional, for geo tools
```

## Usage

**Production mode:**
```bash
python main.py
```

**Development mode with auto-reload:**
```bash
gradio main.py
```

The chat interface will be available at `http://localhost:7860`.

## Settings Panel

The collapsible settings accordion at the top of the UI provides:

| Setting | Description |
|---------|-------------|
| Model | Select LLM model (Claude, GPT-4, Gemini, Llama, Mistral) |
| System Prompt | Editable system prompt text |
| Enabled Tools | Checkbox toggles for each tool |
| Max Tokens | Maximum response length (64-4096) |
| Temperature | Randomness control (0.0-2.0) |
| Top P | Nucleus sampling threshold (0.0-1.0) |
| Frequency Penalty | Penalize repeated tokens (-2.0 to 2.0) |
| Presence Penalty | Penalize already-used tokens (-2.0 to 2.0) |

## Available Tools

| Tool | Description |
|------|-------------|
| `tool_save_memory` | Store preferences and context in persistent memory |
| `tool_delete_memory` | Remove items from memory |
| `tool_geocode` | Convert addresses to coordinates with bounding box |
| `tool_places_nearby` | Search Google Places with filters (type, price, keyword) |
| `tool_place_details` | Get detailed info for a specific place |
| `tool_calculator` | Basic math operations |

## Architecture

```
botty-mcbotface/
├── main.py              # Gradio interface, settings panel, and conversation loop
├── tools.py             # Tool definitions (specs + functions)
├── prompts/
│   └── system.txt       # Default system prompt
├── utils/
│   └── logger.py        # Rotating file logger
├── environment.yml      # Conda environment definition
└── activate-env.sh      # Environment activation script
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
