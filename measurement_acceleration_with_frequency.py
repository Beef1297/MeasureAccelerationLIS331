# -*- coding: utf-8 -*-
"""
Created on Tue Nov  5 17:23:58 2019

@author: ushiyama
"""

import os
import sys
import struct
from datetime import datetime
import numpy as np
from scipy import signal
import serial
import math
# keyboard input event handling のため
from pynput.keyboard import Listener
import keyboard

BAUDRATE = 921600
SAMPLING_RATE = 1000.0  # 1kHz
FULL_SCALE = 24.0

subject_name = ""
measurement_num = 0
vibrator_num = 1
pause = False

# keyboad input callback
def keypress_callback(key) :
    global pause
    if (hasattr(key, "char")) :
        c = key.char
        # Pause: p が押されたら Pause フラグを立てる
        # 複数回 callback が呼ばれる可能性があるので
        if (c == 'p') :
            pause = True
    return
    
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

def convert_to_g(raw_values):
  # LIS331データシートTable 3のSensitivityという値は意味がよくわからない．
  # Sparkfunのサンプルコード(下記2個)でもMeasurement range(最大値)の方を使っているので，それと同様にGに換算する．
  # https://github.com/jenfoxbot/ImpactForceMonitor/blob/master/PythonProgram.py
  # https://github.com/sparkfun/Triple_Axis_Accelerometer_Breakout-LIS332/blob/V_1.2/Firmware/SparkFun_LIS331-v10/main.c
    return raw_values * (2 * FULL_SCALE) / (1 << 16)

def fft(data) :
  N = len(data)
  dt = 1.0 / SAMPLING_RATE
  t = np.arange(0.0, duration, dt)
  window = signal.hamming(N)
  windowed_signal = data
  fk = np.fft.fft(windowed_signal)
  fq = np.linspace(0.0, 1.0/dt, N) #時間から周波数に変換
  fq_out = fq[:int(N/2)+1] # ナイキスト周波数まで
  fk_out = fk[:int(N/2)+1]
  
  # ピーク検出
  maximal_idx = signal.argrelmax(fk_out, order=1)[0]
  peak_cut = 50
  maximal_idx = maximal_idx[(fk[maximal_idx] > peak_cut)]

  peak_freq = [fq_out[idx] for idx in maximal_idx]
  print(peak_freq)

  return [fq_out, fk_out, maximal_idx]


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    
    port_name = "COM3"
    duration = 0.25
    if len(sys.argv) > 1:
      port_name = sys.argv[1]
    if len(sys.argv) > 2:
      duration = float(sys.argv[2])
    if (subject_name == "") :
        print("input subject name")
        subject_name = input()

    # keyboard 入力の callback 登録
    listener = Listener(on_press=keypress_callback)
    listener.start()
    
    
    plt.ion()
    while True:
        # ループの回数
        measurement_num += 1
        data = measure(port_name, int(duration * SAMPLING_RATE)) 
        xyz = convert_to_g(np.array(data))
        t = np.arange(0, duration, 1.0 / SAMPLING_RATE)
        
        # Gからm/s^2に換算
        xyz *= 9.8        
        print("plot graph")

        # 加速度データをプロットする場合
        # plt.xlabel('Time [s]')
        # plt.ylabel('Acceleration [m/s^2]')
        
        # plt.plot(t, xyz[:, 0], label='x')
        # plt.plot(t, xyz[:, 1], label='y')
        # plt.plot(t, xyz[:, 2], label='z')

        # max_val = max([max(xyz[:, 0]), max(xyz[:, 1]), max(xyz[:, 2])])
        # min_val = min([min(xyz[:, 0]), min(xyz[:, 1]), min(xyz[:, 2])])
        # plt.yticks(np.linspace(min_val, max_val, 10))
        # max_z = max(xyz[:, 2])
        # min_z = min(xyz[:, 2])
        # plt.yticks(np.linspace(math.ceil(min_z), math.ceil(max_z), 10))
        # plt.show()

        # 重力成分(平均値)を除去
        xyz -= np.mean(xyz, axis=0)
        # 振幅(実効値)の計算
        amp_rms = np.sqrt(np.mean(xyz * xyz, axis=0)) # 各軸の二乗平均の平方根
        amp_all = np.sqrt(np.sum(amp_rms * amp_rms)) # 全ての軸
        # print("{} [m/s^2]".format(amp_all))

        # フーリエ変換の結果をプロットする場合
        plt.xlabel('Frequency [/s]')
        plt.ylabel('Power')

        z_freq, z_fk, z_maximal_idx = fft(xyz[:, 2])
        z_fk_abs = np.abs(z_fk)

        y_freq, y_fk, y_maximal_idx = fft(xyz[:, 1])
        y_fk_abs = np.abs(y_fk)

        max_val = np.max(z_fk_abs)
        min_val = np.min(z_fk_abs)
        
        
        plt.plot(z_freq, z_fk_abs, label='z-axis abs fft')
        plt.plot(y_freq, y_fk_abs, label='y-axis abs fft')
        

        for i in z_maximal_idx :
          plt.annotate('{0:.0f}Hz, RMS: {1:.0f}m/s^2, Max: {2:.0f}m/s^2 '.format(np.round(z_freq[i]), amp_rms[2], np.max(xyz[:, 2])),
          xy=(z_freq[i], z_fk_abs[i]),
          xytext=(10, 20),
          textcoords='offset points',
          arrowprops=dict(arrowstyle='->', connectionstyle='arc3, rad=.2'))
        
        plt.yticks(np.linspace(min_val, max_val, 10))

        plt.legend()
        plt.grid()
        plt.draw()
        
        
        # 保存ファイルパス確認
        dir_path = os.path.join("data", subject_name, str(vibrator_num))
        # ディレクトリパス を確認 (なかったら作成)
        if not os.path.isdir(dir_path) :
            os.makedirs(dir_path)
        file_path = os.path.join(dir_path, "acceleration-{0}.csv".format(measurement_num))
        # csv 書き出し
        # 毎計測秒 csv に書き出す.
        # np.savetxt(file_path, xyz, delimiter=",", header="x,y,z", fmt="%.16f")
        

        plt.pause(0.1)
        plt.clf()
        
        if (pause) :
            print("pausing...")
            
            print("r waiting...")
            keyboard.wait('r')
            
            vibrator_num += 1
            # 8 回 Pause したら While を抜ける
            if (vibrator_num >= 8) :
                break
            # 次の振動スタート
            measurement_num = 0
            pause = False
            print("start plottting...")