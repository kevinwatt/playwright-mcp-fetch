#!/usr/bin/env python3
"""Setup script for playwright-mcp-fetch."""

from setuptools import setup, find_packages

# Read the contents of README.md
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

# Read the requirements
with open("requirements.txt", encoding="utf-8") as f:
    requirements = f.read().splitlines()

setup(
    name="playwright-mcp-fetch",
    version="0.1.1",
    description="A MCP server with playwright fetch tools",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Kevin Watt",
    author_email="",
    url="https://github.com/kevinwatt/playwright-mcp-fetch",
    packages=find_packages(),
    install_requires=requirements,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "playwright-mcp-fetch=playwright_mcp_fetch.index:main",
            "playwright-mcp-fetch-sse=playwright_mcp_fetch.server:main",
        ],
    },
) 