# 📡 Wi-Fi Sensing Service

This repository contains the scripts for setting up, configuring, and running an Urban Sensing Service on a Raspberry Pi. 

## 🛠️ Installation

The `install.sh` script automates the installation process for the Wi-Fi Sensing Service.

To run the script, use the following command:

```
sudo bash install.sh
```

This script performs the following actions:
1. Updates system packages.
2. Installs Python 3 and Pip 3. 
3. Installs `libpcap`, a library used for packet capture and network traffic analysis. 
4. Installs necessary Python packages: `pcapy` and `dpkt`. 
5. Installs `git` and `ntpdate`. 
6. Installs the Bluetooth library, `libbluetooth-dev`. 
7. Checks if `Bluelog` directory already exists. If not, it clones the `Bluelog` repository from GitHub, builds, and installs it.

## ⚙️ Configuration

The `configure.sh` script handles the configuration necessary for the proper operation of the Wi-Fi Sensing Service.

To run the script, use the following command:

```
sudo bash configure.sh
```

The script does the following: 
- It sets up udev rules to ensure that the Raspberry Pi consistently assigns the correct network interface name to the internal Wi-Fi adapter (`wlan0`). 
- It creates a systemd service file for the Wi-Fi Sensing Service and sets it to start on boot. The service runs the main script of the sensing service, `start.py`, as a Python 3 script.

## 🚀 Running the Wi-Fi Sensing Service

The `start.py` script is the main script that runs the Wi-Fi Sensing Service. It performs a number of operations:
- It synchronizes the system time with a network time protocol server and sets the time zone to Asia/Seoul.
- It optimizes power usage by disabling HDMI and the internal Wi-Fi after 60 seconds. 
- It collects Bluetooth data using the `Bluelog` program and stores the data in a text file.
- It sets up Wi-Fi monitoring on three different channels (1, 6, and 11) on external Wi-Fi adapters.
- It continuously collects Wi-Fi packet data from these channels, parses the data, and stores relevant information in a SQLite database.

This script is designed to be run as a systemd service on boot, as set up by the `configure.sh` script, but can also be run manually using the following command:

```
sudo python3 start.py
```

⚠️ Please note that both scripts must be run with superuser (root) privileges due to the system-level changes they make. If the scripts complete successfully, all necessary packages and libraries for the Wi-Fi Sensing Service will be installed and ready for use, and the service will be configured to start on boot.