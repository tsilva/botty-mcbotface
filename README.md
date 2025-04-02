---
title: botty-mcbotface
app_file: main.py
sdk: gradio
sdk_version: 5.12.0
license: mit
emoji: 😻
colorTo: blue
pinned: true
short_description: 💬 Just what you needed, another AI chatbot 🤦
---
# 🤖 botty-mcbotface

🗣️ A location-aware AI chatbot with memory and integrated tools for travel assistance

## 📖 Overview

Botty McBotface is a Gradio-powered AI assistant that helps with travel recommendations and location-based information. It features a long-term memory system to remember your preferences and uses integrated tools like geocoding, place search, and weather information to provide personalized travel insights.

## 🚀 Installation

```bash
git clone https://github.com/tsilva/botty-mcbotface.git
cd botty-mcbotface
pipx install . --force
```

## 🛠️ Environment Setup

The project uses a Conda environment defined in `environment.yml`. To set up:

```bash
# IMPORTANT: You must SOURCE the activation script
source activate-env.sh
# or
. activate-env.sh
```

This will check for Miniconda, create the environment if needed, and activate it automatically.

## 🔑 API Keys

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit the `.env` file to add:
- `GOOGLE_MAPS_API_KEY` - For location services
- `ANTHROPIC_API_KEY` - For Claude AI model access

## 🚀 Usage

Run the chatbot:

```bash
python main.py
```

For development with auto-reload:

```bash
gradio main.py
```

### Features

- **Location Awareness**: Automatically geocodes and remembers locations
- **Memory System**: Stores your preferences for personalized recommendations
- **Integrated Tools**: Search for places, get directions, check weather
- **Gradio Interface**: Easy-to-use chat interface with memory display

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.