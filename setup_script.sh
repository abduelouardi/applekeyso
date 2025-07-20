#!/bin/bash

echo "🍎 Apple Key Generator Bot Setup"
echo "================================="

# Update system
echo "📦 Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# Install Python and pip
echo "🐍 Installing Python and pip..."
sudo apt-get install python3 python3-pip python3-venv -y

# Install Chrome dependencies
echo "🌐 Installing Chrome dependencies..."
sudo apt-get install -y \
    wget \
    curl \
    unzip \
    xvfb \
    libnss3-dev \
    libgconf-2-4 \
    libxrandr2 \
    libasound2-dev \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcairo-gobject2 \
    libgtk-3-0 \
    libgdk-pixbuf2.0-0

# Install Google Chrome
echo "🔧 Installing Google Chrome..."
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
sudo apt-get update
sudo apt-get install google-chrome-stable -y

# Create project directory
echo "📁 Creating project directory..."
mkdir -p apple_key_bot
cd apple_key_bot

# Create virtual environment
echo "🔧 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python requirements
echo "📚 Installing Python packages..."
pip install --upgrade pip

# Create requirements.txt file
cat > requirements.txt << EOF
python-telegram-bot==20.7
selenium==4.15.2
webdriver-manager==4.0.1
asyncio
urllib3==2.0.7
requests==2.31.0
beautifulsoup4==4.12.2
EOF

# Install requirements
pip install -r requirements.txt

# Create systemd service file for auto-start
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/apple-key-bot.service > /dev/null << EOF
[Unit]
Description=Apple Key Generator Telegram Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python apple_key_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Set permissions
sudo systemctl daemon-reload
sudo systemctl enable apple-key-bot.service

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Copy your bot.py file to this directory"
echo "2. Start the bot: sudo systemctl start apple-key-bot"
echo "3. Check status: sudo systemctl status apple-key-bot"
echo "4. View logs: sudo journalctl -u apple-key-bot -f"
echo ""
echo "🚀 Your bot will automatically start on system boot!"
echo "📍 Project directory: $(pwd)"