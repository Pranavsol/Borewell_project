# Borewell_project

## Overview

The Borewell Project is a multi-device monitoring and control system designed for efficient and automated management of environmental and operational data. It leverages a combination of hardware sensors, Raspberry Pi, Arduino, and software components to provide real-time data visualization, audio control, and video streaming capabilities.

## Key Features

Sensor Data Monitoring:
  - Real-time temperature and humidity readings.
  - Air Quality Index (AQI) monitoring with an MQ135 sensor.

Video Streaming:
  - Live camera stream for monitoring.

Audio Control:
  - Start and stop audio functionalities remotely.

Web Interface:
  - User-friendly interface for visualizing sensor data and controlling devices.

Multi-Device Communication:
  - TCP/IP socket communication for sensor data exchange between devices.

## Technologies Used

Frameworks & Libraries:
  - Python: Flask, PyAudio, OpenCV
  - C++: MQ135 library
  - HTML/CSS/JavaScript for the frontend
Hardware:
  - Raspberry Pi for video and audio processing.
  - Arduino for sensor data collection Analog to Digital Conversion

## Installation

Clone this repository:

```
git clone https://github.com/Pranavsol/Borewell_project.git
```
Navigate to project directory:
```
cd Borewell_project
```
Set up the Python environment:

```
pip install -r requirements.txt
```
Configure hardware and network settings as required:
Update IP addresses and ports in the respective configuration files.

## Usage
Running the Project
Start the Flask server on Device_2:
```
python app.py
```
Start the main file on Devicce_1 to detect movement from PIR sensor:
```
python app.py
```
- Webpage will open on Device_1 after detection and successful intialization of server on Device_2.

## Arduino Setup
Connect the MQ135 sensor to the Arduino.
Upload the Arduino/code.ino file to the Arduino board.

## File Structure

Device_1:
  - app.py: Manages server socket communication and Chromium browser.
  - audio/app.py: Handles audio data transmission between devices.

Device_2:
  - app.py: Main Flask application for video, audio, and sensor monitoring.
  - templates/index.html: Frontend HTML for the web interface.

Arduino:
  - code.ino: Arduino sketch for reading MQ135 sensor data.
