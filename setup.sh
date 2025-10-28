#!/bin/bash

# Medical Document RAG System - Setup Script
# This script sets up the development environment

set -e  # Exit on error

echo "🏥 Medical Document RAG System - Setup"
echo "======================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo -e "${RED}❌ Python $required_version or higher is required. Found: $python_version${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python $python_version detected${NC}"
echo ""

# Check for system dependencies
echo "📦 Checking system dependencies..."

# Check for Tesseract
if ! command -v tesseract &> /dev/null; then
    echo -e "${YELLOW}⚠️  Tesseract OCR not found${NC}"
    echo "Please install Tesseract:"
    echo "  Ubuntu/Debian: sudo apt-get install tesseract-ocr"
    echo "  macOS: brew install tesseract"
    echo "  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki"
else
    echo -e "${GREEN}✅ Tesseract OCR found${NC}"
fi

# Check for Poppler
if ! command -v pdftoimage &> /dev/null && ! command -v pdftoppm &> /dev/null; then
    echo -e "${YELLOW}⚠️  Poppler utilities not found${NC}"
    echo "Please install Poppler:"
    echo "  Ubuntu/Debian: sudo apt-get install poppler-utils"
    echo "  macOS: brew install poppler"
    echo "  Windows: Download from https://github.com/oschwartz10612/poppler-windows/releases/"
else
    echo -e "${GREEN}✅ Poppler utilities found${NC}"
fi
echo ""

# Create virtual environment
echo "🐍 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${YELLOW}ℹ️  Virtual environment already exists${NC}"
fi
echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✅ Pip upgraded${NC}"
echo ""

# Install requirements
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p uploads
mkdir -p reports
mkdir -p data/chroma
mkdir -p data/sessions
mkdir -p logs
mkdir -p agents
mkdir -p services
mkdir -p backend

# Create __init__.py files
touch agents/__init__.py
touch services/__init__.py
touch backend/__init__.py

echo -e "${GREEN}✅ Directory structure created${NC}"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "🔐 Creating .env file..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env and add your OPENAI_API_KEY${NC}"
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi
echo ""

# Check for OpenAI API key
if [ -f ".env" ]; then
    if grep -q "your_openai_api_key_here" .env; then
        echo -e "${RED}❌ Please set your OPENAI_API_KEY in .env file${NC}"
    else
        echo -e "${GREEN}✅ OPENAI_API_KEY is configured${NC}"
    fi
fi
echo ""

echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your OPENAI_API_KEY"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Start backend: uvicorn backend.main:app --reload"
echo "4. Start frontend: streamlit run app.py"
echo ""
echo "Or use Docker:"
echo "  docker-compose up --build"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"