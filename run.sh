#!/bin/bash

# United Voice Agent Runner Script

# Check for required envionment variables
if [ -z "$ELEVENLABS_API_KEY" ] && [ -z "$(grep ELEVENLABS_API_KEY .env 2>/dev/null)" ]; then
    echo "Error: ELEVENLABS_API_KEY not set"
    echo "Please set it in .env file or as environment variable"
    exit 1
fi

if [ -z "$GROQ_API_KEY" ] && [ -z "$(grep GROQ_API_KEY .env 2>/dev/null)" ]; then
    echo "Error: GROQ_API_KEY not set"
    echo "Please set it in .env file or as environment variable"
    exit 1
fi

# Run the application
uv run python main.py