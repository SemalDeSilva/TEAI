#include <SpeedyStepper.h>
#include <LiquidCrystal_I2C.h>
#include <Wire.h>
#include "HX711.h"
#include <DHT.h>
#include <math.h>

// ------------------- LCD -------------------
// 16x4 character LCD on I2C address 0x27
LiquidCrystal_I2C lcd(0x27, 16, 4);

// ------------------- DHT SENSOR -------------------
#define DHTPIN 4          // DHT data pin (change if you wired differently)
#define DHTTYPE DHT11     // or DHT22 if you use that
DHT dht(DHTPIN, DHTTYPE);

// ------------------- PINS -------------------
const int LED_PIN             = 13;
const int MOTOR_STEP_PIN      = 8;
const int MOTOR_DIRECTION_PIN = 9;

// Positions in steps (tune these!)
const long HOME_POSITION_STEPS    = 0;
const long CAPTURE_POSITION_STEPS = -320;  // stop under camera (adjust)
const long WEIGH_POSITION_STEPS   = -820;  // stop over load cell (adjust)

// ------------------- STEPPER -------------------
SpeedyStepper stepper;

// ------------------- LOAD CELL (HX711) -------------------
const uint8_t HX_DOUT_PIN = 6;  // data
const uint8_t HX_SCK_PIN  = 7;  // clock
HX711 scale;

// ✅ Your calibration factor from the calibration sketch
#define CALIBRATION_FACTOR  1073.263305f

// ------------------- STATE -------------------
float lastWeight = 0.0;
float lastTemp   = NAN;
float lastHum    = NAN;

// ---------------------------------------------------------
// LCD helper: show instruction on bottom line (line 3)
// ---------------------------------------------------------
void setInstruction(const char* msg)
{
  lcd.setCursor(0, 3);              // bottom line on 16x4
  lcd.print("                ");     // clear line (16 spaces)
  lcd.setCursor(0, 3);
  lcd.print(msg);
}

// ---------------------------------------------------------
// HELPER: move with LED + status
// ---------------------------------------------------------
void moveToPosition(long targetSteps, const char* label)
{
  Serial.print("MOVING: ");
  Serial.println(label);

  setInstruction(label);   // e.g. "CAPTURE", "WEIGH", "HOME"

  digitalWrite(LED_PIN, HIGH);
  stepper.moveToPositionInSteps(targetSteps);
  digitalWrite(LED_PIN, LOW);

  Serial.print("AT_");
  Serial.println(label);   // e.g. "AT_CAPTURE", "AT_WEIGH", "AT_HOME"
}

// ---------------------------------------------------------
// Read stable weight: wait for tea to fall & weight to stop changing
// ---------------------------------------------------------
float readStableWeight()
{
  const int   samples  = 5;      // average N readings each time
  const int   maxLoops = 20;     // safety limit
  const float thresh   = 0.10f;  // grams difference considered "stable"

  // initial wait so tea can fall into tray
  delay(500);

  float prev = scale.get_units(samples);
  for (int i = 0; i < maxLoops; i++)
  {
    delay(200);  // 0.2s between checks
    float cur = scale.get_units(samples);

    if (fabs(cur - prev) < thresh)
    {
      return cur;  // stable
    }
    prev = cur;
  }
  // if still not stable, just return last reading
  return prev;
}

// ---------------------------------------------------------
// HELPER: read DHT sensor (update global lastTemp/lastHum)
// ---------------------------------------------------------
void readDHTSensor()
{
  float h = dht.readHumidity();
  float t = dht.readTemperature();   // °C

  if (!isnan(h)) lastHum = h;
  if (!isnan(t)) lastTemp = t;
}

// ---------------------------------------------------------
// HELPER: read load cell & send result to PC
//          also reads DHT and updates LCD
// ---------------------------------------------------------
void readAndSendMeasurement()
{
  setInstruction("Weighing...");

  float w = readStableWeight();  // grams
  lastWeight = w;

  // Read DHT sensor right after weighing
  readDHTSensor();

  // -------- LCD LAYOUT (16x4) --------
  // Line 0: Weight
  lcd.setCursor(0, 0);
  lcd.print("W:");
  lcd.print(w, 1);
  lcd.print("g       ");

  // Line 1: Temperature
  lcd.setCursor(0, 1);
  lcd.print("T:");
  if (!isnan(lastTemp))
  {
    lcd.print(lastTemp, 1);
    lcd.print("C      ");
  }
  else
  {
    lcd.print("--.-C      ");
  }

  // Line 2: Humidity
  lcd.setCursor(0, 2);
  lcd.print("H:");
  if (!isnan(lastHum))
  {
    lcd.print(lastHum, 1);
    lcd.print("%      ");
  }
  else
  {
    lcd.print("--.-%      ");
  }

  // Line 3: Status
  setInstruction("Done - next sample");

  // -------- SERIAL OUTPUT TO PYTHON --------
  // Example line:
  // MEASURED W=1.23g T=26.5C H=60.2%
  Serial.print("MEASURED ");
  Serial.print("W=");
  Serial.print(w, 1);
  Serial.print("g ");

  Serial.print("T=");
  Serial.print(lastTemp, 1);
  Serial.print("C ");

  Serial.print("H=");
  Serial.print(lastHum, 1);
  Serial.println("%");

  Serial.println("WEIGH_DONE");
}

// ---------------------------------------------------------
// SERIAL COMMAND HANDLER
//   'C' -> move to CAPTURE position   (AT_CAPTURE)
//   'W' -> move to WEIGH position & measure   (AT_WEIGH, MEASURED..., WEIGH_DONE)
//   'H' -> move to HOME position      (AT_HOME)
//   'Z' -> tare (zero) with current tray weight (ZERO_DONE)
// ---------------------------------------------------------
void handleSerial()
{
  if (Serial.available() > 0)
  {
    char cmd = Serial.read();
    Serial.print("CMD RECEIVED: ");
    Serial.println(cmd);

    if (cmd == 'C')
    {
      moveToPosition(CAPTURE_POSITION_STEPS, (char*)"CAPTURE");
    }
    else if (cmd == 'W')
    {
      moveToPosition(WEIGH_POSITION_STEPS, (char*)"WEIGH");
      readAndSendMeasurement();
    }
    else if (cmd == 'H')
    {
      moveToPosition(HOME_POSITION_STEPS, (char*)"HOME");
      setInstruction("Place sample");
    }
    else if (cmd == 'Z')
    {
      // Tare (zero) with tray in current state
      setInstruction("Taring...");
      Serial.println("TARING");
      scale.tare(20);
      lastWeight = 0.0;

      // Update LCD top line to show 0g
      lcd.setCursor(0, 0);
      lcd.print("W:0.0g        ");

      setInstruction("Tray zeroed");
      Serial.println("ZERO_DONE");
    }
  }
}

// ---------------------------------------------------------
// SETUP
// ---------------------------------------------------------
void setup()
{
  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Tea AI Scale...");
  delay(1500);
  lcd.clear();

  pinMode(LED_PIN, OUTPUT);

  Serial.begin(115200);
  Serial.println("BOOTING...");

  // Stepper
  stepper.connectToPins(MOTOR_STEP_PIN, MOTOR_DIRECTION_PIN);
  stepper.setSpeedInStepsPerSecond(800);
  stepper.setAccelerationInStepsPerSecondPerSecond(250);
  stepper.setCurrentPositionInSteps(HOME_POSITION_STEPS);

  // Load cell
  scale.begin(HX_DOUT_PIN, HX_SCK_PIN);
  scale.set_scale(CALIBRATION_FACTOR);
  scale.tare(20);   // initial tare (tray should be empty at first boot)
  lastWeight = 0.0;

  // DHT sensor
  dht.begin();

  // LCD initial state
  lcd.setCursor(0, 0);
  lcd.print("W:0.0g        ");
  lcd.setCursor(0, 1);
  lcd.print("T:--.-C       ");
  lcd.setCursor(0, 2);
  lcd.print("H:--.-%       ");
  setInstruction("Place sample");

  Serial.println("READY");
}

// ---------------------------------------------------------
// LOOP
// ---------------------------------------------------------
void loop()
{
  // keep showing last weight
  lcd.setCursor(0, 0);
  lcd.print("W:");
  lcd.print(lastWeight, 1);
  lcd.print("g    ");

  // refresh DHT on LCD every 2 seconds
  static unsigned long lastDHTms = 0;
  if (millis() - lastDHTms > 2000)
  {
    readDHTSensor();

    lcd.setCursor(0, 1);
    lcd.print("T:");
    if (!isnan(lastTemp))
    {
      lcd.print(lastTemp, 1);
      lcd.print("C   ");
    }
    else
    {
      lcd.print("--.-C   ");
    }

    lcd.setCursor(0, 2);
    lcd.print("H:");
    if (!isnan(lastHum))
    {
      lcd.print(lastHum, 1);
      lcd.print("%   ");
    }
    else
    {
      lcd.print("--.-%   ");
    }

    lastDHTms = millis();
  }

  // Handle serial commands from Python
  handleSerial();
}
