#!/bin/bash

# Quick setup script for arXiv Newsletter

echo "Setting up arXiv Newsletter..."
echo

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install package
echo "Installing package and dependencies..."
pip install -e .

# Create config if it doesn't exist
if [ ! -f "config.yaml" ]; then
    echo "Creating config.yaml from template..."
    cp config.example.yaml config.yaml
    echo
    echo "⚠️  Please edit config.yaml to add your authors, categories, and keywords!"
else
    echo "config.yaml already exists, skipping..."
fi

# Create output directory
mkdir -p newsletters

echo
echo "✓ Setup complete!"
echo
echo "Next steps:"
echo "  1. Edit config.yaml with your preferences"
echo "  2. Run: arxiv-newsletter"
echo
echo "To activate the virtual environment in future sessions:"
echo "  source venv/bin/activate"
