import numpy as np
from pythonosc import udp_client
import os

class e_utility_vib2 :

    def __init__ (self, subject_name_) :

        self.subject_name = subject_name_

        OSC_IP = "127.0.0.1"
        OSC_PORT = 8000
        self.oscclient = udp_client.SimpleUDPClient(OSC_IP, OSC_PORT)
        # OSC で使う それぞれの振動子のルート
        self.OSC_VIBRATOR_ADDRESS = {
                1 : "/vibrators/1",
                2 : "/vibrators/2",
                3 : "/vibrators/3",
                4 : "/vibrators/4",
                5 : "/vibrators/5",
                6 : "/vibrators/6",
                7 : "/vibrators/7",
        }
        # Max で設定するそれぞれの振動子のボリューム
        self.VIBRATOR_VOLUME = {
                1 : 1.0,
                2 : 1.0,
                3 : 0.02,
                4 : 0.01,
                5 : 0.01,
                6 : 0.01,
                7 : 0.01,
        }

        self.TARGET_ACCELERATION = 100 # m/s^2
        return 

    # send osc message
    def send_osc_msg(self, addr, val) :
        '''
        # for bundle
        msg = osc_message_builder.OscMessageBuilder(address=addr)
        msg.add_arg(val)
        msg = msg.build()
        self.oscclient.send(msg)
        '''
        self.oscclient.send_message(addr, val)
        return 

    def set_scalar_volume(self, index, val) :
        self.send_osc_msg(self.OSC_VIBRATOR_ADDRESS[index], val)
        return

    def set_volume(self, iaddr, ivol) :
        self.send_osc_msg(self.OSC_VIBRATOR_ADDRESS[iaddr], self.VIBRATOR_VOLUME[ivol])
        return

    def saveAcceleration(self, path, xyz) :
        np.savetxt(path, xyz, delimiter=",", 
                header="x,y,z", fmt="%.16f")
        return

    # [OSC] Max の 全ての振動の Volume をセットする
    # @param dict addresses : key が 振動子番号, val osc アドレス
    # @param dict volumes   : key が 振動子眼豪, val volume 
    def setAllVolume(self) :
        for key, val in self.VIBRATOR_VOLUME.items() :
            self.send_osc_msg(self.OSC_VIBRATOR_ADDRESS[key], val)
        return

    def saveVolumePattern(self) :
        # dict values を 配列化
        volume = np.array(list(self.VIBRATOR_VOLUME.values()))
        # csv 書き出し : 2D-array に reshape することで，行として書き出す
        np.savetxt(os.path.join("data", self.subject_name, "vibration-volume.csv"), volume.reshape(1, volume.size) , delimiter=",",
                header="1,2,3,4,5,6,7",fmt="%.18f")
        # While 抜けたら volume の係数を表示
        print(self.VIBRATOR_VOLUME.values())
        return

    def adjustVibrationVol(self,v_amp, step, index) :
        # ここで計測加速度をMaxへフィードバックする
        # ---
        # P制御ぐらいはしても良いと思うが，下手に発振してしまうなら
        # 時間をかけてでもしっかりと調整できるようにすべき
        if (v_amp > self.TARGET_ACCELERATION) :
            self.VIBRATOR_VOLUME[index] -= step
            self.send_osc_msg(self.OSC_VIBRATOR_ADDRESS[index], self.VIBRATOR_VOLUME[index])
            
        if (v_amp < self.TARGET_ACCELERATION) :
            self.VIBRATOR_VOLUME[index] += step
            self.send_osc_msg(self.OSC_VIBRATOR_ADDRESS[index], self.VIBRATOR_VOLUME[index])
        return 
    