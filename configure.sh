#!/bin/bash

# -------------------------------

# Obtain the MAC address of wlan0
INTERNAL_ADAPTER_MAC=$(cat /sys/class/net/wlan0/address)

# Create a udev rule
echo "SUBSYSTEM==\"net\", ACTION==\"add\", ATTR{address}==\"$INTERNAL_ADAPTER_MAC\", NAME=\"wlan0\"" | sudo tee /etc/udev/rules.d/10-local.rules

# Reload udev rules
sudo udevadm control --reload-rules && sudo udevadm trigger

# Print a message to indicate the end of this section
echo "End of udev rules setup"


# -------------------------------

# Create service file
echo "[Unit]
Description=Wifi monitoring service
After=network.target

[Service]
WorkingDirectory=/home/pi/
ExecStart=/usr/bin/python3 /home/pi/urban-sensing-raspi/default/start.py
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

# -------------------------------

sudo mkdir /home/pi/data
sudo mkdir /home/pi/stats
sudo chmod 777 /home/pi/data
sudo chmod 777 /home/pi/stats

# -------------------------------

# Print a message when finished
echo "Script execution finished. The Sensing.service has been set up and started."
