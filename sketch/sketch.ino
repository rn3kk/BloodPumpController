const int pwm_pin = 3;

const int max_v = 255;  //from 0..255  
const int min_v = 75;  // from 0..255 
const float freq = 0.0015;


void setup() {
  pinMode(pwm_pin, OUTPUT);

}

void loop() {  
  int value = abs(sin(millis() * freq)) * (max_v-min_v) + min_v;
  analogWrite(pwm_pin, value);  
  
}
