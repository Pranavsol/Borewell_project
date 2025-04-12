import socket
import threading
import pyaudio
import webbrowser
import os
import subprocess
import time

# Audio configuration
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
DEVICE_INDEX = 3  # Specify the microphone device index

# Network configuration
SERVER_IP = # local device ip address
SERVER_PORT = 5007  # Same port as previous script

# Client configuration
CLIENT_IP = # ip address for another device
CLIENT_PORT = 5007  # Same port for sending and receiving

# IP Mapping for webpage loading
IP_WEBPAGE_MAP = {
    '<ip_add>' : 'http://<ip_add>:5000'
    # Add more IP-to-webpage mappings as needed
}

p = pyaudio.PyAudio()
start_message_sent = False  # Flag to ensure message is sent only once

def send_start_message():
    """Send start_server message to client."""
    global start_message_sent
    if start_message_sent:
        return True
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((CLIENT_IP, CLIENT_PORT))
            s.sendall(b"start_server")
            print("start_server message sent successfully!")
            
            # Wait for acknowledgment with a timeout
            s.settimeout(5)  # 5-second timeout
            try:
                response = s.recv(1024).decode('utf-8').strip()
                print(f"Received response: {response}")
                start_message_sent = True
                return True
            except socket.timeout:
                print("Timeout waiting for response")
                return False
    except Exception as e:
        print(f"Error sending start message: {e}")
        return False

def open_chromium_webpage(url):
    """
    Open a URL in Chromium browser using shell executable.
    """
    try:
        # Use subprocess to open Chromium with the specified URL
        subprocess.Popen(['/usr/bin/chromium-browser', url], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
        print(f"Opened {url} in Chromium")
    except Exception as e:
        print(f"Error opening Chromium: {e}")
        # Fallback to default browser if Chromium fails
        try:
            webbrowser.open(url)
        except Exception as fallback_error:
            print(f"Fallback browser open failed: {fallback_error}")


def load_webpage_for_client(client_ip):
    """Load webpage based on client IP address in Chromium."""
    if client_ip in IP_WEBPAGE_MAP:
        try:
            open_chromium_webpage(IP_WEBPAGE_MAP[client_ip])
            print(f"Loaded webpage for IP {client_ip} in Chromium")
            with open("audio_log.txt", "w") as logfile:
                subprocess.Popen(["python3", "../audio/app.py"], stdout=logfile, stderr=logfile)
        except Exception as e:
            print(f"Error loading webpage for IP {client_ip}: {e}")
    else:
        print(f"No webpage configured for IP {client_ip}")

def main():
    # Setup server socket to listen
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((SERVER_IP, SERVER_PORT))
    server_sock.listen(5)
    print(f"Server listening on port {SERVER_PORT}")
    
    while True:
        try:
            # Send start message only once before first connection
            if not start_message_sent:
                send_start_message()
            
            # Accept connection
            conn, addr = server_sock.accept()
            client_ip = addr[0]
            client_port = addr[1]
            print(f"Connected by IP: {client_ip}, Port: {client_port}")
            
            # Load webpage for the specific client IP in Chromium
            load_webpage_for_client(client_ip)
            
        except Exception as e:
            print(f"Server error: {e}")
            time.sleep(1)  # Prevent rapid error loops

if __name__ == "__main__":
    main()
