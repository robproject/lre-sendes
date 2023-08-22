#include <Arduino.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>


LiquidCrystal_I2C lcd(32, 16, 2);

#define US A0 // the FSR and 10K pulldown are connected to A0
#define DS A1
#define Pot A2

float D1 = 1;
float D2 = .5;
float rho = 1;
float d = D2/D1;

unsigned long t1 = 0;
int Pot_read1 = 0;
  
void setup() {
  Serial.begin(9600);
  
  lcd.init();
  lcd.begin(16,2);
  lcd.backlight();
  
  Pot_read1 = analogRead(Pot);
  t1 = millis();
}

void loop() {
  
  delay(300);
  
  unsigned long t2 = millis();
  int Pot_read2 = analogRead(Pot);
  
  int P1 = analogRead(US);
  int P2 = analogRead(DS);
  
  float Pot_read = Pot_read2 - Pot_read1;
  float t = t2 - t1;
    
  float q = Pot_read / t;
  
  float cd = q / (M_PI / 4 * pow(D2,2) * pow(2 * (P1-P2) / (rho * (1-pow(d,4))), .5));

  
  lcd.setCursor(0,0);
  lcd.print("US: ");
  lcd.print(P1);
  lcd.print(" DS: ");
  lcd.print(P2);
  lcd.print("  ");
  lcd.setCursor(0,1);
  lcd.print("Pot: ");
  lcd.print(Pot_read1);
  lcd.print(" Cd: ");
  lcd.print(cd);

  t1 = t2;
  Pot_read1 = Pot_read2;
}
