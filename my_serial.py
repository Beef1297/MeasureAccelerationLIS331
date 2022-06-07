import serial
import struct

BAUDRATE = 115200

def read_sample(port):
    buf = port.read(size=2*3)
    x, y, z = struct.unpack('>hhh', buf)
    return (x, y, z)

def measure(port_name, num_samples):
    with serial.Serial(port=port_name, baudrate=BAUDRATE) as port:
      port.write('s'.encode('utf-8')) # 計測開始
      try:
        data = []
        for i in range(num_samples):
          #print("measuring")
          data.append(read_sample(port))
      finally:
        # 確実に計測停止する
        #print("stop measuring")
        port.write('e'.encode('utf-8')) # 計測停止
    return data
  
def start_measure(port_name) :
    port = serial.Serial(port=port_name, baudrate=BAUDRATE)
    port.write('s'.encode('utf-8'))
    return port

def stream_measure(port):
    data = read_sample(port)
    return data