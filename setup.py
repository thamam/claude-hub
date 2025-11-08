"""Setup script for Claude Code Conductor."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="claude-code-conductor",
    version="0.1.0",
    description="Orchestrate and enhance Claude Code sessions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Claude Code Community",
    url="https://github.com/thamam/claude-hub",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click>=8.1.0",
        "rich>=13.0.0",
        "pyyaml>=6.0",
        "pyperclip>=1.8.2",
    ],
    entry_points={
        'console_scripts': [
            'conductor=conductor.cli:cli',
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
)
