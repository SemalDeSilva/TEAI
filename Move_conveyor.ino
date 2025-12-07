
//      ******************************************************************
//      *                                                                *
//      *       Using "absolute" moves to position a stepper motor       *
//      *                                                                *
//      *            S. Reifel & Co.                6/24/2018            *
//      *                                                                *
//      ******************************************************************


// This example is similar to Example 1 except that is uses "absolute" 
// moves instead of "relative" ones.  Relative moves will use a coordinate 
// system that is relative to the motor's current position.  Absolute moves 
// use a coordinate system that is referenced to the original position of 
// the motor when it is turned on.
//
// For example moving relative 200 steps, then another 200, then another  
// 200 will turn 600 steps in total (and end up at an absolute position of 
// 600).
//
// However issuing an absolute move to position 200 will rotate forward one   
// rotation.  Then running the next absolute move to position 400 will turn  
// just one more revolution in the same direction.  Finally moving to position 0  
// will rotate backward two revolutions, back to the starting position.
//  
//
// Documentation for this library can be found at:
//    https://github.com/Stan-Reifel/SpeedyStepper
//
//
// This library requires that your stepper motor be connected to the Arduino 
// using drive electronics that has a "Step and Direction" interface.  
// Examples of these are:
//
//    Pololu's DRV8825 Stepper Motor Driver Carrier:
//        https://www.pololu.com/product/2133
//
//    Pololu's A4988 Stepper Motor Driver Carrier:
//        https://www.pololu.com/product/2980
//
//    Sparkfun's Big Easy Driver:
//        https://www.sparkfun.com/products/12859
//
//    GeckoDrive G203V industrial controller:
//        https://www.geckodrive.com/g203v.html
//
// For all driver boards, it is VERY important that you set the motor 
// current before running the example.  This is typically done by adjusting
// a potentiometer on the board.  Read the driver board's documentation to 
// learn how.

// ***********************************************************************


#include <SpeedyStepper.h>


//
// pin assignments
//
const int LED_PIN = 13;
const int MOTOR_STEP_PIN = 8;
const int MOTOR_DIRECTION_PIN = 9;


//
// create the stepper motor object
//
SpeedyStepper stepper;



void setup() 
{
  //
  // setup the LED pin and enable print statements
  //
  pinMode(LED_PIN, OUTPUT);   
  Serial.begin(9600);


  //
  // connect and configure the stepper motor to its IO pins
  //
  stepper.connectToPins(MOTOR_STEP_PIN, MOTOR_DIRECTION_PIN);


  stepper.setSpeedInStepsPerSecond(800);
  stepper.setAccelerationInStepsPerSecondPerSecond(300);
  stepper.moveToPositionInSteps(-300);
}



void loop() 
{




  // stepper.setSpeedInStepsPerSecond(1250);
  // stepper.setAccelerationInStepsPerSecondPerSecond(800);
  // stepper.moveToPositionInSteps(0);
  delay(2000);
}




