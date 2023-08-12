#!/bin/bash

# Create service file
echo "Creating the Wifi monitoring service file..."

echo "[Unit]
Description=urban-sensing-service
After=network.target

[Service]
WorkingDirectory=/home/pi/
ExecStart=/usr/bin/python3 /home/pi/urban-sensing-raspi/code/default/start.py
User=root
Group=root

[Install]
WantedBy=multi-user.target" | sudo tee /lib/systemd/system/sensing.service

# Set permissions for the service file
sudo chmod 644 /lib/systemd/system/sensing.service

# Reload the systemd daemon
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable sensing.service

# Start the service
sudo systemctl start sensing.service
