import sys
import struct
import time
import numpy as np
import serial

BAUDRATE = 921600
SAMPLING_RATE = 1000.0  # 1kHz
FULL_SCALE = 24.0

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
        data.append(read_sample(port))
    finally:
      # 確実に計測停止する
      port.write('e'.encode('utf-8')) # 計測停止
  return data

def convert_to_g(raw_values):
  # LIS331データシートTable 3のSensitivityという値は意味がよくわからない．
  # Sparkfunのサンプルコード(下記2個)でもMeasurement range(最大値)の方を使っているので，それと同様にGに換算する．
  # https://github.com/jenfoxbot/ImpactForceMonitor/blob/master/PythonProgram.py
  # https://github.com/sparkfun/Triple_Axis_Accelerometer_Breakout-LIS331/blob/V_1.2/Firmware/SparkFun_LIS331-v10/main.c
  return raw_values * (2 * FULL_SCALE) / (1 << 16)

if __name__ == '__main__':
  import matplotlib.pyplot as plt

  port_name = "COM3"
  duration = 0.25

  if len(sys.argv) > 1:
    port_name = sys.argv[1]
  if len(sys.argv) > 2:
    duration = float(sys.argv[2])

  plt.ion()
  while True:
    data = measure(port_name, int(duration * SAMPLING_RATE))

    xyz = convert_to_g(np.array(data))
    t = np.arange(0, duration, 1.0 / SAMPLING_RATE)

    # Gからm/s^2に換算
    xyz *= 9.8

    plt.plot(t, xyz[:, 0], label='x')
    plt.plot(t, xyz[:, 1], label='y')
    plt.plot(t, xyz[:, 2], label='z')
    plt.legend()
    plt.xlabel('Time [s]')
    plt.ylabel('Acceleration [m/s^2]')
    plt.show()
    plt.draw()

    # 重力成分(平均値)を除去
    xyz -= np.mean(xyz, axis=0)
    # 振幅(実効値)の計算
    amp_rms = np.sqrt(np.mean(xyz * xyz, axis=0)) # 各軸の二乗平均の平方根
    amp_all = np.sqrt(np.sum(amp_rms * amp_rms)) # 全ての軸
    print("{} [m/s^2]".format(amp_all))

    plt.pause(0.1)
    plt.clf()