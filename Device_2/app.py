import threading
import time
import logging
import sys
import traceback
import subprocess
import socket
import serial
from flask import Flask, jsonify, render_template, Response
import RPi.GPIO as GPIO
import dht11
import cv2
import picamera2
import pyaudio

audio_process = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/raspberrypi/sensor_camera_audio_app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('sensor-camera-audio-app')

# Global configuration
SENSOR_UPDATE_INTERVAL = 0.1  # Update sensor data every 5 seconds
THREAD_TIMEOUT = 30  # Timeout for thread operations

# Audio configuration with more flexible settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

SERVER_IP = # add erver ip address here
SERVER_PORT = 5007

LOCAL_IP = # add local ip address here
LOCAL_PORT = 5007

# Open serial connection (Update the port if necessary)
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)

last_reading = {"value": 0.0}

# Thread-safe data storage (Previous implementation remains the same)
sensor_data = {
    'temperature': None,
    'humidity': None,
    'last_updated': None
}
sensor_data_lock = threading.Lock()

# Singleton Camera Stream Class (Previous implementation remains the same)
class CameraStream:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(CameraStream, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, 'initialized'):
            return
        self.initialized = True
        self.camera = None

        for attempt in range(3):
            try:
                self._release_camera_resources()
                time.sleep(2)

                self.camera = picamera2.Picamera2()
                config = self.camera.create_video_configuration(
                    main={"size": (1280, 720)},
                    lores={"size": (640, 480)}
                )
                self.camera.configure(config)
                self.camera.start()

                logger.info("Camera initialized successfully")
                return
            except Exception as e:
                logger.error(f"Camera initialization attempt {attempt + 1} failed: {e}")
                self._log_camera_diagnostics()

                if self.camera:
                    try:
                        self.camera.stop()
                        self.camera.close()
                    except Exception as close_error:
                        logger.error(f"Error closing camera: {close_error}")

        raise RuntimeError("Could not initialize camera after multiple attempts")

    def _release_camera_resources(self):
        try:
            subprocess.run(['sudo', 'fuser', '-k', '/dev/video0'], check=False)
            subprocess.run(['sudo', 'pkill', '-f', 'rpicam-hello'], check=False)
            subprocess.run(['sudo', 'pkill', '-f', 'raspivid'], check=False)
            subprocess.run(['sudo', 'pkill', '-f', 'python.*picamera2'], check=False)
        except Exception as e:
            logger.error(f"Error releasing camera resources: {e}")

    def _log_camera_diagnostics(self):
        try:
            camera_status = subprocess.run(
                ['vcgencmd', 'get_camera'],
                capture_output=True,
                text=True
            )
            logger.info(f"Camera system status: {camera_status.stdout}")

            process_list = subprocess.run(
                ['sudo', 'lsof', '/dev/video0'],
                capture_output=True,
                text=True
            )
            logger.info(f"Processes using video device: {process_list.stdout}")
        except Exception as diag_error:
            logger.error(f"Diagnostic error: {diag_error}")

    def get_frame(self):
        try:
            frame = self.camera.capture_array("main")
            _, buffer = cv2.imencode('.jpg', frame)
            return buffer.tobytes()
        except Exception as e:
            logger.error(f"Frame capture error: {e}")
            return None

    def __del__(self):
        if self.camera:
            try:
                self.camera.stop()
                self.camera.close()
            except Exception as e:
                logger.error(f"Error closing camera in destructor: {e}")

# Rest of the previous implementation remains the same
# (sensor thread, camera thread, Flask routes, etc.)

# Initialize GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.cleanup()

# Set up DHT11 sensor
sensor = dht11.DHT11(pin=4)  # Change 4 to your GPIO pin
app = Flask(__name__)

def read_sensor_thread():
    """
    Continuously read sensor data in a separate thread.
    """
    global sensor_data
    while True:
        try:
            result = sensor.read()
            if result.is_valid():
                with sensor_data_lock:
                    sensor_data['temperature'] = result.temperature
                    sensor_data['humidity'] = result.humidity
                    sensor_data['last_updated'] = time.time()
            time.sleep(SENSOR_UPDATE_INTERVAL)
        except Exception as e:
            logger.error(f"Sensor reading error: {e}")
            time.sleep(SENSOR_UPDATE_INTERVAL)

def camera_stream_thread():
    """
    Thread to keep camera stream active and log any issues
    """
    camera = CameraStream()
    logger.info("Camera stream thread started")
    while True:
        try:
            time.sleep(60)  # Prevents tight looping
        except Exception as e:
            logger.error(f"Camera stream thread error: {e}")
            time.sleep(10)

def generate_frames():
    """Generate frames for video streaming"""
    camera = CameraStream()
    while True:
        frame = camera.get_frame()
        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            time.sleep(0.1)


last_reading = {"value": 0.0}

def request_sensor_data():
    """ Requests a reading from the Arduino and updates the latest value """
    global last_reading
    while True:
        try:
            ser.write(b'GET\n')  # Send request to Arduino
            time.sleep(0.1)  # Give Arduino time to respond
            response = ser.readline().decode('utf-8').strip()  # Read response
            
            if response.replace('.', '', 1).isdigit():  # Ensure valid number
                last_reading["value"] = float(response)
                print(f"Received: {last_reading['value']}")
        except Exception as e:
            print(f"Serial error: {e}")
        
        time.sleep(2)  # Adjust polling interval as needed



@app.route('/')
def index():
    """Render main web interface with sensor data and camera stream"""
    return render_template("index.html")

@app.route('/data')
def data():
    """API endpoint to fetch temperature and humidity"""
    with sensor_data_lock:
        if sensor_data['temperature'] is not None:
            return jsonify({
                "temperature": sensor_data['temperature'],
                "humidity": sensor_data['humidity'],
                "last_updated": sensor_data['last_updated']
            })
        else:
            return jsonify({"error": "No sensor data available"}), 503

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/current')
def get_current():
    return jsonify(last_reading)


@app.route('/start_audio')
def start_audio():
    global audio_process
    if audio_process is None or audio_process.poll() is not None:
        try:
            audio_process = subprocess.Popen(['python3', '../audio/app.py'])
            return jsonify({"status": "Audio started"})
        except Exception as e:
            return jsonify({"status": f"Failed to start: {e}"}), 500
    else:
        return jsonify({"status": "Audio already running"})


@app.route('/stop_audio')
def stop_audio():
    global audio_process
    if audio_process and audio_process.poll() is None:
        try:
            audio_process.terminate()
            audio_process.wait(timeout=5)
            audio_process = None
            return jsonify({"status": "Audio stopped"})
        except Exception as e:
            return jsonify({"status": f"Failed to stop: {e}"}), 500
    else:
        return jsonify({"status": "Audio not running"})



def start_threads():
    """
    Start multiple background threads for sensor, camera, and audio
    """
    threads = [
        threading.Thread(target=read_sensor_thread, daemon=True, name="SensorThread"),
        threading.Thread(target=camera_stream_thread, daemon=True, name="CameraThread"),
        threading.Thread(target=request_sensor_data, daemon=True, name="AQIThread")
        #threading.Thread(target=send_audio, daemon=True, name="AudioSendThread"),
        #threading.Thread(target=receive_audio, daemon=True, name="AudioReceiveThread")
    ]
    
    for thread in threads:
        thread.start()

def main():
    try:
        # Ensure threads are started before Flask
        start_threads()
        # Warmup threads
        time.sleep(2)
        
        #trying...
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(15)
        sock.connect((SERVER_IP, SERVER_PORT))

        # Run Flask app
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except Exception as e:
        logger.error(f"Server startup error: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        traceback.print_exc()
