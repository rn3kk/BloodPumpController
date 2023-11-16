#include <HX710.h>
#include <EEPROM.h>

const int pwm_pin = 3;
const int DOUT_D1 = 5;              // Указываем вывод OUT датчика 1
const int SCLK_D1  = 6;             // Указываем вывод CLK датчика 1

const int PRE1_PWM = 7; //если замкнут этот пин то помимо измерений будет работаь управление мотором
const int PRE2 = 8;
const int PRE3 = 9;

HX710 ps;

int max_v = 255;  //from 0..255
int hear_rate = 0; //in minutes
int min_v = 0;  // from 0..255


float Vref = 5;  //volt
double hear_ms = 0.0015;
const float pi = 3.141619;

const String ADC_ = "adc";
const String PREASURE = "pre";
const String RATE_ = "rte";
const String MIN_ = "min";
const String MAX_ = "max";
const String CALIBRATED_OK = "calOK";
const String ZERO_COEF_1 = "zero1=";
const String ZERO_COEF_2 = "zero2=";

const int EE_ADR_MIN = 1;
const int EE_ADR_MAX = 2;
const int EE_ADR_RATE = 3;
int start_measure = 0;

String PRE_NUM = "UNKN";

unsigned long start_measure_time = 0;

bool isMain = false;

void setup() {
  pinMode(PRE1_PWM, INPUT_PULLUP);
  pinMode(PRE2, INPUT_PULLUP);
  pinMode(PRE3, INPUT_PULLUP);
  pinMode(pwm_pin, OUTPUT);   
  Serial.begin(9600);
  max_v = EEPROM.read(EE_ADR_MAX);
  min_v = EEPROM.read(EE_ADR_MIN);
  hear_rate = EEPROM.read(EE_ADR_RATE);    
  hear_ms = calculate_hear_ms(hear_rate); 
  ps.initialize( SCLK_D1 , DOUT_D1 );
  
  int p1 = digitalRead(PRE1_PWM);
  int p2 = digitalRead(PRE2);
  int p3 = digitalRead(PRE3);
  
  if(p1 == 0){
    PRE_NUM = "1";
    isMain = true;
  }
  else if(p2 ==0){
    PRE_NUM = "2";    
  }
  else if(p3 ==0){
    PRE_NUM = "3";    
  }
    
}

float calculate_hear_ms(int rate)
{
  float h = rate/60.0;
  h = h/float(1000.0);
  return h*pi;    
}

void pwm_set(){  
  int value = abs(sin( millis() * hear_ms )) * (max_v-min_v) + min_v;  
  analogWrite(pwm_pin, value);   
}
  
void loop() {  
  if(isMain)
    pwm_set();      
  
  if (Serial.available() > 0) {
    String str = Serial.readString();
    str.remove('\n');
    if(str.indexOf("sta") >= 0){
      start_measure = 1;
      start_measure_time = millis();
    }
    else if(str.indexOf("sto") >= 0){
      start_measure = 0;
      start_measure_time = 0;
    }
    else if(str.indexOf("get") >= 0)
    {
      if(isMain){
        String mi=  MIN_ + PRE_NUM + String(min_v) + "\n";
        String ma = MAX_ + PRE_NUM +String(max_v) +"\n";
        String he = RATE_+ PRE_NUM + String(hear_rate) +"\n";        
        Serial.print(mi);
        Serial.print(ma);
        Serial.print(he); 
        Serial.flush();       
      }      
    }
    else if(isMain && str.indexOf(MAX_) == 0)
    {      
      max_v = str.substring(3, str.length()).toInt();
      if(max_v > 255 || max_v < 0)
      {
        max_v = 255;
      }
      EEPROM.write(EE_ADR_MAX, max_v);
      String ma = MAX_ + PRE_NUM  + String(max_v) +"\n";
      Serial.print(ma);
    }
    else if(isMain && str.indexOf(MIN_) == 0)
    {
      min_v = str.substring(3, str.length()).toInt();
      if(min_v < 0 || min_v > 255)
      {
        min_v = 0;
      }
      EEPROM.write(EE_ADR_MIN, min_v);
      String mi=  MIN_ + PRE_NUM  + String(min_v) + "\n";
      Serial.print(mi);
    }
    else if(isMain && str.indexOf(RATE_) == 0)
    {
      hear_rate = str.substring(3, str.length()).toInt();      
      hear_ms = calculate_hear_ms(hear_rate);
      EEPROM.write(EE_ADR_RATE, hear_rate);
      String he = RATE_ + PRE_NUM  + String(hear_rate) +"\n";
      Serial.print(he);   
    }       
  }   
  
  if (start_measure == 1 and ps.isReady()){
      ps.readAndSelectNextData( HX710_DIFFERENTIAL_INPUT_40HZ );
      double m = ps.getLastDifferentialInput() /10000.0;
      unsigned long time_diff = millis() - start_measure_time;
      Serial.print(PREASURE + PRE_NUM + " " +String(time_diff) + " " + String(m,1) + "\n");
      Serial.flush();
  }
  else if (start_measure == 0 and ps.isReady()){
      ps.readAndSelectNextData( HX710_DIFFERENTIAL_INPUT_40HZ );
      double m = ps.getLastDifferentialInput() /10000.0;      
  }

  
}
