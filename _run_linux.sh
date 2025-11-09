#!/bin/bash

##############################################################
# DMRScope - Linux Launch Script
##############################################################
# This script activates the virtual environment and runs run.py
##############################################################

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║          DMRScope - Starting Application              ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${RED}[ERROR] Virtual environment not found!${NC}"
    echo "[INFO] Please run ./install_linux.sh first"
    echo ""
    exit 1
fi

# Activate virtual environment
echo "[*] Activating virtual environment..."
source venv/bin/activate

if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}[ERROR] Failed to activate virtual environment!${NC}"
    exit 1
fi

echo -e "${GREEN}[OK] Virtual environment activated!${NC}"
echo ""

# Check if run.py exists
if [ ! -f "run.py" ]; then
    echo -e "${RED}[ERROR] run.py not found!${NC}"
    echo "[INFO] Make sure you are in the correct directory"
    echo ""
    exit 1
fi

# Run the application
echo "[*] Starting DMRScope..."
echo ""
python3 run.py

# If the script exits, show a message
echo ""
echo -e "${GREEN}[*] Application closed${NC}"
echo ""

exit 0
