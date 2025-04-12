import socket
import threading
import pyaudio

# Configuration
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# Replace with the other device's IP and port
REMOTE_IP = # add ip address of another device
REMOTE_PORT = 8000

# This device's IP and port
LOCAL_IP = ''
LOCAL_PORT = 8000

# Initialize PyAudio
audio = pyaudio.PyAudio()

# Open input/output streams
stream_in = audio.open(format=FORMAT,
                       channels=CHANNELS,
                       rate=RATE,
                       input=True,
                       frames_per_buffer=CHUNK)

stream_out = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        output=True,
                        frames_per_buffer=CHUNK)

# UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((LOCAL_IP, LOCAL_PORT))

# Sender thread
def send_audio():
    while True:
        try:
            data = stream_in.read(CHUNK, exception_on_overflow=False)
            sock.sendto(data, (REMOTE_IP, REMOTE_PORT))
        except Exception as e:
            print(f"Send error: {e}")
            break

# Receiver thread
def receive_audio():
    while True:
        try:
            data, addr = sock.recvfrom(4096)
            stream_out.write(data)
        except Exception as e:
            print(f"Receive error: {e}")
            break

# Start threads
t1 = threading.Thread(target=send_audio)
t2 = threading.Thread(target=receive_audio)

t1.start()
t2.start()

t1.join()
t2.join()
