#include "HX711.h"

HX711 scale;

// adjust pins if needed
const uint8_t DATA_PIN  = 6;
const uint8_t CLOCK_PIN = 7;

// put your known weight here (in grams)
const float KNOWN_WEIGHT = 505.0;   // e.g. 425 g

void waitForKey(const char *msg)
{
  Serial.println(msg);
  while (!Serial.available());
  while (Serial.available()) Serial.read();  // clear buffer
}

void setup()
{
  Serial.begin(115200);
  Serial.println();
  Serial.println("HX711 CALIBRATION SKETCH");

  scale.begin(DATA_PIN, CLOCK_PIN);

  // 1) Show raw units with nothing
  Serial.println("Reading raw units (no calibration yet)...");
  Serial.print("UNITS (no tare): ");
  Serial.println(scale.get_units(10));

  // 2) Tare with empty scale
  waitForKey("Empty the scale (no weight) and press any key...");
  scale.tare(20);  // average of 20 samples
  Serial.println("TARE DONE.");
  Serial.print("UNITS after tare (should be near 0): ");
  Serial.println(scale.get_units(10));

  // 3) Place known weight
  waitForKey("Place known weight on the scale and press any key...");
  
  // Option A: let library compute calibration factor:
  // scale.calibrate_scale(KNOWN_WEIGHT, 20);

  // Option B: do manual computation to show you what's happening:
  long raw = scale.read_average(20);
  long offset = scale.get_offset();
  long net = raw - offset;

  float calibrationFactor = (float)net / KNOWN_WEIGHT;
  scale.set_scale(calibrationFactor);

  Serial.println();
  Serial.println("CALIBRATION DONE.");
  Serial.print("Raw reading: ");
  Serial.println(raw);
  Serial.print("Offset: ");
  Serial.println(offset);
  Serial.print("Net: ");
  Serial.println(net);
  Serial.print("Calibration factor: ");
  Serial.println(calibrationFactor, 6);

  Serial.print("Check get_units(): ");
  Serial.println(scale.get_units(10));  // should be ~KNOWN_WEIGHT

  Serial.println();
  Serial.println(">>> COPY THIS VALUE into your main code as CALIBRATION_FACTOR <<<");
}

void loop()
{
  // just keep showing the weight in grams
  float w = scale.get_units(5);
  Serial.print("Weight: ");
  Serial.print(w, 2);
  Serial.println(" g");
  delay(1000);
}
