#!/usr/bin/env python
"""
Generate secure secrets for Django and production environment.
This script creates secure random secrets for use in production environments.
"""

import argparse
import secrets
import string
import os
import re
from pathlib import Path


def generate_django_secret_key(length=50):
    """Generate a secure random string suitable for use as a Django secret key."""
    # Characters suitable for Django's secret key
    chars = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
    return ''.join(secrets.choice(chars) for _ in range(length))


def generate_password(length=16):
    """Generate a secure random password."""
    # Characters suitable for passwords
    chars = string.ascii_letters + string.digits + '!@#$%^&*'
    # Ensure at least one of each character type
    while True:
        password = ''.join(secrets.choice(chars) for _ in range(length))
        # Check if the password contains at least one uppercase, one lowercase, one digit, and one special character
        if (any(c.isupper() for c in password) and
                any(c.islower() for c in password) and
                any(c.isdigit() for c in password) and
                any(c in '!@#$%^&*' for c in password)):
            return password


def update_env_file(env_file, secrets_dict):
    """Update the environment file with generated secrets."""
    # Create the file if it doesn't exist
    if not os.path.exists(env_file):
        print(f"Creating new .env file at {env_file}")
        with open(env_file, 'w') as f:
            f.write("# Social Cube Environment Configuration\n\n")
    
    # Read the existing file
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Update each secret
    for key, value in secrets_dict.items():
        # Check if the key already exists
        pattern = re.compile(f"^{key}=.*$", re.MULTILINE)
        if pattern.search(content):
            # Replace the existing value
            content = pattern.sub(f"{key}={value}", content)
            print(f"Updated {key} in {env_file}")
        else:
            # Add the new key-value pair
            content += f"\n# Added by generate_secrets.py\n{key}={value}\n"
            print(f"Added {key} to {env_file}")
    
    # Write back to the file
    with open(env_file, 'w') as f:
        f.write(content)


def main():
    """Main function to parse arguments and generate secrets."""
    parser = argparse.ArgumentParser(description="Generate secure secrets for production environment")
    parser.add_argument("--env-file", dest="env_file", default=".env",
                        help="Path to the .env file (default: .env)")
    parser.add_argument("--secret-key", dest="secret_key", action="store_true",
                        help="Generate a new Django SECRET_KEY")
    parser.add_argument("--db-password", dest="db_password", action="store_true",
                        help="Generate a new database password")
    parser.add_argument("--superuser-password", dest="superuser_password", action="store_true",
                        help="Generate a new superuser password")
    parser.add_argument("--all", dest="all", action="store_true",
                        help="Generate all secrets")
    
    args = parser.parse_args()
    
    # Resolve the .env file path
    env_file = Path(args.env_file).resolve()
    
    # Initialize the secrets dictionary
    secrets_dict = {}
    
    # Generate the requested secrets
    if args.secret_key or args.all:
        secrets_dict["SECRET_KEY"] = generate_django_secret_key()
    
    if args.db_password or args.all:
        secrets_dict["DB_PASSWORD"] = generate_password()
    
    if args.superuser_password or args.all:
        secrets_dict["DJANGO_SUPERUSER_PASSWORD"] = generate_password()
    
    # Check if any secrets were generated
    if not secrets_dict:
        parser.print_help()
        print("\nNo secrets were generated. Please specify which secrets to generate.")
        return
    
    # Update the .env file
    update_env_file(env_file, secrets_dict)
    
    print(f"\nAll secrets have been generated and saved to {env_file}")
    
    # Give the user a final reminder
    if "DJANGO_SUPERUSER_PASSWORD" in secrets_dict:
        print("\nIMPORTANT: For security, do not share or commit these passwords to version control.")


if __name__ == "__main__":
    main()