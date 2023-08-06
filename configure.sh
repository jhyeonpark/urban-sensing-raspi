#!/bin/bash

# Ask the user if they want to change the device name
read -p "Do you want to change the device name (hostname)? (yes/no): " change_decision

if [ "$change_decision" == "yes" ]; then
    # Prompt the user for a new device name
    read -p "Enter a new device name (hostname): " new_hostname

    # Set the new device name
    sudo hostnamectl set-hostname $new_hostname

    # Update the /etc/hosts file
    sudo sed -i "s/127.0.1.1.*/127.0.1.1\t$new_hostname/" /etc/hosts

    # Display the updated hostname
    echo "Updated Device Name (Hostname): $(hostname)"

    # Optionally, you can reboot the system for changes to fully take effect.
    read -p "Do you want to reboot now? (yes/no): " answer
    if [ "$answer" == "yes" ]; then
        sudo reboot
    fi
else
    echo "Skipped hostname change process."
fi


# -------------------------------


# Obtain the MAC address of wlan0
echo "Obtaining the MAC address of wlan0..."
INTERNAL_ADAPTER_MAC=$(cat /sys/class/net/wlan0/address)

# Create a udev rule
echo "Creating a udev rule..."
echo "SUBSYSTEM==\"net\", ACTION==\"add\", ATTR{address}==\"$INTERNAL_ADAPTER_MAC\", NAME=\"wlan0\"" | sudo tee /etc/udev/rules.d/10-local.rules

# Reload udev rules
echo "Reloading udev rules..."
sudo udevadm control --reload-rules && sudo udevadm trigger

# Print a message to indicate the end of this section
echo "End of udev rules setup"


# -------------------------------

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

# -------------------------------

echo "Creating necessary directories..."
sudo mkdir /home/pi/data
sudo mkdir /home/pi/stats
sudo mkdir /home/pi/urban-sensing-raspi

echo "Setting permissions for the directories..."
sudo chmod 777 /home/pi/data
sudo chmod 777 /home/pi/stats
sudo chmod 777 /home/pi/urban-sensing-raspi

# -------------------------------

# Print a message when finished
echo "Script execution finished. The Sensing.service has been set up and started."
