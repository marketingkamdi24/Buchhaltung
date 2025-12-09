#!/usr/bin/env python3
"""
Run script for Buchhaltung application.
Starts the Flask web server.
"""
import sys
import os

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Set the working directory to the project root
os.chdir(current_dir)


def run():
    """Run the application."""
    # Import here to ensure path is set correctly
    from src.ui.app import main
    main()


if __name__ == "__main__":
    run()