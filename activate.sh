#!/bin/bash

# Check if Miniconda is installed
if ! command -v conda &> /dev/null; then
    echo "Miniconda is not installed. Please install Miniconda and try again."
    exit 1
fi

# Check if environment.yml exists
if [ ! -f "environment.yml" ]; then
    echo "environment.yml not found in the current directory. Please provide an environment.yml file."
    exit 1
fi

# Extract environment name from environment.yml
env_name=$(grep "^name:" environment.yml | awk '{print $2}')

if [ -z "$env_name" ]; then
    echo "Environment name not found in environment.yml. Please ensure the file has a 'name' field."
    exit 1
fi

# Check if Conda is initialized
if ! conda info &> /dev/null; then
    echo "Conda is not initialized. Run 'conda init' and restart your shell."
    exit 1
fi

# Check if the environment already exists
if conda env list | grep -q "^$env_name\s"; then
    echo "Activating existing environment: $env_name"
    source $(conda info --base)/etc/profile.d/conda.sh
    conda activate "$env_name"
else
    echo "Environment $env_name not found. Creating it from environment.yml..."
    conda env create -f environment.yml

    if [ $? -ne 0 ]; then
        echo "Failed to create the environment. Check your environment.yml for errors."
        exit 1
    fi

    echo "Environment $env_name created successfully. Activating it..."
    source $(conda info --base)/etc/profile.d/conda.sh
    conda activate "$env_name"
fi

# Confirm activation
if [ "$CONDA_DEFAULT_ENV" = "$env_name" ]; then
    echo "Environment $env_name is now active."
else
    echo "Failed to activate environment $env_name."
    exit 1
fi
