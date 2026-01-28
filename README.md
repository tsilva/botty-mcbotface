---
title: botty-mcbotface
app_file: main.py
sdk: gradio
sdk_version: 6.5.0
license: mit
emoji: 😻
colorTo: blue
pinned: true
short_description: A location-aware AI chatbot with memory and integrated tools
---

<div align="center">
  <img src="logo.png" alt="botty-mcbotface" width="512"/>

  [![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
  [![Python](https://img.shields.io/badge/Python-3.11-3776AB.svg)](https://python.org)
  [![Gradio](https://img.shields.io/badge/Gradio-6.5.0-orange.svg)](https://gradio.app)
  [![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97-Spaces-yellow)](https://huggingface.co/spaces/tsilva/botty-mcbotface)

  **🗺️ Your AI travel buddy that remembers your preferences and knows its way around Google Maps**

  [Live Demo](https://huggingface.co/spaces/tsilva/botty-mcbotface)
</div>

## Overview

Botty McBotface is a Gradio-powered AI chatbot that provides personalized travel recommendations. It remembers your preferences across conversations, automatically geocodes locations you mention, and uses Google Maps APIs to search for places, get directions, and provide detailed location information.

## Features

- **Location Awareness** - Automatically geocodes addresses and maintains location context for searches
- **Memory System** - Stores your preferences (food, music, arts) for personalized recommendations
- **Place Search** - Search nearby restaurants, attractions, hotels with filters for price, ratings, and more
- **Place Details** - Get comprehensive info including reviews, hours, and contact details
- **Real-time Tool Feedback** - Visual status updates as the assistant uses its tools

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
- Google Maps API key (for geocoding and place search)
- Anthropic API key (for Claude AI) or OpenRouter API key

### Environment Setup

The project uses Conda for environment management:

```bash
# This script checks for Miniconda, creates the env if needed, and activates it
source activate-env.sh
```

### API Keys

Create a `.env` file with your API keys:

```bash
GOOGLE_MAPS_API_KEY=your_google_maps_key
OPENROUTER_API_KEY=your_anthropic_key
OPENROUTER_API_KEY=your_openrouter_key  # Optional alternative
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

### Example Conversations

```
You: I'm planning a trip to Porto, Portugal
Bot: [Geocodes Porto, saves to memory]
     I've noted Porto as your current location context!

You: Find me some good seafood restaurants
Bot: [Searches nearby places with type=seafood_restaurant]
     Here are the top seafood spots in Porto...

You: I prefer budget-friendly options
Bot: [Saves preference to memory]
     Got it! I'll prioritize affordable options in future searches.
```

## Available Tools

| Tool | Description |
|------|-------------|
| `tool_geocode` | Convert addresses to coordinates with bounding box |
| `tool_places_nearby` | Search Google Places with filters (type, price, keyword) |
| `tool_place_details` | Get detailed info for a specific place |
| `tool_save_memory` | Store preferences and location context |
| `tool_delete_memory` | Remove items from memory |
| `tool_calculator` | Basic math operations |

## Architecture

```
botty-mcbotface/
├── main.py              # Gradio interface and conversation loop
├── tools.py             # Tool definitions (specs + functions)
├── prompts/
│   └── system.txt       # System prompt for location-aware behavior
├── utils/
│   └── logger.py        # Rotating file logger
├── environment.yml      # Conda environment definition
└── activate-env.sh      # Environment activation script
```

### How It Works

1. User message is added to conversation history
2. LLM responds with text and/or tool calls
3. For each tool call:
   - UI shows pending status with tool name
   - Tool executes (geocode, search, etc.)
   - Results cached to avoid duplicate API calls
   - UI updates with completion status
4. Loop continues until no more tool calls

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
