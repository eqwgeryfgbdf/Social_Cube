#!/usr/bin/env python
"""
Run development server script for Social Cube project.
This script sets the DJANGO_ENV environment variable and runs the server.
"""

import os
import sys
import subprocess
from pathlib import Path

# Get the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent


def main():
    """Main function to run the development server."""
    # Set environment variables
    env = os.environ.copy()
    env["DJANGO_ENV"] = "development"

    # Check if .env file exists
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        print(f"Warning: .env file not found at {env_file}")
        print("You can create it by running: python scripts/setup_env.py")

    # Run Django development server
    cmd = [sys.executable, "manage.py", "runserver"]
    print(f"Running command: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, env=env, cwd=BASE_DIR, check=True)
    except KeyboardInterrupt:
        print("\nServer stopped")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
