# 📡 Urban Sensing Service

This repository contains the scripts and code necessary to transform a Raspberry Pi into an urban sensor. Here's the file and directory structure:

```bash
.
├── install.sh
├── configure.sh
├── code
│   ├── default
│   │   └── start.py
│   └── ... (additional directories/files as needed)
└── README.md
```

## 🛠️ Installation script

The `install.sh` script automates the installation process for the Urban Sensing Service. To execute the script, run the following command:

```
sudo bash install.sh
```

This script performs several tasks:
1. Updates system packages.
2. Installs Python 3 and Pip 3. 
3. Installs `libpcap`, a library used for network traffic analysis and packet capture. 
4. Installs required Python packages: `pcapy` and `dpkt`. 
5. Installs `git` and `ntpdate`. 
6. Installs the Bluetooth library, `libbluetooth-dev`. 
7. Checks if the `Bluelog` directory exists. If not, it clones the `Bluelog` repository from GitHub, then builds and installs it.
## ⚙️ Configuration script

The `configure.sh` script manages the configurations required for the smooth operation of the Urban Sensing Service. To execute the script, run the following command:

```

sudo bash configure.sh
```

This script performs the following tasks: 
1. Sets up udev rules to ensure the Raspberry Pi consistently assigns the correct network interface name (`wlan0`) to the internal WiFi adapter. 
2. Creates a systemd service file for the Urban Sensing Service, set to start on boot. This service runs `start.py`, the primary script of the sensing service, as a Python 3 script.
3. Gives a permission to the 'stats' and 'data' folder for Samba access.

## 🚀 Urban Sensing Code

The default code example (`start.py` located in the 'code/default' folder) runs the Urban Sensing Service. It carries out several operations:
- Synchronizes the system time with a Network Time Protocol server and sets the timezone to Asia/Seoul.
- Optimizes power usage by disabling HDMI and the internal WiFi after 60 seconds of inactivity.
- Collects Bluetooth data and saves it in a text file.
- Sets up WiFi monitoring on three different channels (1, 6, and 11) using external WiFi adapters.
- Continuously collects WiFi packet data from these channels, parses the data, and stores relevant information in a SQLite database.

This script is designed to be run as a systemd service upon boot (as configured by the `configure.sh` script), but can also be run manually with the following command:

```
sudo python3 start.py
```
### Adding Additional Operations

You have the freedom to extend the functionalities of your urban sensing system as per your needs. Simply create other `start.py` file in additional directories of 'code' directory. These could include tasks like recording a scene, turning off Bluetooth to save battery, or any other sensing operations you require.