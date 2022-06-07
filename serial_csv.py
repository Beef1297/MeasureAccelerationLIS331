import os
import sys
import struct
import time
import threading
import serial

BAUDRATE = 115200
SAMPLING_RATE = 1000.0  # 1kHz

def read_port(port) :
    while True:
        time.sleep(1)
        header = port.read(1)
        print("header: {0}, {1}".format(header, type(header)))
        if (header != 0xFF) :
            time.sleep(0.1)
            continue
        val = port.read(1)
        print(val)
        print("val: {0}, {1}".format(val, type(val)))
        
        

def read_sample(port):
  buf = port.read(size=2*2)
  header, val = struct.unpack('>hh', buf)
  return (header, val)


if __name__ == '__main__':
    
    port_name = "COM5"

    port = serial.Serial(port=port_name, baudrate=BAUDRATE)
#   thread = threading.Thread(target=read_port, args=(port,))
#   thread.start()
    while True:
        time.sleep(1)
        header = port.read(1)
        print("header: {0}, {1}".format(header, type(header)))
        if (header != 0xFF) :
            time.sleep(0.1)
            continue
        val = port.read(1)
        print(val)
        print("val: {0}, {1}".format(val, type(val)))

      