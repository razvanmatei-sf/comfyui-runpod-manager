#!/bin/bash
set -e

cd /workspace

if [ -d "ComfyUI" ] && [ -f ".comfyui-status/comfyui_install_status" ]; then
    echo "ComfyUI already installed"
    exit 0
fi

echo "Installing ComfyUI..."
git clone https://github.com/comfyanonymous/ComfyUI.git

cd ComfyUI
python3.11 -m venv .venv
source .venv/bin/activate

pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu129
pip install -r requirements.txt

mkdir -p /workspace/.comfyui-status
echo "COMPLETED" > /workspace/.comfyui-status/comfyui_install_status

echo "ComfyUI installed"
