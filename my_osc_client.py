import numpy as np
from pythonosc import udp_client
import os

# OSC で使う それぞれの振動子のルート
VIBRATOR_ADDRESS = {
        1 : "/1",
        2 : "/2",
        3 : "/3",
        4 : "/4",
        5 : "/5",
        6 : "/6",
        7 : "/7",
        8 : "/8",
}
# self.subject_name = subject_name_

IP_ADDRESS = "127.0.0.1"
OSC_PORT = 3333
oscclient = udp_client.SimpleUDPClient(IP_ADDRESS, OSC_PORT)

# Max で設定するそれぞれの振動子のボリューム
vibrator_volumes_70hz = {
        1 : 0.51,
        2 : 0.225,
        3 : 0.5,
        4 : 0.5,
        5 : 0.3,
        6 : 0.3,
        7 : 0.5,
        8 : 0.2
}

vibrator_volumes_220hz = {
        1 : 0.21,
        2 : 0.225,
        3 : 0.2,
        4 : 0.2,
        5 : 0.3,
        6 : 0.3,
        7 : 0.2,
        8 : 0.2
}

TARGET_ACCELERATION = 80 # m/s^2

# send osc message
def send_message(addr, val) :
    '''
    # for bundle
    msg = osc_message_builder.OscMessageBuilder(address=addr)
    msg.add_arg(val)
    msg = msg.build()
    self.oscclient.send(msg)
    '''
    oscclient.send_message(addr, val)
    return 

def set_all_frequency(freq) :
    for key, val in VIBRATOR_ADDRESS.items() :
        path = val + "/freq"
        oscclient.send_message(path, freq)

def set_scalar_volume(index, val) :
    path = VIBRATOR_ADDRESS[index] + "/amp"
    send_message(path, val)
    return

def set_volume(iaddr, ivol) :
    path = VIBRATOR_ADDRESS[iaddr] + "/amp"
    send_message(path, vibrator_volumes_70hz[ivol])
    return

def save_acceleration(path, xyz) :
    np.savetxt(path, xyz, delimiter=",", 
            header="x,y,z", fmt="%.16f")
    return

def audio_on() :
    path = "/on"
    send_message(path, 1)
    return

def audio_off() :
    path = "/on"
    send_message(path, 0)
    return

def gate(index, val) :
    path = VIBRATOR_ADDRESS[index] + "/gate"
    send_message(path, val)

def gate_on_only_one_vibrator(index) :
    for i, address in enumerate(VIBRATOR_ADDRESS.values()) :
        path = address + "/gate"
        if i == (index-1): 
            send_message(path, 1)
        else:
            send_message(path, 0)
            

# [OSC] Max の 全ての振動の Volume をセットする
# @param dict addresses : key が 振動子番号, val osc アドレス
# @param dict volumes   : key が 振動子眼豪, val volume 
def set_all_volume_70hz() :
    for key, val in vibrator_volumes_70hz.items() :
        path = VIBRATOR_ADDRESS[key] + "/amp"
        send_message(path, val)
    return

def save_volume_pattern(path) :
    # dict values を 配列化
    volume_70hz = np.array(list(vibrator_volumes_70hz.values()))
    volume_220hz = np.array(list(vibrator_volumes_220hz.values()))
    volumes = np.vstack((volume_70hz, volume_220hz))
    # csv 書き出し : 2D-array に reshape することで，行として書き出す
    np.savetxt(os.path.join(path, "vibration-volume.csv"), 
    volumes.reshape(2, volume_70hz.size) , delimiter=",",
            header="1,2,3,4,5,6,7,8",fmt="%.18f")
    
    # While 抜けたら volume の係数を表示
    print(volumes)
    return

def adjust_vibration_volume(v_amp, index) :
    step = 0.005
    
    i = int((index + 1) / 2.0)
    # ここで計測加速度をMaxへフィードバックする

    if ((index % 2) == 1) :
        if (v_amp > TARGET_ACCELERATION) :
            vibrator_volumes_70hz[i] -= step
            path = VIBRATOR_ADDRESS[i] + "/amp"
            send_message(path, vibrator_volumes_70hz[i])
            
        if (v_amp < TARGET_ACCELERATION) :
            vibrator_volumes_70hz[i] += step
            path = VIBRATOR_ADDRESS[i] + "/amp"
            send_message(path, vibrator_volumes_70hz[i])
    else :
        if (v_amp > TARGET_ACCELERATION) :
            vibrator_volumes_220hz[i] -= step
            path = VIBRATOR_ADDRESS[i] + "/amp"
            send_message(path, vibrator_volumes_220hz[i])
            
        if (v_amp < TARGET_ACCELERATION) :
            vibrator_volumes_220hz[i] += step
            path = VIBRATOR_ADDRESS[i] + "/amp"
            send_message(path, vibrator_volumes_220hz[i])
    return 