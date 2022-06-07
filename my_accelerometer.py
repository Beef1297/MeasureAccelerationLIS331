FULL_SCALE = 24.0

def convert_to_g(raw_values):
    # LIS331データシートTable 3のSensitivityという値は意味がよくわからない．
    # Sparkfunのサンプルコード(下記2個)でもMeasurement range(最大値)の方を使っているので，それと同様にGに換算する．
    # https://github.com/jenfoxbot/ImpactForceMonitor/blob/master/PythonProgram.py
    # https://github.com/sparkfun/Triple_Axis_Accelerometer_Breakout-LIS332/blob/V_1.2/Firmware/SparkFun_LIS331-v10/main.c
      return raw_values * (2 * FULL_SCALE) / (1 << 16)