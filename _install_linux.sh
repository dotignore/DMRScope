#!/bin/bash

##############################################################
# DMRScope Installation Script for Linux
##############################################################
# This script sets up the environment for running DMRScope
# It will:
# - Check if Python 3 is installed
# - Install pip3 if needed
# - Create a virtual environment (venv)
# - Activate the virtual environment
# - Install all required packages from requirements.txt
# - Set executable permissions on shell scripts
##############################################################

set -e

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║        DMRScope - Linux Installation Script           ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python 3 is installed
echo "[*] Checking if Python 3 is installed..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python 3 is not installed!${NC}"
    echo "[INFO] Installing Python 3..."
    
    # Try to detect the package manager and install Python
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3 python3-pip
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y python3 python3-pip
    elif command -v pacman &> /dev/null; then
        sudo pacman -S --noconfirm python
    else
        echo -e "${RED}[ERROR] Could not detect package manager${NC}"
        echo "[INFO] Please install Python 3 manually from your distribution"
        exit 1
    fi
fi

python3 --version
echo -e "${GREEN}[OK] Python 3 found!${NC}"
echo ""

# Check if pip3 is installed
echo "[*] Checking if pip3 is installed..."
if ! command -v pip3 &> /dev/null; then
    echo "[INFO] Installing pip3..."
    sudo apt-get install -y python3-pip
fi

pip3 --version
echo -e "${GREEN}[OK] pip3 found!${NC}"
echo ""

# Check if venv directory already exists
if [ -d "venv" ]; then
    echo "[*] Virtual environment already exists. Skipping creation..."
    echo ""
else
    echo "[*] Creating virtual environment..."
    python3 -m venv venv
    
    if [ ! -d "venv" ]; then
        echo -e "${RED}[ERROR] Failed to create virtual environment!${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}[OK] Virtual environment created!${NC}"
    echo ""
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

# Upgrade pip
echo "[*] Upgrading pip..."
python3 -m pip install --upgrade pip
echo ""

# Install required packages
echo "[*] Installing required packages from requirements.txt..."
echo "[*] This may take several minutes..."
echo ""

pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to install requirements!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}[OK] All packages installed successfully!${NC}"
echo ""

# Set executable permissions on shell scripts
echo "[*] Setting executable permissions on shell scripts..."
chmod +x run_linux.sh 2>/dev/null || true
chmod +x install_linux.sh 2>/dev/null || true
echo -e "${GREEN}[OK] Permissions set!${NC}"
echo ""

# Deactivate venv after installation
echo "[*] Virtual environment will be activated automatically when you run run_linux.sh"
echo ""

echo "╔════════════════════════════════════════════════════════╗"
echo "║     Installation Complete!                            ║"
echo "║                                                        ║"
echo "║  To start the application, run:                       ║"
echo "║  - ./run_linux.sh                                     ║"
echo "║  - Or: bash run_linux.sh                              ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

exit 0
