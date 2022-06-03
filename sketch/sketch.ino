const int pwm_pin = 3;

const int max_v = 255;  //from 0..255  
const int min_v = 0;  // from 0..255 
const float hear_rate = 60; //in minutes


float hear_ms;
const float pi = 3.141619

void setup() {
  pinMode(pwm_pin, OUTPUT);
  hear_ms = hear_rate/60/1000;

}

void loop() {  
  int value = abs(sin( millis() * hear_ms * pi )) * (max_v-min_v) + min_v;
  analogWrite(pwm_pin, value);  
}
