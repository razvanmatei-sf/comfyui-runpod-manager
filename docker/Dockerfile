FROM runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04

RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    vim \
    net-tools \
    iputils-ping \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --ignore-installed blinker -r requirements.txt

COPY enhanced_artist_server.py /app/enhanced_artist_server.py
COPY startup.sh /app/startup.sh

RUN mkdir -p /app/static
COPY static/admin.css /app/static/admin.css

RUN chmod +x /app/startup.sh

RUN mkdir -p /workspace/output
RUN mkdir -p /workspace/.comfyui-status

EXPOSE 8080
EXPOSE 8888
EXPOSE 8188

ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=enhanced_artist_server.py

CMD ["/app/startup.sh"]