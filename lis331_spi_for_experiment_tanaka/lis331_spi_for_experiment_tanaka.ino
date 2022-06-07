#include <SPI.h>
#include <Wire.h>
#include <stdint.h>

#define SCLK 18
#define MOSI 23
#define MISO 19
#define CS 5

#define SDA_PIN 21
#define SCL_PIN 22
#define INT1_PIN 17
#define DEBUG_PIN 32

const uint8_t CTRL_REG1 = 0x20;
const uint8_t CTRL_REG4 = 0x23;
const uint8_t OUT_X_L = 0x28;
const uint8_t OUT_X_H = 0x29;
const uint8_t OUT_Y_L = 0x2A;
const uint8_t OUT_Y_H = 0x2B;
const uint8_t OUT_Z_L = 0x2C;
const uint8_t OUT_Z_H = 0x2D;

static uint8_t i2cAddr = 0x18;
static uint8_t CSPin = CS;

// FOR_DEBUG
int count = 0;

// hard ware timer for logging accelerometer, ADXL345
hw_timer_t *timer = NULL;

typedef enum {
  USE_I2C,
  USE_SPI
} comm_mode;

comm_mode useMode;

typedef enum {
  POWER_DOWN,
  NORMAL
} power_mode;

typedef enum {
  G6_RANGE,
  G12_RANGE,
  NO_RANGE,
  G24_RANGE
} fs_range;

typedef enum {
  DR_50HZ,
  DR_100HZ,
  DR_400HZ,
  DR_1000HZ
} data_rate;

void LIS331_read(uint8_t reg_address, uint8_t *data, uint8_t len) {

  if (useMode == comm_mode::USE_I2C) {
    Wire.beginTransmission(i2cAddr);
    Wire.write(reg_address);
    Wire.endTransmission();
    Wire.requestFrom(i2cAddr, len);
    for (int i = 0; i < len; i++) {
      data[i] = Wire.read();
    }
  } else {
    // SPI read handling code
    digitalWrite(CSPin, LOW);
    SPI.transfer(reg_address | 0xC0);
    for (int i = 0; i < len; i++) {
      data[i] = SPI.transfer(0);
    }
    digitalWrite(CSPin, HIGH);
  }

}

void LIS331_write(uint8_t reg_address, uint8_t *data, uint8_t len) {

  if (useMode == comm_mode::USE_I2C) {
    Wire.beginTransmission(i2cAddr);
    Wire.write(reg_address);
    for (int i = 0; i < len; i++) {
      Wire.write(data[i]);
    }
    Wire.endTransmission();
  } else {
    // SPI write handling code
    digitalWrite(CSPin, LOW);
    SPI.transfer(reg_address | 0x40);
    for (int i = 0; i < len; i++) {
      SPI.transfer(data[i]);
    }
    digitalWrite(CSPin, HIGH);
  }
}

void setPowerMode(power_mode pmode) {
  uint8_t data;
  LIS331_read(CTRL_REG1, &data, 1);
  data &= ~0xe0; // 先頭3bit をクリアする
  data |= pmode << 5; // 先頭3bit が powermode なのかな？
  LIS331_write(CTRL_REG1, &data, 1);
}

void axesEnable(bool enable) {
  uint8_t data;
  LIS331_read(CTRL_REG1, &data, 1);
  if (enable) {
    data |= 0x07;
  } else {
    data &= ~0x07;
  }
  LIS331_write(CTRL_REG1, &data, 1);
}

void setFullScale(fs_range range) {
  uint8_t data;
  LIS331_read(CTRL_REG4, &data, 1);
  data &= ~0xcf;
  data |= range << 4;
  LIS331_write(CTRL_REG4, &data, 1);
}

void setODR(data_rate drate) {
  uint8_t data;
  LIS331_read(CTRL_REG1, &data, 1);

  data &= ~0x18;
  data |= drate << 3;
  LIS331_write(CTRL_REG1, &data, 1);
}

void setBDU(bool bdu) {
  uint8_t data;
  LIS331_read(CTRL_REG4, &data, 1);
  data &= ~0x80;  // clear BDU
  data |= (bdu ? 0x80 : 0x00);  // set BDU if bdu==true
  LIS331_write(CTRL_REG4, &data, 1);
}

void readAxesRaw(int16_t &x, int16_t &y, int16_t &z) {
  uint8_t data[6];
  LIS331_read(OUT_X_L, &data[0], 1);
  LIS331_read(OUT_X_H, &data[1], 1);
  LIS331_read(OUT_Y_L, &data[2], 1);
  LIS331_read(OUT_Y_H, &data[3], 1);
  LIS331_read(OUT_Z_L, &data[4], 1);
  LIS331_read(OUT_Z_H, &data[5], 1);

  // 2の補数表現なのでそのまま正負になるはず
  x = (data[1] << 8) | data[0];
  y = (data[3] << 8) | data[2];
  z = (data[5] << 8) | data[4];
}

void readZ(int16_t &z) {
  uint8_t data[2];
  LIS331_read(OUT_Z_L, &data[0], 1);
  LIS331_read(OUT_Z_H, &data[1], 1);

  z = data[0] | data[1] << 8;
  z = z >> 4;
}

void LIS331_begin(comm_mode cmode) {
  useMode = cmode;

  setPowerMode(power_mode::NORMAL);
  axesEnable(true);
  setODR(data_rate::DR_1000HZ);
  uint8_t data = 0;
  for (int i = 0x21; i < 0x25; i++) {
    LIS331_write(i, &data, 1);
  }
  for (int i = 0x30; i < 0x37; i++) {
    LIS331_write(i, &data, 1);
  }

  setFullScale(fs_range::G24_RANGE);

  // 16bitのうち片方の8bitが読まれた後，もう片方が読まれるまで更新しない
  // (センサ内で書き込み中に読み出されてデータが壊れることを防ぐ)
  // データシートの7.4末尾を参照
  setBDU(true);
}

// データシートTable 3のSensitivityという値は意味がよくわからない．
// Sparkfunのサンプルコード(下記2個)でもMeasurement range(最大値)の方を使っているので，それと同じような計算を使う．
//  https://github.com/jenfoxbot/ImpactForceMonitor/blob/master/PythonProgram.py
//  https://github.com/sparkfun/Triple_Axis_Accelerometer_Breakout-LIS331/blob/V_1.2/Firmware/SparkFun_LIS331-v10/main.c
// ただし割り込みハンドラ内でfloatの演算をすると落ちるので(https://esp32.com/viewtopic.php?t=1292 参照)，
// doubleの定数としておく
const int maxScale = 24;
const double raw_to_g = 2.0 * maxScale / (1 << 16);

bool active = false;

void IRAM_ATTR sendData() {
  if (!active) {
    return; // 計測停止中は何もしない

  }
  
  int16_t rx, ry, rz; // reading value
  uint8_t send_data[6];
//  double ax, ay, az;
//  double gx, gy, gz;
//  const int max_g = 24;
  
  readAxesRaw(rx, ry, rz);
  /*
  Serial.print(rx * raw_to_g);
  Serial.print(",");
  Serial.print(ry * raw_to_g);
  Serial.print(",");
  Serial.print(rz * raw_to_g);
  Serial.println();
  */
  // 変換せずそのままPCに送る
  send_data[0] = (rx & 0xFF00) >> 8;
  send_data[1] = rx & 0x00FF;
  send_data[2] = (ry & 0xFF00) >> 8;
  send_data[3] = ry & 0x00FF;
  send_data[4] = (rz & 0xFF00) >> 8;
  send_data[5] = rz & 0x00FF;
  Serial.write(send_data, 6);

//  count = (count + 1) % 2;
//  if (count) {
//    digitalWrite(DEBUG_PIN, HIGH);
//  } else {
//    digitalWrite(DEBUG_PIN, LOW);
//  }
}

void setup() {

  pinMode(DEBUG_PIN, OUTPUT); // for debug

  pinMode(CS, OUTPUT);
  digitalWrite(CS, HIGH);
  pinMode(MOSI, OUTPUT);
  pinMode(MISO, INPUT);
  pinMode(SCLK, OUTPUT);
  SPI.begin(SCLK, MISO, MOSI, CS);
  SPI.setFrequency(4000000);

  LIS331_begin(comm_mode::USE_SPI);

  /*
    // I2C setup

    int freq = 400000;
    Wire.begin(SDA_PIN, SCL_PIN, freq);

  */
//  Serial.begin(921600);
  Serial.begin(115200);

  // timer setup

  timer = timerBegin(0, 80, true); // 1 us
  timerAttachInterrupt(timer, &sendData, true);
  timerAlarmWrite(timer, 1000, true); // 1000us -> 1ms loop
  timerAlarmEnable(timer);
}

void loop() {
  if (Serial.available()) {
    char chr = Serial.read();
    if (chr == 's') {
      active = true;  // 計測開始
    } else if (chr == 'e') {
      active = false; // 計測停止
    }
  }

  delay(1);
}
