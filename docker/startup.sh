#!/bin/bash

echo "Configuring Jupyter for passwordless access..."

# Create Jupyter config directory
mkdir -p ~/.jupyter

# Generate Jupyter config without password
cat > ~/.jupyter/jupyter_notebook_config.py << 'EOF'
c.NotebookApp.token = ''
c.NotebookApp.password = ''
c.NotebookApp.allow_origin = '*'
c.NotebookApp.allow_remote_access = True
c.NotebookApp.ip = '0.0.0.0'
c.NotebookApp.port = 8888
c.NotebookApp.open_browser = False
c.NotebookApp.notebook_dir = '/workspace'
EOF

echo "Starting Jupyter and other services..."

# Start Jupyter manually with our config
nohup jupyter lab --config=~/.jupyter/jupyter_notebook_config.py > /var/log/jupyter.log 2>&1 &

# Start other RunPod services if available
if [ -f "/start.sh" ]; then
    # Skip jupyter in the default start script since we're starting it manually
    sed 's/jupyter/#jupyter/g' /start.sh > /tmp/start_no_jupyter.sh
    chmod +x /tmp/start_no_jupyter.sh
    /tmp/start_no_jupyter.sh &
elif [ -f "/usr/local/bin/start.sh" ]; then
    sed 's/jupyter/#jupyter/g' /usr/local/bin/start.sh > /tmp/start_no_jupyter.sh
    chmod +x /tmp/start_no_jupyter.sh
    /tmp/start_no_jupyter.sh &
fi

# Wait a moment for services to initialize
sleep 5

echo "Starting ComfyUI Admin/Artist Interface..."

mkdir -p /workspace/output
mkdir -p /workspace/.comfyui-status
mkdir -p /app/static

echo "Checking workspace directories..."
ls -la /workspace/

echo "Setting up environment..."
export PYTHONPATH=/app:$PYTHONPATH
export FLASK_APP=enhanced_artist_server.py
export FLASK_ENV=production

echo "Starting Flask server on port 8080..."
cd /app
python3 enhanced_artist_server.py