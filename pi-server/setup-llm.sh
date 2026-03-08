#!/bin/bash
# Solarpunk Computing - Pi 5 LLM Server Setup
# Installs llama.cpp and downloads a small model for offline AI
#
# Usage: bash setup-llm.sh
# After setup: bash start-llm.sh

set -e

INSTALL_DIR="$HOME/solarpunk-llm"
MODEL_DIR="$INSTALL_DIR/models"

echo "==================================="
echo "  Solarpunk LLM Server Setup"
echo "  Target: Raspberry Pi 5 (4GB)"
echo "==================================="

# Install build dependencies
echo "[1/4] Installing dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq build-essential cmake git wget

# Clone and build llama.cpp
echo "[2/4] Building llama.cpp..."
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

if [ ! -d "llama.cpp" ]; then
    git clone --depth 1 https://github.com/ggerganov/llama.cpp.git
fi

cd llama.cpp
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j$(nproc)

# Download a small model
echo "[3/4] Downloading TinyLlama 1.1B (Q4_K_M, ~670MB)..."
mkdir -p "$MODEL_DIR"
cd "$MODEL_DIR"

MODEL_FILE="tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
if [ ! -f "$MODEL_FILE" ]; then
    wget -q --show-progress \
        "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/$MODEL_FILE" \
        -O "$MODEL_FILE"
fi

# Create start script
echo "[4/4] Creating start script..."
cat > "$INSTALL_DIR/start-llm.sh" << 'STARTEOF'
#!/bin/bash
# Start the Solarpunk LLM server
# The ESP32 connects to this on port 8080

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODEL="$SCRIPT_DIR/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"

if [ ! -f "$MODEL" ]; then
    echo "Model not found: $MODEL"
    echo "Run setup-llm.sh first"
    exit 1
fi

echo "Starting Solarpunk LLM server..."
echo "Model: TinyLlama 1.1B"
echo "Listening on: 0.0.0.0:8080"
echo "Press Ctrl+C to stop"
echo ""

exec "$SCRIPT_DIR/llama.cpp/build/bin/llama-server" \
    -m "$MODEL" \
    --host 0.0.0.0 \
    --port 8080 \
    -c 512 \
    -ngl 0 \
    -t 4 \
    --log-disable
STARTEOF
chmod +x "$INSTALL_DIR/start-llm.sh"

# Create systemd service
cat > "$INSTALL_DIR/solarpunk-llm.service" << SVCEOF
[Unit]
Description=Solarpunk LLM Server (llama.cpp)
After=network.target

[Service]
Type=simple
ExecStart=$INSTALL_DIR/start-llm.sh
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
SVCEOF

echo ""
echo "==================================="
echo "  Setup complete!"
echo "==================================="
echo ""
echo "To start manually:"
echo "  bash $INSTALL_DIR/start-llm.sh"
echo ""
echo "To install as a service:"
echo "  mkdir -p ~/.config/systemd/user"
echo "  cp $INSTALL_DIR/solarpunk-llm.service ~/.config/systemd/user/"
echo "  systemctl --user daemon-reload"
echo "  systemctl --user enable --now solarpunk-llm"
echo ""
echo "To set up WiFi hotspot for ESP32:"
echo "  sudo nmcli device wifi hotspot ifname wlan0 ssid solarpunk-pi password solarpunk"
echo ""
