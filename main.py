#!/usr/bin/env python3
"""
Main entry point for United Voice Agent
"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.voice_agent import main

if __name__ == "__main__":
    main()