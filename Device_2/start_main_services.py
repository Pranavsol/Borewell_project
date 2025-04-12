import socket
import subprocess
import threading

# Server Configuration
HOST = "0.0.0.0"  # Listen on all available interfaces
PORT = 5007  # Port for TCP trigger
DATA_PORT = 8009  # Port for sensor data communication

def start_flask_server():
    """Starts the Flask server."""
    print("Starting Flask server...")
    subprocess.Popen(["python3", "app.py"])
    print("Server started successfully!")

def tcp_listener():
    """Listens for a trigger over TCP to start the Flask server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen(1)  # Allow one connection
        print(f"Listening for trigger on port {PORT}...")
        
        conn, addr = server_socket.accept()
        with conn:
            data = conn.recv(1024)
            if data == b"start_server":
                start_flask_server()
    
    print("Exiting server listener...")

def sensor_data_server():
    """Receives sensor data over TCP."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, DATA_PORT))
        server_socket.listen(5)  # Allow multiple connections
        print(f"Sensor data server running on port {DATA_PORT}...")
        
        while True:
            conn, addr = server_socket.accept()
            with conn:
                data = conn.recv(1024)
                if data:
                    print(f"Received sensor data: {data.decode()}")

def sensor_data_client(target_ip):
    """Sends sensor data to the server over TCP."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((target_ip, DATA_PORT))
        while True:
            sensor_data = input("Enter sensor data: ")
            client_socket.sendall(sensor_data.encode())

def start_threads():
    """Starts the TCP listener and sensor data server in separate threads."""
    tcp_thread = threading.Thread(target=tcp_listener)
    sensor_thread = threading.Thread(target=sensor_data_server)
    
    tcp_thread.start()
    sensor_thread.start()
    
    tcp_thread.join()
    sensor_thread.join()

if __name__ == "__main__":
    start_threads()
