#!/bin/bash
# ============================================================
# Data Octopus - Mac/Linux Installer
# v5.2.0 - Professional Dashboard mit Manifold Integration
# ============================================================

echo ""
echo "========================================"
echo "  DATA OCTOPUS - Installation"
echo "  Version 5.2.0"
echo "========================================"
echo ""

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON=python
else
    echo "[ERROR] Python nicht gefunden!"
    echo ""
    echo "Bitte Python 3.10+ installieren:"
    echo "  Mac:   brew install python@3.13"
    echo "  Linux: sudo apt install python3 python3-pip python3-tk"
    echo ""
    exit 1
fi

echo "[OK] Python gefunden: $($PYTHON --version)"

# Check tkinter
$PYTHON -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[WARNUNG] tkinter nicht gefunden!"
    echo ""
    echo "tkinter installieren:"
    echo "  Mac:   brew install python-tk@3.13"
    echo "  Linux: sudo apt install python3-tk"
    echo ""
fi

# Create virtual environment
echo ""
echo "Erstelle virtuelle Umgebung..."
$PYTHON -m venv venv

# Activate venv
source venv/bin/activate

# Install dependencies
echo "Installiere Abhängigkeiten..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "========================================"
echo "  Installation abgeschlossen!"
echo "========================================"
echo ""
echo "Starten mit:"
echo "  ./run.sh"
echo ""
echo "Oder manuell:"
echo "  source venv/bin/activate"
echo "  python main_v5.1.py"
echo ""
