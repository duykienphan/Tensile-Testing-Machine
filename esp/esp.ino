#define LED_PIN 2  // Chân D2

int a=0,b=0,c=0,d=0;

void setup() {
  // Khởi tạo chân LED là OUTPUT
  pinMode(LED_PIN, OUTPUT);
  
  // Khởi tạo Serial Monitor
  Serial.begin(115200);

  Serial.println("Serial Monitor is ready.");
  digitalWrite(LED_PIN, LOW);
}

void loop() {
  // Kiểm tra xem có dữ liệu từ Serial Monitor không
  if (Serial.available() > 0) {
    char incomingByte = Serial.read();  // Đọc dữ liệu

    // Kiểm tra tín hiệu và điều khiển LED
    if (incomingByte == '1') {
      digitalWrite(LED_PIN, LOW);  // Bật LED
      Serial.println("LED ON");
    } else if (incomingByte == '0') {
      digitalWrite(LED_PIN, HIGH);  // Tắt LED
      Serial.println("LED OFF");
    }
  }
  a++;
  b = b+2;
  c = c+3;
  d = d+4;
  if (a > 300) a=0;
  if (b > 300) b=0;
  if (c > 300) c=0;
  if (d > 300) d=0;
  Serial.print(a);
  Serial.print("/");
  Serial.print(b);
  Serial.print("/");
  Serial.print(c);
  Serial.print("/");
  Serial.println(d);
  delay(50);
}
