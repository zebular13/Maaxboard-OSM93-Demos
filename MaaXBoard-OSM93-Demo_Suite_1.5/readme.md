# Project Name: MaaXBoard OSM93 Demo Applications Suite

## Overview
Tria developed application suite to explore funtionality of the MaaXBoard OSM93. Multiple applications are included in this project folder including: Web server, CAN interface demo, AI Fitness Trainer, and Driver Monitoring system. 

## Features
- **CAN Bus Communication:** 
    - Interface with the CAN bus to send and receive messages.
    - A "Test" folder is provided in CanTools to exercise a CAN bus demo isolated from the main demo application suite.
- **Web Dashboard:** 
    - Creates a simple web server on the MaaXBoard OSM93 <IP_addr:5555>.
    - Displays general information for MaaXBoard OSM93 and OSM93 module.
    - Allow accessing a camera interface (if connected).
- **Demo Application Suite:** 
    - Three demos included in the suite: AI Fitness trainer, DMS (Driver Monitoring), interactive CAN demo.
    - Demos built on top of Glade UI. 


## Prerequisites
- MaaXBoard OSM93
- USB-C Power Supply for board (5V, 2A)
- Camera (USB or MIPI) - Required for AI Fitness Trainer & DMS Demo
- Display panel (MIPI) - Demo application suite shown on 7" MIPI display
- CAN Interface cable (PN: XXXX) - Required for interactive CAN demo.
- Relevant Python libraries - See requirements.txt

## Installation
1. Clone the repository to your MaaXBoard OSM93:
    ```bash
    git clone 
    ```

2. Change access permissions to setup.sh shell script:
    ```bash
    chmod +x ./setup.sh
    ```

3. Run the setup.sh script to change access permissions to project folder & install python dependencies:
    ```bash
    ./setup.sh
    ```

3. Reboot the MaaXBoard OSM93 twice to allow auto-launch to configure properly. 

4. After the second reboot, the demo application suite should automatically launch. 