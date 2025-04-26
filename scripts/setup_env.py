#!/usr/bin/env python
"""
Setup environment script for Social Cube project.
This script creates a .env file if it doesn't exist.
"""

import os
import sys
import secrets
from pathlib import Path
from cryptography.fernet import Fernet

# Get the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent


def generate_secret_key():
    """Generate a Django secret key."""
    return "".join(
        secrets.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)")
        for i in range(50)
    )


def main():
    """Main function to create the .env file."""
    env_file = BASE_DIR / ".env"

    # Check if .env file already exists
    if env_file.exists():
        print(f"Error: .env file already exists at {env_file}")
        print("If you want to regenerate it, please delete the existing file first.")
        sys.exit(1)

    # Get environment variables from example file
    env_example = BASE_DIR / ".env.example"
    if not env_example.exists():
        print(f"Error: .env.example file not found at {env_example}")
        sys.exit(1)

    with open(env_example, "r") as f:
        env_content = f.read()

    # Replace placeholder values
    env_content = env_content.replace("your-secret-key-here", generate_secret_key())
    env_content = env_content.replace(
        "your-fernet-key-for-encrypting-bot-tokens", Fernet.generate_key().decode()
    )

    # Write .env file
    with open(env_file, "w") as f:
        f.write(env_content)

    print(f"Successfully created .env file at {env_file}")
    print("Please edit the file to add your Discord OAuth2 credentials.")


if __name__ == "__main__":
    main()
