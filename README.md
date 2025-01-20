---
title: botty-mcbotface
app_file: main.py
sdk: gradio
sdk_version: 5.12.0
---
# 🤖 Botty McBotface

<p align="center">
  <img src="logo.png" alt="Botty McBotface Logo" width="400"/>
</p>

> 💬 Just what you needed, another AI chatbot trying to remember things and use tools without breaking everything 🤦

## ✨ Features

- 🧠 Long-term memory system
- 🛠️ Integrated tools support
- 🌍 Location awareness
- 🌤️ Weather information
- 🔍 Place search capabilities
- 🖥️ Gradio-powered GUI

## 🛠️ Installation

1. Clone this repository:
   ```sh
   git clone https://github.com/tsilva/botty-mcbotface.git
   ```
2. Navigate to the project directory:
   ```sh
   cd botty-mcbotface
   ```

## Environment Setup

The project uses a Conda environment defined in `environment.yml`. To set up and activate the environment:

1. Ensure you have Miniconda or Anaconda installed
2. **IMPORTANT:** You must SOURCE the activation script (do not run with bash/sh):
   ```bash
   source activate-env.sh
   # or
   . activate-env.sh
   ```

⚠️ Running with `bash activate-env.sh` or `./activate-env.sh` will not work!

The script will:
- Check for Miniconda installation
- Create the environment if it doesn't exist
- Activate the environment automatically

Note: Using `./activate-env.sh` won't work as the script needs to be sourced to modify your current shell environment.

## 🚀 Usage

1. Run the chatbot:
   ```sh
   python main.py
   ```

2. For development with auto-reload:
   ```sh
   gradio main.py
   ```
   This will automatically restart the app when you make changes to the source files.

3. Interact with the chatbot through the GUI.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
