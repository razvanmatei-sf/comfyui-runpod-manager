#!/usr/bin/env python3

import os
import json
import hashlib
import subprocess
import time
import threading
import requests
import signal
import sys
import queue
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify, session

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Global variables
artist_name = None
comfyui_process = None
jupyter_process = None
session_start_time = None
comfyui_ready = False
installation_in_progress = False
current_process = None
output_queue = queue.Queue()

# Configuration
ADMIN_PASSWORD_HASH = hashlib.sha256('admin'.encode()).hexdigest()
WORKSPACE_DIR = '/workspace'
OUTPUT_DIR = f'{WORKSPACE_DIR}/output'
STATUS_DIR = f'{WORKSPACE_DIR}/.comfyui-status'
GITHUB_REPO = 'https://github.com/razvanmatei-sf/comfyui-runpod-manager'

# Combined interface template
MAIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ComfyUI Studio</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #333;
        }
        
        .container { 
            background: white;
            padding: 3rem;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            max-width: 800px;
            width: 95%;
            text-align: center;
            min-height: 500px;
        }
        
        h1 { 
            color: #333;
            margin-bottom: 0.5rem;
            font-size: 2.5rem;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 2rem;
            font-size: 1.1rem;
        }
        
        select, input, button { 
            width: 100%;
            padding: 15px 20px;
            margin: 10px 0;
            border-radius: 10px;
            font-size: 16px;
            transition: all 0.3s ease;
        }
        
        select, input {
            border: 2px solid #e0e0e0;
            background: white;
        }
        
        select:focus, input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        button { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            cursor: pointer;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        .mode-selector {
            margin: 20px 0;
        }
        
        #password-prompt {
            display: none;
            margin: 20px 0;
        }
        
        /* Artist Panel */
        .artist-panel {
            display: none;
            margin-top: 2rem;
        }
        
        .session-section {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 2rem;
            margin-top: 2rem;
        }
        
        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 0.75rem 0;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .info-row:last-child {
            border-bottom: none;
        }
        
        .info-label {
            color: #666;
            font-weight: 500;
        }
        
        .info-value {
            color: #333;
            font-weight: 600;
        }
        
        .service-links {
            display: grid;
            gap: 1rem;
            margin-top: 1.5rem;
        }
        
        .service-link {
            display: block;
            padding: 1rem;
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            text-decoration: none;
            color: #333;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .service-link:hover:not(.inactive) {
            border-color: #667eea;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .service-link.ready {
            border-color: #4caf50;
            background: #f1f8e9;
        }
        
        .service-link.waiting {
            border-color: #ff9800;
            background: #fff3e0;
        }
        
        .service-link.inactive {
            background: #f5f5f5;
            color: #999;
            cursor: not-allowed;
            opacity: 0.7;
        }
        
        /* Admin Panel */
        .admin-panel {
            display: none;
            margin-top: 2rem;
        }
        
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .status-card {
            background: #f7fafc;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
            transition: all 0.3s ease;
        }
        
        .status-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-color: #667eea;
        }
        
        .status-card h3 {
            margin: 0 0 15px 0;
            color: #4a5568;
            font-size: 1.1rem;
            font-weight: 600;
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
        }
        
        .status-installed {
            background: #48bb78;
            box-shadow: 0 0 0 3px rgba(72, 187, 120, 0.2);
        }
        
        .status-not-installed {
            background: #f56565;
            box-shadow: 0 0 0 3px rgba(245, 101, 101, 0.2);
        }
        
        .status-installing {
            background: #f6ad55;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(246, 173, 85, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(246, 173, 85, 0); }
            100% { box-shadow: 0 0 0 0 rgba(246, 173, 85, 0); }
        }
        
        .installation-options {
            background: linear-gradient(145deg, #edf2f7, #e2e8f0);
            padding: 25px;
            border-radius: 12px;
            margin: 25px 0;
            border: 1px solid #cbd5e0;
        }
        
        .checkbox-group {
            display: flex;
            flex-direction: column;
            gap: 15px;
            margin: 20px 0;
        }
        
        .checkbox-item {
            display: flex;
            align-items: center;
            padding: 10px;
            border-radius: 8px;
            transition: background-color 0.3s;
        }
        
        .checkbox-item:hover {
            background: rgba(102, 126, 234, 0.05);
        }
        
        .checkbox-item input[type="checkbox"] {
            width: 18px;
            height: 18px;
            margin-right: 12px;
            cursor: pointer;
            accent-color: #667eea;
        }
        
        .checkbox-item label {
            font-weight: 500;
            cursor: pointer;
            user-select: none;
            width: 100%;
            margin: 0;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .checkmark {
            color: #4caf50;
            font-weight: bold;
            font-size: 1.2em;
            display: none;
        }
        
        .checkmark.installed {
            display: inline;
        }
        
        .checkbox-item.installed {
            background: #e8f5e8;
            border: 1px solid #4caf50;
        }
        
        .checkbox-item.installed input[type="checkbox"] {
            display: none;
        }
        
        .node-expansion, .model-expansion {
            margin-top: 15px;
            padding: 15px;
            background: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        
        .node-list, .model-list {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .individual-node, .individual-model {
            display: flex;
            align-items: center;
            padding: 8px 12px;
            margin: 5px 0;
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            transition: all 0.2s ease;
        }
        
        .individual-node:hover, .individual-model:hover {
            background: #f0f0f0;
            border-color: #667eea;
        }
        
        .individual-node input[type="checkbox"], .individual-model input[type="checkbox"] {
            margin-right: 10px;
        }
        
        .loading {
            text-align: center;
            color: #666;
            font-style: italic;
            padding: 20px;
        }
        
        .terminal {
            background: #1a202c;
            color: #68d391;
            padding: 20px;
            border-radius: 12px;
            font-family: 'Monaco', 'Consolas', 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.4;
            height: 300px;
            overflow-y: auto;
            margin: 20px 0;
            border: 2px solid #2d3748;
        }
        
        .terminal-line {
            margin: 3px 0;
            word-wrap: break-word;
        }
        
        .terminate-btn {
            background: #f44336 !important;
            margin-top: 2rem;
        }
        
        .terminate-btn:hover:not(:disabled) {
            box-shadow: 0 5px 15px rgba(244, 67, 54, 0.4) !important;
        }
        
        .alert {
            padding: 15px 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid;
            font-weight: 500;
        }
        
        .alert-info {
            background: #bee3f8;
            color: #2c5282;
            border-left-color: #3182ce;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 ComfyUI Studio</h1>
        <p class="subtitle">Select your mode to begin</p>
        
        <div class="mode-selector">
            <select id="mode" onchange="handleModeChange()">
                <option value="">-- Select Mode --</option>
                {% if artists %}
                    {% for artist in artists %}
                        <option value="artist:{{ artist }}">Artist: {{ artist }}</option>
                    {% endfor %}
                {% endif %}
                <option value="admin">Admin Mode</option>
            </select>
        </div>
        
        <div id="password-prompt">
            <input type="password" id="password" placeholder="Enter admin password" autocomplete="off">
            <button onclick="authenticate()">Login</button>
        </div>
        
        <!-- Artist Panel -->
        <div id="artist-panel" class="artist-panel">
            <div class="session-section">
                <div class="info-row">
                    <span class="info-label">Active Artist:</span>
                    <span class="info-value" id="activeArtist">Not Selected</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Session Time:</span>
                    <span class="info-value" id="sessionTime">--:--</span>
                </div>
                
                <div class="service-links">
                    <a href="#" class="service-link inactive" id="comfyLink" onclick="handleComfyClick(event)">
                        <strong>ComfyUI</strong>
                        <span id="comfyStatus"> - Click "Start Session" first</span>
                    </a>
                    <a href="#" class="service-link inactive" id="jupyterLink">
                        <strong>Jupyter Lab</strong>
                        <span id="jupyterStatus"> - Click "Start Session" first</span>
                    </a>
                </div>
                
                <button id="startBtn" onclick="startSession()">
                    Start My Session
                </button>
                
                <button class="terminate-btn" onclick="terminateRunPod()">
                    Terminate RunPod Instance
                </button>
            </div>
        </div>
        
        <!-- Admin Panel -->
        <div id="admin-panel" class="admin-panel">
            
            <div class="installation-options">
                <h3>Installation Options</h3>
                <div class="checkbox-group">
                    <div class="checkbox-item">
                        <input type="checkbox" id="install-comfyui">
                        <label for="install-comfyui">
                            <span class="checkbox-label">Install ComfyUI</span>
                            <span class="checkmark" id="comfyui-checkmark">✓</span>
                        </label>
                    </div>
                    <div class="checkbox-item">
                        <input type="checkbox" id="install-models" onchange="toggleModelExpansion()">
                        <label for="install-models">
                            <span class="checkbox-label">Install Models</span>
                            <span class="checkmark" id="models-checkmark">✓</span>
                        </label>
                    </div>
                    
                    <!-- Expandable model list -->
                    <div class="model-expansion" id="model-expansion" style="display: none;">
                        <div class="model-list" id="individual-models">
                            <div class="loading">Loading available models...</div>
                        </div>
                    </div>
                    <div class="checkbox-item">
                        <input type="checkbox" id="install-nodes" onchange="toggleNodeExpansion()">
                        <label for="install-nodes">
                            <span class="checkbox-label">Install Custom Nodes</span>
                            <span class="checkmark" id="nodes-checkmark">✓</span>
                        </label>
                    </div>
                    
                    <!-- Expandable node list -->
                    <div class="node-expansion" id="node-expansion" style="display: none;">
                        <div class="node-list" id="individual-nodes">
                            <div class="loading">Loading available nodes...</div>
                        </div>
                    </div>
                </div>
                <button id="install-btn" onclick="startInstallation()">
                    Start Installation
                </button>
                <button onclick="checkStatus()">
                    Refresh Status
                </button>
            </div>
            
            <div class="terminal" id="terminal">
                <div>Terminal output will appear here...</div>
            </div>
            
            <button class="terminate-btn" onclick="terminateRunPod()">
                Terminate RunPod Instance
            </button>
        </div>
    </div>
    
    <script>
        let isAuthenticated = false;
        let sessionStartTime = null;
        let timerInterval = null;
        let checkInterval = null;
        let sessionActive = false;
        let terminalCheckInterval = null;
        
        function handleModeChange() {
            const mode = document.getElementById('mode').value;
            const passwordPrompt = document.getElementById('password-prompt');
            const adminPanel = document.getElementById('admin-panel');
            const artistPanel = document.getElementById('artist-panel');
            
            // Hide all panels
            passwordPrompt.style.display = 'none';
            adminPanel.style.display = 'none';
            artistPanel.style.display = 'none';
            
            if (mode === 'admin') {
                if (!isAuthenticated) {
                    passwordPrompt.style.display = 'block';
                } else {
                    adminPanel.style.display = 'block';
                    checkStatus();
                    startTerminalCheck();
                }
            } else if (mode.startsWith('artist:')) {
                const artist = mode.split(':')[1];
                document.getElementById('activeArtist').textContent = artist;
                artistPanel.style.display = 'block';
            }
        }
        
        function authenticate() {
            const password = document.getElementById('password').value;
            
            fetch('/authenticate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({password: password})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    isAuthenticated = true;
                    document.getElementById('password-prompt').style.display = 'none';
                    document.getElementById('admin-panel').style.display = 'block';
                    checkStatus();
                    startTerminalCheck();
                } else {
                    alert('Invalid password');
                }
            });
        }
        
        function checkStatus() {
            fetch('/check_status')
            .then(response => response.json())
            .then(data => {
                // Update checkbox styles for installed components
                updateComponentStatus('comfyui', data.comfyui);
                updateComponentStatus('models', data.models);
                updateComponentStatus('nodes', data.nodes);
                
                // Load available nodes if not already loaded
                if (!document.getElementById('individual-nodes').dataset.loaded) {
                    loadAvailableNodes();
                }
                
                // Load available models if not already loaded
                if (!document.getElementById('individual-models').dataset.loaded) {
                    loadAvailableModels();
                }
            });
        }
        
        function updateComponentStatus(component, status) {
            const checkbox = document.getElementById('install-' + component);
            const checkboxItem = checkbox.parentElement.parentElement;
            const checkmark = document.getElementById(component + '-checkmark');
            
            if (status.installed) {
                checkboxItem.classList.add('installed');
                checkmark.classList.add('installed');
                checkbox.disabled = true;
                checkbox.checked = false;
            } else {
                checkboxItem.classList.remove('installed');
                checkmark.classList.remove('installed');
                checkbox.disabled = false;
            }
        }
        
        function toggleNodeExpansion() {
            const checkbox = document.getElementById('install-nodes');
            const expansion = document.getElementById('node-expansion');
            
            if (checkbox.checked) {
                expansion.style.display = 'block';
                // Load available nodes if not already loaded
                if (!document.getElementById('individual-nodes').dataset.loaded) {
                    loadAvailableNodes();
                }
                // Select all individual nodes
                setTimeout(() => {
                    const nodeCheckboxes = document.querySelectorAll('.individual-node input[type="checkbox"]');
                    nodeCheckboxes.forEach(cb => cb.checked = true);
                }, 100);
            } else {
                expansion.style.display = 'none';
                // Deselect all individual nodes
                const nodeCheckboxes = document.querySelectorAll('.individual-node input[type="checkbox"]');
                nodeCheckboxes.forEach(cb => cb.checked = false);
            }
        }
        
        function loadAvailableNodes() {
            fetch('/get_available_nodes')
            .then(response => response.json())
            .then(data => {
                const nodeList = document.getElementById('individual-nodes');
                nodeList.dataset.loaded = 'true';
                
                if (data.success && data.nodes.length > 0) {
                    nodeList.innerHTML = '';
                    data.nodes.forEach(node => {
                        const nodeDiv = document.createElement('div');
                        nodeDiv.className = 'individual-node';
                        nodeDiv.innerHTML = `
                            <input type="checkbox" id="node-${node.id}" value="${node.id}" onchange="updateMainNodeCheckbox()">
                            <label for="node-${node.id}">${node.name}</label>
                        `;
                        nodeList.appendChild(nodeDiv);
                    });
                } else {
                    nodeList.innerHTML = '<div class="loading">No nodes available or failed to load</div>';
                }
            })
            .catch(e => {
                document.getElementById('individual-nodes').innerHTML = '<div class="loading">Failed to load nodes</div>';
            });
        }
        
        function updateMainNodeCheckbox() {
            const nodeCheckboxes = document.querySelectorAll('.individual-node input[type="checkbox"]');
            const checkedNodes = document.querySelectorAll('.individual-node input[type="checkbox"]:checked');
            const mainCheckbox = document.getElementById('install-nodes');
            
            if (checkedNodes.length === 0) {
                mainCheckbox.checked = false;
            } else if (checkedNodes.length === nodeCheckboxes.length) {
                mainCheckbox.checked = true;
            }
        }
        
        function toggleModelExpansion() {
            const checkbox = document.getElementById('install-models');
            const expansion = document.getElementById('model-expansion');
            
            if (checkbox.checked) {
                expansion.style.display = 'block';
                // Load available models if not already loaded
                if (!document.getElementById('individual-models').dataset.loaded) {
                    loadAvailableModels();
                }
                // Select all individual models
                setTimeout(() => {
                    const modelCheckboxes = document.querySelectorAll('.individual-model input[type="checkbox"]');
                    modelCheckboxes.forEach(cb => cb.checked = true);
                }, 100);
            } else {
                expansion.style.display = 'none';
                // Deselect all individual models
                const modelCheckboxes = document.querySelectorAll('.individual-model input[type="checkbox"]');
                modelCheckboxes.forEach(cb => cb.checked = false);
            }
        }
        
        function loadAvailableModels() {
            fetch('/get_available_models')
            .then(response => response.json())
            .then(data => {
                const modelList = document.getElementById('individual-models');
                modelList.dataset.loaded = 'true';
                
                if (data.success && data.models.length > 0) {
                    modelList.innerHTML = '';
                    data.models.forEach(model => {
                        const modelDiv = document.createElement('div');
                        modelDiv.className = 'individual-model';
                        modelDiv.innerHTML = `
                            <input type="checkbox" id="model-${model.id}" value="${model.id}" onchange="updateMainModelCheckbox()">
                            <label for="model-${model.id}">${model.name} (${model.size})</label>
                        `;
                        modelList.appendChild(modelDiv);
                    });
                } else {
                    modelList.innerHTML = '<div class="loading">No models available or failed to load</div>';
                }
            })
            .catch(e => {
                document.getElementById('individual-models').innerHTML = '<div class="loading">Failed to load models</div>';
            });
        }
        
        function updateMainModelCheckbox() {
            const modelCheckboxes = document.querySelectorAll('.individual-model input[type="checkbox"]');
            const checkedModels = document.querySelectorAll('.individual-model input[type="checkbox"]:checked');
            const mainCheckbox = document.getElementById('install-models');
            
            if (checkedModels.length === 0) {
                mainCheckbox.checked = false;
            } else if (checkedModels.length === modelCheckboxes.length) {
                mainCheckbox.checked = true;
            }
        }
        
        function startInstallation() {
            // Get selected individual nodes
            const selectedNodes = [];
            const nodeCheckboxes = document.querySelectorAll('.individual-node input[type="checkbox"]:checked');
            nodeCheckboxes.forEach(cb => selectedNodes.push(cb.value));
            
            // Get selected individual models
            const selectedModels = [];
            const modelCheckboxes = document.querySelectorAll('.individual-model input[type="checkbox"]:checked');
            modelCheckboxes.forEach(cb => selectedModels.push(cb.value));
            
            const options = {
                comfyui: document.getElementById('install-comfyui').checked,
                models: document.getElementById('install-models').checked,
                nodes: document.getElementById('install-nodes').checked,
                individual_nodes: selectedNodes,
                individual_models: selectedModels
            };
            
            if (!options.comfyui && !options.models && !options.nodes) {
                alert('Please select at least one component to install');
                return;
            }
            
            document.getElementById('install-btn').disabled = true;
            document.getElementById('install-btn').textContent = 'Installing...';
            document.getElementById('terminal').innerHTML = '<div class="terminal-line">Starting installation...</div>';
            
            fetch('/install', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(options)
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success && data.message) {
                    alert(data.message);
                    document.getElementById('install-btn').disabled = false;
                    document.getElementById('install-btn').textContent = 'Start Installation';
                }
            });
        }
        
        function startTerminalCheck() {
            if (terminalCheckInterval) clearInterval(terminalCheckInterval);
            
            terminalCheckInterval = setInterval(() => {
                fetch('/terminal_output')
                .then(response => response.json())
                .then(data => {
                    if (data.output) {
                        const terminal = document.getElementById('terminal');
                        const lines = data.output.split('\\n');
                        lines.forEach(line => {
                            if (line.trim()) {
                                const lineDiv = document.createElement('div');
                                lineDiv.className = 'terminal-line';
                                lineDiv.textContent = line;
                                terminal.appendChild(lineDiv);
                            }
                        });
                        terminal.scrollTop = terminal.scrollHeight;
                    }
                    
                    if (data.installation_complete) {
                        document.getElementById('install-btn').disabled = false;
                        document.getElementById('install-btn').textContent = 'Start Installation';
                        checkStatus();
                    }
                })
                .catch(e => console.error('Terminal check failed:', e));
            }, 2000);
        }
        
        // Artist mode functions
        async function startSession() {
            const artistName = document.getElementById('activeArtist').textContent;
            if (!artistName || artistName === 'Not Selected') {
                alert('Please select an artist first');
                return;
            }
            
            document.getElementById('startBtn').disabled = true;
            document.getElementById('startBtn').textContent = 'Starting...';
            
            const response = await fetch('/start_session', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ artist_name: artistName })
            });
            
            const result = await response.json();
            if (result.success) {
                sessionActive = true;
                sessionStartTime = new Date();
                
                document.getElementById('startBtn').style.display = 'none';
                
                // Enable Jupyter immediately
                const runpodId = '{{ runpod_id }}';
                const jupyterUrl = `https://${runpodId}-8888.proxy.runpod.net`;
                document.getElementById('jupyterLink').href = jupyterUrl;
                document.getElementById('jupyterLink').classList.remove('inactive');
                document.getElementById('jupyterLink').classList.add('ready');
                document.getElementById('jupyterLink').target = '_blank';
                document.getElementById('jupyterStatus').textContent = ' - Ready';
                
                // Show ComfyUI as waiting
                document.getElementById('comfyLink').classList.remove('inactive');
                document.getElementById('comfyLink').classList.add('waiting');
                document.getElementById('comfyStatus').textContent = ' - Starting...';
                
                checkComfyUIStatus();
                startSessionTimer();
            } else {
                alert('Error: ' + result.message);
                document.getElementById('startBtn').disabled = false;
                document.getElementById('startBtn').textContent = 'Start My Session';
            }
        }
        
        function checkComfyUIStatus() {
            checkInterval = setInterval(async () => {
                try {
                    const response = await fetch('/comfyui_status');
                    const result = await response.json();
                    
                    if (result.ready) {
                        const runpodId = '{{ runpod_id }}';
                        const comfyUrl = `https://${runpodId}-8188.proxy.runpod.net`;
                        document.getElementById('comfyLink').href = comfyUrl;
                        document.getElementById('comfyLink').classList.remove('waiting');
                        document.getElementById('comfyLink').classList.add('ready');
                        document.getElementById('comfyLink').innerHTML = '<strong>Open ComfyUI</strong>';
                        document.getElementById('comfyLink').target = '_blank';
                        clearInterval(checkInterval);
                    }
                } catch (e) {
                    console.error('Status check failed:', e);
                }
            }, 5000);
        }
        
        function handleComfyClick(event) {
            const link = document.getElementById('comfyLink');
            if (link.classList.contains('inactive')) {
                event.preventDefault();
                return false;
            }
        }
        
        function startSessionTimer() {
            timerInterval = setInterval(() => {
                if (sessionStartTime) {
                    const elapsed = Math.floor((new Date() - sessionStartTime) / 1000);
                    const hours = Math.floor(elapsed / 3600);
                    const minutes = Math.floor((elapsed % 3600) / 60);
                    const seconds = elapsed % 60;
                    
                    let timeStr = '';
                    if (hours > 0) {
                        timeStr = `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                    } else {
                        timeStr = `${minutes}:${seconds.toString().padStart(2, '0')}`;
                    }
                    
                    document.getElementById('sessionTime').textContent = timeStr;
                }
            }, 1000);
        }
        
        async function terminateRunPod() {
            if (confirm('Are you sure you want to terminate this RunPod instance? All unsaved work will be lost.')) {
                const btn = event.target;
                btn.disabled = true;
                btn.textContent = 'Terminating...';
                
                try {
                    const response = await fetch('/terminate', {
                        method: 'POST'
                    });
                    const result = await response.json();
                    
                    if (result.success) {
                        alert('Processes terminated. Instance will shut down shortly...');
                    } else {
                        alert('Failed to terminate: ' + result.message);
                        btn.disabled = false;
                        btn.textContent = 'Terminate RunPod Instance';
                    }
                } catch (e) {
                    alert('Error: ' + e.message);
                    btn.disabled = false;
                    btn.textContent = 'Terminate RunPod Instance';
                }
            }
        }
    </script>
</body>
</html>
"""

def ensure_directories():
    Path(STATUS_DIR).mkdir(parents=True, exist_ok=True)
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

def get_existing_artists():
    """Get list of existing artist folders"""
    artists = []
    try:
        if os.path.exists(OUTPUT_DIR):
            for item in os.listdir(OUTPUT_DIR):
                if os.path.isdir(os.path.join(OUTPUT_DIR, item)):
                    if not item.startswith('.') and item != '.ipynb_checkpoints':
                        artists.append(item)
            artists.sort()
    except:
        pass
    return artists

def parse_nodes_from_script(script_content):
    """Parse install_nodes.sh script to extract available custom nodes"""
    import re
    nodes = []
    
    # Look for git clone commands and extract node information
    git_clone_pattern = r'git clone\s+([^\s]+)\s+([^\s]*)'
    lines = script_content.split('\n')
    
    for i, line in enumerate(lines):
        # Look for comments that describe nodes or git clone commands
        if 'git clone' in line:
            match = re.search(git_clone_pattern, line)
            if match:
                repo_url = match.group(1)
                
                # Extract node name from URL
                if 'github.com' in repo_url:
                    node_name = repo_url.split('/')[-1]
                    if node_name.endswith('.git'):
                        node_name = node_name[:-4]
                    
                    # Look for comment above for description
                    description = node_name.replace('-', ' ').replace('_', ' ').title()
                    if i > 0:
                        prev_line = lines[i-1].strip()
                        if prev_line.startswith('#') and not prev_line.startswith('#!/'):
                            description = prev_line[1:].strip()
                    
                    # Create unique ID from node name
                    node_id = node_name.lower().replace('-', '_').replace(' ', '_')
                    
                    nodes.append({
                        'id': node_id,
                        'name': description,
                        'repo_url': repo_url,
                        'folder_name': node_name
                    })
    
    return nodes

def parse_models_from_script(script_content):
    """Parse install_models.sh script to extract available models"""
    import re
    models = []
    
    # Look for wget/curl download commands and extract model information
    download_patterns = [
        r'wget\s+.*?-O\s+([^\s]+)\s+"([^"]+)"',  # wget -O filename "url"
        r'wget\s+"([^"]+)"\s+-O\s+([^\s]+)',     # wget "url" -O filename
        r'curl\s+.*?-o\s+([^\s]+)\s+"([^"]+)"',  # curl -o filename "url"
        r'curl\s+"([^"]+)"\s+-o\s+([^\s]+)'      # curl "url" -o filename
    ]
    
    lines = script_content.split('\n')
    
    for i, line in enumerate(lines):
        # Skip comments and empty lines
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        # Check each download pattern
        for pattern in download_patterns:
            match = re.search(pattern, line)
            if match:
                if 'wget' in line and '-O' in line:
                    if line.find('-O') < line.find('"'):
                        filename = match.group(1)
                        url = match.group(2)
                    else:
                        url = match.group(1)
                        filename = match.group(2)
                elif 'curl' in line and '-o' in line:
                    if line.find('-o') < line.find('"'):
                        filename = match.group(1)
                        url = match.group(2)
                    else:
                        url = match.group(1)
                        filename = match.group(2)
                else:
                    continue
                
                # Extract model info from filename/path
                model_name = filename.split('/')[-1]  # Get just the filename
                if model_name.endswith('.safetensors') or model_name.endswith('.ckpt') or model_name.endswith('.pt'):
                    # Clean up the model name
                    display_name = model_name.replace('_', ' ').replace('-', ' ')
                    display_name = display_name.rsplit('.', 1)[0]  # Remove extension
                    
                    # Try to extract size info from comment above
                    size_info = "Unknown size"
                    if i > 0:
                        prev_line = lines[i-1].strip()
                        if prev_line.startswith('#'):
                            size_match = re.search(r'(\d+\.?\d*\s*[GMK]B)', prev_line, re.IGNORECASE)
                            if size_match:
                                size_info = size_match.group(1)
                    
                    # Create unique ID from model name
                    model_id = model_name.lower().replace(' ', '_').replace('-', '_').replace('.', '_')
                    
                    models.append({
                        'id': model_id,
                        'name': display_name,
                        'filename': model_name,
                        'url': url,
                        'size': size_info
                    })
                    break
    
    return models

def install_individual_nodes(node_ids):
    """Install specific custom nodes by their IDs"""
    global installation_in_progress, output_queue
    
    try:
        # First fetch the script to get node information
        github_url = "https://raw.githubusercontent.com/razvanmatei-sf/comfyui-runpod-manager/main/installer/install_nodes.sh"
        response = requests.get(github_url, timeout=10)
        
        if response.status_code != 200:
            output_queue.put("Failed to fetch node installation script from GitHub")
            return False
        
        # Parse nodes and filter by selected IDs
        all_nodes = parse_nodes_from_script(response.text)
        selected_nodes = [node for node in all_nodes if node['id'] in node_ids]
        
        if not selected_nodes:
            output_queue.put("No valid nodes selected for installation")
            return False
        
        output_queue.put(f"Installing {len(selected_nodes)} custom nodes...")
        
        # Activate virtual environment and install each node
        for node in selected_nodes:
            try:
                output_queue.put(f"Installing {node['name']}...")
                
                # Commands to install the node
                commands = [
                    "cd /workspace/ComfyUI",
                    "source .venv/bin/activate",
                    f"cd custom_nodes",
                    f"git clone {node['repo_url']} {node['folder_name']}",
                    f"cd {node['folder_name']}",
                    "if [ -f requirements.txt ]; then pip install -r requirements.txt; fi"
                ]
                
                # Execute installation command
                cmd = " && ".join(commands)
                process = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if process.returncode == 0:
                    output_queue.put(f"✓ {node['name']} installed successfully")
                else:
                    output_queue.put(f"✗ Failed to install {node['name']}: {process.stderr}")
                    logging.error(f"Node installation failed: {process.stderr}")
                    
            except subprocess.TimeoutExpired:
                output_queue.put(f"✗ Installation of {node['name']} timed out")
                return False
            except Exception as e:
                output_queue.put(f"✗ Error installing {node['name']}: {str(e)}")
                logging.error(f"Node installation error: {e}")
        
        output_queue.put("Individual node installation completed")
        return True
        
    except Exception as e:
        output_queue.put(f"Node installation failed: {str(e)}")
        logging.error(f"Individual nodes installation error: {e}")
        return False

def install_individual_models(model_ids):
    """Install specific models by their IDs"""
    global installation_in_progress, output_queue
    
    try:
        # First fetch the script to get model information
        github_url = "https://raw.githubusercontent.com/razvanmatei-sf/comfyui-runpod-manager/main/installer/install_models.sh"
        response = requests.get(github_url, timeout=10)
        
        if response.status_code != 200:
            output_queue.put("Failed to fetch model installation script from GitHub")
            return False
        
        # Parse models and filter by selected IDs
        all_models = parse_models_from_script(response.text)
        selected_models = [model for model in all_models if model['id'] in model_ids]
        
        if not selected_models:
            output_queue.put("No valid models selected for installation")
            return False
        
        output_queue.put(f"Installing {len(selected_models)} models...")
        
        # Download each model
        for model in selected_models:
            try:
                output_queue.put(f"Downloading {model['name']} ({model['size']})...")
                
                # Determine the correct directory path from filename
                file_path = f"/workspace/ComfyUI/{model['filename']}"
                
                # Create directory if it doesn't exist
                model_dir = os.path.dirname(file_path)
                if model_dir:
                    os.makedirs(model_dir, exist_ok=True)
                
                # Download the model using wget
                cmd = f'cd /workspace/ComfyUI && wget -O "{model["filename"]}" "{model["url"]}"'
                process = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=1800  # 30 minutes for large models
                )
                
                if process.returncode == 0:
                    output_queue.put(f"✓ {model['name']} downloaded successfully")
                else:
                    output_queue.put(f"✗ Failed to download {model['name']}: {process.stderr}")
                    logging.error(f"Model download failed: {process.stderr}")
                    
            except subprocess.TimeoutExpired:
                output_queue.put(f"✗ Download of {model['name']} timed out")
                return False
            except Exception as e:
                output_queue.put(f"✗ Error downloading {model['name']}: {str(e)}")
                logging.error(f"Model download error: {e}")
        
        output_queue.put("Individual model installation completed")
        return True
        
    except Exception as e:
        output_queue.put(f"Model installation failed: {str(e)}")
        logging.error(f"Individual models installation error: {e}")
        return False

def get_runpod_id():
    """Get RunPod instance ID from environment"""
    return os.environ.get('RUNPOD_POD_ID', 'localhost')

def check_component_status(component):
    status_file = f"{STATUS_DIR}/{component}_status.json"
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"installed": False, "installing": False, "timestamp": None}

def update_component_status(component, installed=False, installing=False):
    status_file = f"{STATUS_DIR}/{component}_status.json"
    status = {
        "installed": installed,
        "installing": installing,
        "timestamp": datetime.now().isoformat()
    }
    with open(status_file, 'w') as f:
        json.dump(status, f)
    return status

def check_comfyui_ready():
    """Check if ComfyUI is responding"""
    global comfyui_ready
    try:
        response = requests.get('http://localhost:8188/api/prompt', timeout=2)
        comfyui_ready = response.status_code == 200
    except:
        comfyui_ready = False
    return comfyui_ready

def stream_output(process):
    """Stream process output to queue"""
    global output_queue
    for line in iter(process.stdout.readline, ''):
        if line:
            output_queue.put(line.strip())
    for line in iter(process.stderr.readline, ''):
        if line:
            output_queue.put(f"ERROR: {line.strip()}")

def run_installation_script(component):
    """Run installation script for component"""
    global current_process, installation_in_progress
    
    try:
        installation_in_progress = True
        update_component_status(component, installing=True)
        
        output_queue.put(f"Starting {component} installation...")
        output_queue.put(f"Pulling installation scripts from GitHub...")
        
        temp_dir = f"/tmp/comfyui-install-{int(time.time())}"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Clone repository
        clone_cmd = f"git clone {GITHUB_REPO} {temp_dir}"
        process = subprocess.Popen(
            clone_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise Exception(f"Failed to clone repository: {stderr}")
        
        script_map = {
            'comfyui': 'installer/install_comfyui.sh',
            'models': 'installer/install_models.sh',
            'nodes': 'installer/install_nodes.sh'
        }
        
        script_path = f"{temp_dir}/{script_map[component]}"
        
        if not os.path.exists(script_path):
            raise Exception(f"Installation script not found: {script_map[component]}")
        
        os.chmod(script_path, 0o755)
        
        current_process = subprocess.Popen(
            script_path,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        output_thread = threading.Thread(target=stream_output, args=(current_process,))
        output_thread.start()
        
        current_process.wait()
        output_thread.join()
        
        success = current_process.returncode == 0
        update_component_status(component, installed=success, installing=False)
        
        # Cleanup
        subprocess.run(f"rm -rf {temp_dir}", shell=True)
        
        return success
        
    except Exception as e:
        output_queue.put(f"ERROR: {str(e)}")
        update_component_status(component, installed=False, installing=False)
        return False
    finally:
        installation_in_progress = False
        current_process = None

@app.route('/')
def index():
    existing_artists = get_existing_artists()
    runpod_id = get_runpod_id()
    return render_template_string(MAIN_HTML, artists=existing_artists, runpod_id=runpod_id)

@app.route('/authenticate', methods=['POST'])
def authenticate():
    password = request.json.get('password', '')
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    if password_hash == ADMIN_PASSWORD_HASH:
        session['authenticated'] = True
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/check_status')
def check_status():
    ensure_directories()
    return jsonify({
        'comfyui': check_component_status('comfyui'),
        'models': check_component_status('models'),
        'nodes': check_component_status('nodes')
    })

@app.route('/get_available_nodes')
def get_available_nodes():
    """Parse install_nodes.sh from GitHub to get available nodes"""
    if not session.get('authenticated'):
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    try:
        github_url = "https://raw.githubusercontent.com/razvanmatei-sf/comfyui-runpod-manager/main/installer/install_nodes.sh"
        response = requests.get(github_url, timeout=10)
        
        if response.status_code == 200:
            script_content = response.text
            nodes = parse_nodes_from_script(script_content)
            return jsonify({'success': True, 'nodes': nodes})
        else:
            return jsonify({'success': False, 'message': 'Failed to fetch install script'})
            
    except Exception as e:
        logging.error(f"Error fetching available nodes: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/get_available_models')
def get_available_models():
    """Parse install_models.sh from GitHub to get available models"""
    if not session.get('authenticated'):
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    try:
        github_url = "https://raw.githubusercontent.com/razvanmatei-sf/comfyui-runpod-manager/main/installer/install_models.sh"
        response = requests.get(github_url, timeout=10)
        
        if response.status_code == 200:
            script_content = response.text
            models = parse_models_from_script(script_content)
            return jsonify({'success': True, 'models': models})
        else:
            return jsonify({'success': False, 'message': 'Failed to fetch install script'})
            
    except Exception as e:
        logging.error(f"Error fetching available models: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/install', methods=['POST'])
def install():
    if not session.get('authenticated'):
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    if installation_in_progress:
        return jsonify({'success': False, 'message': 'Installation already in progress'})
    
    options = request.json
    
    def run_installations():
        try:
            if options.get('comfyui'):
                success = run_installation_script('comfyui')
                if not success:
                    output_queue.put('ComfyUI installation failed')
                    return
            
            if options.get('models'):
                # Check if individual models are specified
                individual_models = options.get('individual_models', [])
                if individual_models:
                    success = install_individual_models(individual_models)
                else:
                    success = run_installation_script('models')
                    
                if not success:
                    output_queue.put('Models installation failed')
                    return
            
            if options.get('nodes'):
                # Check if individual nodes are specified
                individual_nodes = options.get('individual_nodes', [])
                if individual_nodes:
                    success = install_individual_nodes(individual_nodes)
                else:
                    success = run_installation_script('nodes')
                    
                if not success:
                    output_queue.put('Nodes installation failed')
                    return
            
            output_queue.put('Installation completed successfully!')
        except Exception as e:
            output_queue.put(f'Installation failed: {str(e)}')
    
    thread = threading.Thread(target=run_installations)
    thread.start()
    
    return jsonify({'success': True})

@app.route('/terminal_output')
def terminal_output():
    """Get terminal output for admin interface"""
    global output_queue, installation_in_progress
    
    output_lines = []
    try:
        while True:
            line = output_queue.get_nowait()
            output_lines.append(line)
    except:
        pass
    
    return jsonify({
        'output': '\n'.join(output_lines) if output_lines else '',
        'installation_complete': not installation_in_progress,
        'success': True
    })

@app.route('/start_session', methods=['POST'])
def start_session():
    global artist_name, comfyui_process, jupyter_process, session_start_time, comfyui_ready
    
    try:
        data = request.get_json()
        name = data.get('artist_name', '').strip()
        
        if not name:
            return jsonify({'success': False, 'message': 'Artist name required'})
        
        artist_name = name
        session_start_time = datetime.now()
        comfyui_ready = False
        
        # Create output directory
        output_dir = f"/workspace/output/{artist_name}"
        os.makedirs(output_dir, exist_ok=True)
        
        # Start Jupyter Lab
        if not jupyter_process or jupyter_process.poll() is not None:
            jupyter_process = subprocess.Popen([
                'jupyter', 'lab',
                '--ip=0.0.0.0',
                '--port=8888',
                '--no-browser',
                '--allow-root',
                '--NotebookApp.token=',
                '--NotebookApp.password='
            ], cwd='/workspace')
        
        # Start ComfyUI
        if not comfyui_process or comfyui_process.poll() is not None:            
            env = os.environ.copy()
            env['HF_HOME'] = '/workspace'
            env['HF_HUB_ENABLE_HF_TRANSFER'] = '1'
            
            artist_output_dir = f"/workspace/output/{artist_name}"
            
            # Start ComfyUI using the virtual environment
            comfyui_process = subprocess.Popen([
                '/workspace/ComfyUI/.venv/bin/python',
                'main.py',
                '--listen', '0.0.0.0',
                '--port', '8188',
                '--output-directory', artist_output_dir
            ], cwd='/workspace/ComfyUI', env=env)
            
            def monitor_comfyui():
                time.sleep(5)
                for _ in range(30):
                    if check_comfyui_ready():
                        break
                    time.sleep(1)
            
            threading.Thread(target=monitor_comfyui, daemon=True).start()
        
        return jsonify({'success': True, 'message': f'Session started for {artist_name}'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/comfyui_status')
def comfyui_status():
    """Check if ComfyUI is ready"""
    return jsonify({'ready': check_comfyui_ready()})

@app.route('/terminate', methods=['POST'])
def terminate():
    """Kill processes and cleanup"""
    try:        
        cleanup_processes()
        
        return jsonify({'success': True, 'message': 'Processes terminated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

def cleanup_processes():
    global comfyui_process, jupyter_process
    if comfyui_process:
        comfyui_process.terminate()
    if jupyter_process:
        jupyter_process.terminate()

def signal_handler(sig, frame):
    cleanup_processes()
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    ensure_directories()
    print("Starting ComfyUI Studio on port 8080...")
    app.run(host='0.0.0.0', port=8080, debug=False)