#!/usr/bin/env python
"""Setup script for Social Cube project."""

from setuptools import setup, find_packages

setup(
    name="social_cube",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Django>=4.2.0",
        "python-dotenv>=1.0.0",
        "discord.py>=2.3.0",
        "requests>=2.31.0",
        "python-jose>=3.3.0",
        "cryptography>=41.0.0",
        "django-crispy-forms>=2.0",
        "crispy-bootstrap5>=0.7",
        "whitenoise>=6.5.0",
        "gunicorn>=21.2.0",
        "psycopg2-binary>=2.9.9",
        "django-environ>=0.11.2",
        "django-cors-headers>=4.3.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 4.2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    description="A Django application for managing Discord bots.",
    author="Social Cube Team",
    author_email="admin@example.com",
    url="https://github.com/yourusername/social_cube",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/social_cube/issues",
        "Documentation": "https://github.com/yourusername/social_cube",
        "Source Code": "https://github.com/yourusername/social_cube",
    },
    python_requires=">=3.11",
)