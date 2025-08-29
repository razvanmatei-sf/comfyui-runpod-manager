#!/bin/bash
set -e

MODELS_DIR="/workspace/ComfyUI/models"

# Create directories if they don't exist
mkdir -p "$MODELS_DIR/diffusion_models"
mkdir -p "$MODELS_DIR/text_encoders"
mkdir -p "$MODELS_DIR/controlnet"
mkdir -p "$MODELS_DIR/loras"
mkdir -p "$MODELS_DIR/vae"

# Function to download model if it doesn't exist
download_model() {
    local url="$1"
    local dest_dir="$2"
    local filename=$(basename "$url")
    local filepath="$dest_dir/$filename"
    
    if [ -f "$filepath" ]; then
        echo "✓ $filename already exists, skipping"
    else
        echo "↓ Downloading $filename..."
        wget -c "$url" -O "$filepath"
    fi
}

echo "=== Installing Qwen Models ==="

# Diffusion Models
echo "→ Diffusion Models"
download_model "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_fp8_e4m3fn.safetensors" "$MODELS_DIR/diffusion_models"
download_model "https://huggingface.co/Comfy-Org/Qwen-Image-Edit_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_edit_fp8_e4m3fn.safetensors" "$MODELS_DIR/diffusion_models"

# ControlNet
echo "→ ControlNet"
download_model "https://huggingface.co/Comfy-Org/Qwen-Image-InstantX-ControlNets/resolve/main/split_files/controlnet/Qwen-Image-InstantX-ControlNet-Union.safetensors" "$MODELS_DIR/controlnet"

# LoRA
echo "→ LoRA"
download_model "https://huggingface.co/lightx2v/Qwen-Image-Lightning/resolve/main/Qwen-Image-Lightning-4steps-V1.0.safetensors" "$MODELS_DIR/loras"

# Text Encoders
echo "→ Text Encoders"
download_model "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors" "$MODELS_DIR/text_encoders"

# VAE
echo "→ VAE"
download_model "https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors" "$MODELS_DIR/vae"

echo "=== Qwen models installation complete ==="