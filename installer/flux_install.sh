#!/bin/bash
set -e

MODELS_DIR="/workspace/ComfyUI/models"

# Create directories if they don't exist
mkdir -p "$MODELS_DIR/diffusion_models"
mkdir -p "$MODELS_DIR/text_encoders"
mkdir -p "$MODELS_DIR/clip_vision"
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

echo "=== Installing Flux Models ==="

# Diffusion Models
echo "→ Diffusion Models"
download_model "https://huggingface.co/Comfy-Org/flux1-dev/resolve/main/flux1-dev.safetensors" "$MODELS_DIR/diffusion_models"
download_model "https://huggingface.co/Comfy-Org/flux1-kontext-dev_ComfyUI/resolve/main/split_files/diffusion_models/flux1-dev-kontext_fp8_scaled.safetensors" "$MODELS_DIR/diffusion_models"
download_model "https://huggingface.co/black-forest-labs/FLUX.1-Fill-dev/resolve/main/flux1-fill-dev.safetensors" "$MODELS_DIR/diffusion_models"
download_model "https://huggingface.co/Comfy-Org/Flux1-Redux-Dev/resolve/main/flux1-redux-dev.safetensors" "$MODELS_DIR/diffusion_models"
download_model "https://huggingface.co/Comfy-Org/FLUX.1-Krea-dev_ComfyUI/resolve/main/split_files/diffusion_models/flux1-krea-dev_fp8_scaled.safetensors" "$MODELS_DIR/diffusion_models"
download_model "https://huggingface.co/black-forest-labs/FLUX.1-Krea-dev/resolve/main/flux1-krea-dev.safetensors" "$MODELS_DIR/diffusion_models"

# Text Encoders
echo "→ Text Encoders"
download_model "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors" "$MODELS_DIR/text_encoders"
download_model "https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp8_e4m3fn_scaled.safetensors" "$MODELS_DIR/text_encoders"

# CLIP Vision
echo "→ CLIP Vision"
download_model "https://huggingface.co/Comfy-Org/sigclip_vision_384/resolve/main/sigclip_vision_patch14_384.safetensors" "$MODELS_DIR/clip_vision"

# VAE
echo "→ VAE"
download_model "https://huggingface.co/Comfy-Org/Lumina_Image_2.0_Repackaged/resolve/main/split_files/vae/ae.safetensors" "$MODELS_DIR/vae"

echo "=== Flux models installation complete ==="