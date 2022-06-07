# -*- coding: utf-8 -*-
"""
Created on Tue Nov  5 17:23:58 2019

@author: ushiyama
"""

import os
import sys
from datetime import datetime
import numpy as np
import math
import time
from enum import Enum
# keyboard input event handling のため
from pynput.keyboard import Listener
import keyboard

# custom utility
import experiment_utils3
import my_accelerometer
import my_serial
import my_osc_client

SAMPLING_RATE = 1000.0  # 1kHz

subject_name = ""
measurement_num = 0
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

class vibrator_id(Enum):
    ELBOW_F = "elbow_flexor"
    ELBOW_E = "elbow_extensor"
    WRIST_F = "wrist_flexor"
    WRIST_E = "wrist_extensor"


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    
    port_name = "COM6"
    duration = 0.1 # 0.5Hzのため
    record_id = 1

    if len(sys.argv) > 1:
      port_name = sys.argv[1]
    if len(sys.argv) > 2:
      duration = float(sys.argv[2])
    if (subject_name == "") :
        print("input subject name")
        subject_name = input()

    dir_path = os.path.abspath(
        os.path.join("..", "..", "experiments", "ShapeModulation", "Acceleration", subject_name, str(record_id)))
    print("save path is... {0}. Check!".format(dir_path))

    # keyboard 入力の callback 登録
    listener = Listener(on_press=keypress_callback)
    listener.start()
    
    # グラフをバックエンドで更新するために fig と line をあらかじめ作成する
    plt.ion() # interactive on
    fig = plt.figure()
    canvas = fig.canvas
    ax = plt.subplot(111)
    plt.legend()
    ax.grid()
    xlabel = ax.set_xlabel('Time [s]')
    print(type(xlabel))
    ax.set_ylabel('Acceleration [m/s^2]')
    xyz = []
    t = []
    (ln, ) = ax.plot(t, xyz)
    fig.show()

    # 振動提示を開始する
    my_osc_client.set_all_frequency(70)
    my_osc_client.gate_on_only_one_vibrator(record_id)
    my_osc_client.audio_on()

    while True:
        # ループの回数
        measurement_num += 1

        data = my_serial.measure(port_name, int(duration * SAMPLING_RATE)) 
        xyz = my_accelerometer.convert_to_g(np.array(data))
        t = np.arange(0, duration, 1.0 / SAMPLING_RATE)
        
        # Gからm/s^2に換算
        xyz *= 9.8        
        print("plot graph")
        # plt.plot(t, xyz[:, 0], label='x')
        # plt.plot(t, xyz[:, 1], label='y')
        # plt.plot(t, xyz[:, 2], label='z')
        ln.set_data(t, xyz[:, 2])
        
        # 重力成分(平均値)を除去
        xyz -= np.mean(xyz, axis=0)

        max_z = max(xyz[:, 2])
        min_z = min(xyz[:, 2])
        amplitude_z = (max_z - min_z) / 2 
        # 振幅を計算 (1/2をしないと peak-to-peakになる)
        # 偏りが出てしまう可能性があるので，平均値をとって 0-p (zero-to-peak) とする
        my_osc_client.adjust_vibration_volume(amplitude_z, record_id)

        # 本当はグラフ内にテキストで表示したいがplt.clf()をしないため，更新が面倒
        # label で振幅を確認する
        xlabel.set_text("{0};amp [m/s^2]: {1}".format(measurement_num, amplitude_z))
        # plt.draw()
        t_xyz = np.hstack((t[:, np.newaxis], xyz))
        print(t_xyz.shape)
        # 保存ファイルパス確認
        experiment_utils3.save_csv(dir_path, measurement_num, t_xyz)
        
        
        # 振幅(実効値)の計算
        #amp_rms = np.sqrt(np.mean(xyz * xyz, axis=0)) # 各軸の二乗平均の平方根
        #amp_all = np.sqrt(np.sum(amp_rms * amp_rms)) # 全ての軸
        #print("{} [m/s^2]".format(amp_all))

        # https://stackoverflow.com/questions/44278369/how-to-keep-matplotlib-python-window-in-background
        # これを参考に relim と autoscale_view, canvas.flush_events() を実行

        ax.relim() 
        ax.autoscale_view()
        try :
            fig.canvas.flush_events() # 描画の更新
        except:
            my_osc_client.audio_off()
            exit()
            # raise Exception("graph windows closed")
        time.sleep(0.1)

        # plt.pause(0.5)
        # plt.clf()
                
        if (pause) :
            print("pausing...")
            my_osc_client.gate(int((record_id + 1)/2), 0)

            print("r waiting...")
            keyboard.wait('r')

            record_id += 1
            if ((record_id % 2) == 1) :
                my_osc_client.set_all_frequency(70)
            else :
                my_osc_client.set_all_frequency(220)
            
            # 8 回 Pause したら While を抜ける
            if (record_id > 16) :
                path = os.path.join("..", "..", "experiments", "ShapeModulation", "Acceleration", subject_name)
                my_osc_client.save_volume_pattern(path)
                break

            dir_path = os.path.abspath(
            os.path.join("..", "..", "experiments", "ShapeModulation", "Acceleration", subject_name, str(record_id)))
            print("save path is... {0}. Check!".format(dir_path))
            # 次の振動スタート
            measurement_num = 0
            pause = False
            my_osc_client.gate(int((record_id + 1)/2), 1)

            print("start plottting...")