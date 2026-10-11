// Pin D2 will act as our physical trigger
const int interruptPin = 2; 

// The volatile keyword tells the compiler this variable can change at any time (via interrupt)
volatile bool potholeDetected = false;

// The interrupt service routine (ISR). This runs instantly when the hardware triggers.
// IRAM_ATTR keeps this function in RAM for lightning-fast execution on the ESP32.
void IRAM_ATTR handleInterrupt() {
  potholeDetected = true;
}

void setup() {
  // Start the serial monitor connection to your laptop
  Serial.begin(115200);
  // initialize builtin rgb led on the board.
pinMode(LED_RED,OUTPUT);
pinMode(LED_GREEN,OUTPUT);
pinMode(LED_BLUE,OUTPUT);

// wait for 3 seconds for serial monitor to respond before doing anything.
  delay(3000);
  
  // Set the pin as an input with an internal pull-up resistor (defaults to HIGH)
  pinMode(interruptPin, INPUT_PULLUP);

  // Turn all OFF to start (Active Low: HIGH means OFF)
  digitalWrite(LED_RED, HIGH);
  digitalWrite(LED_GREEN, HIGH);
  digitalWrite(LED_BLUE, HIGH);
  
  // Attach the interrupt to Pin 2. FALLING means it triggers when the pin goes from HIGH to LOW (when it touches Ground)
  attachInterrupt(digitalPinToInterrupt(interruptPin), handleInterrupt, FALLING);
  // start the blue light for testing.
  digitalWrite(LED_BLUE,LOW);
  delay(1000);
  digitalWrite(LED_BLUE,HIGH);
  
  Serial.println("System Ready. Waiting for pothole impact...");
}

void loop() {
  // If the interrupt was triggered, send the message to the Python script
  if (potholeDetected) {
    Serial.println("EVENT:IMU_BUMP");
    
    // Reset the flag
    potholeDetected = false;
    
    // A 1-second debounce delay so a messy wire tap doesn't trigger it 50 times in a row
    delay(3000); 
  }

  if(Serial.available()>0){
    char incomingbyte = Serial.read();

    if(incomingbyte =='H'){
      // initialize red led.
      digitalWrite(LED_RED,LOW);
      delay(3000);
      digitalWrite(LED_RED,HIGH);

    }
    else if(incomingbyte == 'M' || incomingbyte == 'L'){
      // initialize green led.
      digitalWrite(LED_GREEN,LOW);
      delay(3000);
      digitalWrite(LED_GREEN,HIGH);
    }
  }
}
