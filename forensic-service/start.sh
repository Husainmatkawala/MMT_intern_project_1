#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Forensic Service Startup Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to create virtual environment${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install dependencies${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found. Using default configuration.${NC}"
    echo -e "${YELLOW}Create a .env file with your MongoDB URI if needed.${NC}"
fi

# Start the service
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Starting Forensic Service...${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

python app.py
