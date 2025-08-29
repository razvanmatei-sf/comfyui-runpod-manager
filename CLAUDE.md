# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ComfyUI RunPod Manager - A Flask-based admin/artist interface for managing ComfyUI installations on RunPod containers with GitHub integration for automated setup.

### Key Components
- **Flask Admin Interface** (`docker/enhanced_artist_server.py`): 1400+ line Flask app with dual-mode interface
- **Installation Scripts** (`installer/`): Bash scripts for ComfyUI, models, and custom nodes installation
- **Docker Setup** (`docker/`): Docker configuration for RunPod deployment

## Development Commands

### Docker Build & Deploy
```bash
# Build Docker image for RunPod (linux/amd64)
cd docker
chmod +x build.sh
./build.sh

# The build.sh script uses buildx to build and push in one step:
# docker buildx build --platform linux/amd64 -t ghcr.io/razvanmatei-sf/comfyui-admin:latest --push .

# Local testing
docker run -d \
  -p 8080:8080 \
  -p 8188:8188 \
  -p 8888:8888 \
  -v $(pwd)/test-workspace:/workspace \
  ghcr.io/razvanmatei-sf/comfyui-admin:latest
```

### GitHub Repository Management
```bash
# GitHub Container Registry login (required before building)
echo YOUR_GITHUB_TOKEN | docker login ghcr.io -u razvanmatei-sf --password-stdin

# Push installation scripts to GitHub
git add .
git commit -m "Update installation scripts"
git push origin main

# The Flask app pulls scripts from:
# https://github.com/razvanmatei-sf/comfyui-runpod-manager
```

## Architecture

### Directory Structure
```
comfyui-runpod-project/
├── docker/                      # Flask app and Docker setup
│   ├── enhanced_artist_server.py # Main Flask application
│   ├── Dockerfile               # RunPod-compatible Docker config
│   ├── build.sh                 # Build and push script
│   └── requirements.txt         # Python dependencies
└── installer/                   # Installation scripts
    ├── comfyui_install.sh       # Base ComfyUI installation
    ├── flux_install.sh          # Flux model bundle
    └── qwen_install.sh          # Qwen model bundle
```

### Flask Application (`docker/enhanced_artist_server.py`)

**Dual-Mode Interface:**
- **Artist Mode**: Session management for ComfyUI/Jupyter with artist selection
- **Admin Mode**: Password-protected installation management (password: `admin`)

**Key Functions:**
- `parse_models_from_script()`: Dynamically extracts available models from install scripts
- `parse_nodes_from_script()`: Extracts custom nodes from installation scripts
- `install_individual_models()`: Downloads specific models with progress tracking
- `install_individual_nodes()`: Installs selected custom nodes with venv activation
- `start_session()`: Launches ComfyUI and Jupyter processes

**GitHub Integration:**
- Pulls scripts from `https://github.com/razvanmatei-sf/comfyui-runpod-manager`
- Dynamic parsing for individual component selection
- Real-time terminal output streaming

**Recent Updates:**
- Removed bulky status cards for cleaner UI
- Added expandable individual selection for both Models and Custom Nodes
- GitHub integration for dynamic script parsing
- Green checkmark styling for installed components
- Fixed checkbox persistence issues

### Installation Scripts

**Model Download Pattern:**
```bash
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
```

**ComfyUI Directory Structure:**
```
/workspace/ComfyUI/models/
├── diffusion_models/    # Main model files
├── text_encoders/       # CLIP, T5 encoders
├── clip_vision/         # CLIP vision models
├── vae/                 # VAE models
├── checkpoints/         # SD-style checkpoints
├── loras/              # LoRA models
├── controlnet/         # ControlNet models
└── upscale_models/     # Upscaling models
```

## Critical Implementation Details

### Virtual Environment Management
- ComfyUI uses `.venv` in `/workspace/ComfyUI/.venv`
- ALL pip installations for custom nodes MUST activate this venv first:
  ```bash
  source /workspace/ComfyUI/.venv/bin/activate
  pip install -r requirements.txt
  ```

### Status Tracking
- Installation status stored in `/workspace/.comfyui-status/`
- JSON files track individual component installation
- Green checkmarks display for installed components in UI

### Docker Configuration
- **Base Image**: `runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04`
- **Registry**: GitHub Container Registry (`ghcr.io/razvanmatei-sf/comfyui-admin:latest`)
- **Ports**: 8080 (web admin), 8188 (ComfyUI), 8888 (Jupyter)
- **Build Platform**: linux/amd64 (required for RunPod)

### RunPod Specifics
- Working directory: `/workspace` (persistent network volume)
- Proxy URLs generated for RunPod environment
- Sessions start ComfyUI and Jupyter independently
- No fuser dependency required

### Security
- Admin password: `admin` (SHA256 hashed)
- Session management via Flask sessions
- Input sanitization for subprocess execution
- Read-only GitHub script fetching with timeout protection
- 30-minute timeout for large model downloads

## Testing Considerations

- Model downloads can take 30+ minutes for large files
- Virtual environment activation is critical for custom node dependencies
- GitHub rate limiting may affect dynamic script parsing
- RunPod proxy URLs differ from local development URLs
- Always test with linux/amd64 platform for RunPod compatibility