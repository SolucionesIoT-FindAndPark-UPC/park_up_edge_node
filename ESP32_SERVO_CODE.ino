#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <ESP32Servo.h>  
#include <WebServer.h>  // AGREGADO: Para los endpoints del servo

// 1. Module of this version of ESP32-CAM
#include "board_config.h"

// 2. WiFi Credentials
const char* ssid = "ARIANAVR";
const char* password = "ev@rt2801";

// 3. Edge Node URL
const char*  edgeNodeUrl = "http://your-server.com/upload";

// 4. Time intervals for loop
unsigned long lastSend = 0;
const unsigned long interval = 2000;

// Servo setup
Servo myservo;
const int servoPin = 14;  // CAMBIADO: GPIO 12 es más seguro que GPIO 14

// AGREGADO: Control automático del servo basado en detección
bool plateDetected = false;  // Estado de detección de placa
unsigned long lastPlateTime = 0;  // Última vez que se detectó una placa
const unsigned long plateTimeout = 5000;  // 5 segundos sin detección = cerrar servo
bool servoOpen = false;  // Estado actual del servo

// AGREGADO: WebServer para endpoints
WebServer server(80);

// Prototypes
void startCameraServer();
void setupLedFlash();
void captureAndSend();

// AGREGADO: Servo control functions
void handleServoOpen();
void handleServoClose();
void handleServoStatus();

// AGREGADO: Control automático del servo
void setPlateDetected(bool detected);
void updateServoBasedOnPlate();
void openServoAuto();
void closeServoAuto();

// AGREGADO: Endpoints para detección automática
void handlePlateDetected();
void handlePlateLost();

void setup() {
  // 1. Serial Setup
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  // 2. ESP32-CAM Setup
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.frame_size = FRAMESIZE_QVGA;
  config.pixel_format = PIXFORMAT_RGB565; // for face detection/recognition
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 12;
  config.fb_count = 1;

  if (config.pixel_format == PIXFORMAT_JPEG) {
    if (psramFound()) {
      config.jpeg_quality = 10;
      config.fb_count = 2;
      config.grab_mode = CAMERA_GRAB_LATEST;
    } else {
      config.frame_size = FRAMESIZE_SVGA;
      config.fb_location = CAMERA_FB_IN_DRAM;
    }
  } else {
    config.frame_size = FRAMESIZE_240X240;
#if CONFIG_IDF_TARGET_ESP32S3
    config.fb_count = 2;
#endif
  }

#if defined(CAMERA_MODEL_ESP_EYE)
  pinMode(13, INPUT_PULLUP);
  pinMode(14, INPUT_PULLUP);
#endif

  // camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  sensor_t *s = esp_camera_sensor_get();
  if (s->id.PID == OV3660_PID) {
    s->set_vflip(s, 1);
    s->set_brightness(s, 1);
    s->set_saturation(s, -2);
  }
  if (config.pixel_format == PIXFORMAT_JPEG) {
    s->set_framesize(s, FRAMESIZE_QVGA);
  }

#if defined(CAMERA_MODEL_M5STACK_WIDE) || defined(CAMERA_MODEL_M5STACK_ESP32CAM)
  s->set_vflip(s, 1);
  s->set_hmirror(s, 1);
#endif

#if defined(CAMERA_MODEL_ESP32S3_EYE)
  s->set_vflip(s, 1);
#endif

#if defined(LED_GPIO_NUM)
  setupLedFlash();
#endif

  // 3. WiFi Setup
  WiFi.begin(ssid, password);
  WiFi.setSleep(false);
  Serial.print("WiFi connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");

  // 4. Server Setup
  startCameraServer();
  
  // AGREGADO: Configurar endpoints del servo
  server.on("/open", HTTP_POST, handleServoOpen);
  server.on("/close", HTTP_POST, handleServoClose);
  server.on("/servo-status", HTTP_GET, handleServoStatus);
  
  // AGREGADO: Endpoint para control automático de detección
  server.on("/plate-detected", HTTP_POST, handlePlateDetected);
  server.on("/plate-lost", HTTP_POST, handlePlateLost);
  
  server.begin();
  
  Serial.print("Camera Ready! Use 'http://");
  Serial.print(WiFi.localIP());
  Serial.println("' to connect");

  // 5. Servo Setup - MEJORADO
  Serial.println("Inicializando servo...");
  
  // Configurar pin como salida primero
  pinMode(servoPin, OUTPUT);
  
  // Configurar ESP32Servo con parámetros específicos
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);
  myservo.setPeriodHertz(50);    // Frecuencia estándar para servos (50 Hz)
  
  // Attach con valores de pulso específicos
  myservo.attach(servoPin, 500, 2500); // min=500us, max=2500us
  
  // Mover a posición inicial y verificar
  Serial.println("Moviendo servo a posición inicial (0°)...");
  myservo.write(0);
  delay(1000);  // Dar más tiempo
  
  Serial.println("Probando movimiento del servo...");
  myservo.write(90);  // Probar movimiento
  delay(1000);
  myservo.write(0);   // Volver a inicial
  delay(1000);
  
  Serial.printf("Servo inicializado en pin %d - Posición: 0°\n", servoPin);
}

// AGREGADO: Variables para test del servo
unsigned long lastServoTest = 0;
const unsigned long servoTestInterval = 10000; // Test cada 10 segundos
bool servoTestEnabled = true; // Cambiar a false para desactivar test automático

void loop() {
  // AGREGADO: Manejar requests del servidor
  server.handleClient();
  
  // AGREGADO: Control automático del servo basado en detección de placas
  updateServoBasedOnPlate();
  
  // AGREGADO: Test automático del servo (solo para debugging)
  if (servoTestEnabled && millis() - lastServoTest > servoTestInterval) {
    Serial.println("=== TEST AUTOMÁTICO DEL SERVO ===");
    Serial.println("Moviendo a 45°...");
    myservo.write(45);
    delay(1000);
    Serial.println("Moviendo a 0°...");
    myservo.write(0);
    delay(1000);
    lastServoTest = millis();
    Serial.println("=== FIN TEST AUTOMÁTICO ===");
  }
  
  // Código original del loop
  if (millis() - lastSend > interval) {
    captureAndSend();         // Captura y envía la foto
    lastSend = millis();
  }
}

void captureAndSend() {
  camera_fb_t * fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    return;
  }
  // Start HTTP POST
  HTTPClient http;
  http.begin(edgeNodeUrl);
  http.addHeader("Content-Type", "image/jpeg");

  int httpResponseCode = http.POST(fb->buf, fb->len);

  if (httpResponseCode > 0) {
    Serial.printf("Image sent, response: %d\n", httpResponseCode);
  } else {
    Serial.printf("Error sending image: %s\n", http.errorToString(httpResponseCode).c_str());
  }

  http.end();
  esp_camera_fb_return(fb);
}

// AGREGADO: Funciones del servo para el control remoto
void handleServoOpen() {
  Serial.println("🚪 === INICIANDO APERTURA DE PUERTA ===");
  Serial.printf("Pin del servo: %d\n", servoPin);
  Serial.println("Estado antes: Verificando...");
  
  // Verificar que el servo esté conectado
  if (!myservo.attached()) {
    Serial.println("❌ ERROR: Servo no está conectado");
    server.send(500, "application/json", 
                "{\"status\":\"error\",\"message\":\"Servo not attached\"}");
    return;
  }
  
  Serial.println("✅ Servo conectado correctamente");
  Serial.println("Enviando señal PWM para abrir (90°)...");
  
  // Mover servo a posición abierta con debugging
  myservo.write(90);
  Serial.println("Señal PWM enviada: 90°");
  delay(1000);  // Dar más tiempo al servo
  
  Serial.println("Verificando posición...");
  
  // Respuesta JSON
  server.send(200, "application/json", 
              "{\"status\":\"success\",\"action\":\"opened\",\"message\":\"Gate opened\",\"position\":90,\"pin\":" + String(servoPin) + "}");
  
  Serial.println("🚪 === APERTURA COMPLETADA ===");
}

void handleServoClose() {
  Serial.println("🚪 === INICIANDO CIERRE DE PUERTA ===");
  Serial.printf("Pin del servo: %d\n", servoPin);
  
  if (!myservo.attached()) {
    Serial.println("❌ ERROR: Servo no está conectado");
    server.send(500, "application/json", 
                "{\"status\":\"error\",\"message\":\"Servo not attached\"}");
    return;
  }
  
  Serial.println("Enviando señal PWM para cerrar (0°)...");
  
  // Cerrar servo (0 grados)
  myservo.write(0);
  Serial.println("Señal PWM enviada: 0°");
  delay(1000);
  
  server.send(200, "application/json", 
              "{\"status\":\"success\",\"action\":\"closed\",\"message\":\"Gate closed\",\"position\":0,\"pin\":" + String(servoPin) + "}");
              
  Serial.println("🚪 === CIERRE COMPLETADO ===");
}

void handleServoStatus() {
  // Estado actual del servo con más información
  bool attached = myservo.attached();
  
  String response = "{";
  response += "\"servo_connected\":" + String(attached ? "true" : "false") + ",";
  response += "\"servo_pin\":" + String(servoPin) + ",";
  response += "\"status\":\"" + String(attached ? "ready" : "disconnected") + "\",";
  response += "\"pwm_frequency\":50,";
  response += "\"pulse_range\":\"500-2500us\",";
  response += "\"plate_detected\":" + String(plateDetected ? "true" : "false") + ",";
  response += "\"servo_open\":" + String(servoOpen ? "true" : "false");
  response += "}";
  
  server.send(200, "application/json", response);
  
  Serial.println("Status solicitado:");
  Serial.printf("- Pin: %d\n", servoPin);
  Serial.printf("- Conectado: %s\n", attached ? "Sí" : "No");
  Serial.printf("- Placa detectada: %s\n", plateDetected ? "Sí" : "No");
  Serial.printf("- Servo abierto: %s\n", servoOpen ? "Sí" : "No");
}

// ========================================
// FUNCIONES DE CONTROL AUTOMÁTICO DEL SERVO
// ========================================

void setPlateDetected(bool detected) {
  /**
   * Función para establecer el estado de detección de placa
   * Llamar esta función desde el sistema de detección de placas
   */
  if (detected && !plateDetected) {
    Serial.println("🚗 PLACA DETECTADA - Activando servo");
    plateDetected = true;
    lastPlateTime = millis();
  } else if (detected && plateDetected) {
    // Actualizar tiempo si sigue detectando
    lastPlateTime = millis();
  }
  
  plateDetected = detected;
}

void updateServoBasedOnPlate() {
  /**
   * Función principal que controla el servo automáticamente
   * Se ejecuta en cada loop()
   */
  
  // Verificar timeout de detección
  if (plateDetected && (millis() - lastPlateTime > plateTimeout)) {
    Serial.println("⏰ TIMEOUT - No se detecta placa, cerrando servo");
    plateDetected = false;
  }
  
  // Controlar servo basado en estado de detección
  if (plateDetected && !servoOpen) {
    // Placa detectada y servo cerrado → ABRIR
    openServoAuto();
  } else if (!plateDetected && servoOpen) {
    // Sin placa y servo abierto → CERRAR
    closeServoAuto();
  }
}

void openServoAuto() {
  /**
   * Abrir servo automáticamente cuando se detecta placa
   */
  Serial.println("🚪 ABRIENDO SERVO AUTOMÁTICAMENTE");
  Serial.println("Motivo: Placa detectada = TRUE");
  
  if (!myservo.attached()) {
    Serial.println("❌ ERROR: Servo no conectado");
    return;
  }
  
  myservo.write(90);  // Abrir a 90°
  servoOpen = true;
  
  Serial.println("✅ Servo abierto automáticamente (90°)");
}

void closeServoAuto() {
  /**
   * Cerrar servo automáticamente cuando no hay placa
   */
  Serial.println("🚪 CERRANDO SERVO AUTOMÁTICAMENTE");
  Serial.println("Motivo: Placa detectada = FALSE");
  
  if (!myservo.attached()) {
    Serial.println("❌ ERROR: Servo no conectado");
    return;
  }
  
  myservo.write(0);   // Cerrar a 0°
  servoOpen = false;
  
  Serial.println("✅ Servo cerrado automáticamente (0°)");
}

// ========================================
// ENDPOINTS PARA DETECCIÓN AUTOMÁTICA
// ========================================

void handlePlateDetected() {
  /**
   * Endpoint: POST /plate-detected
   * Llamado cuando el sistema de Python detecta una placa
   */
  Serial.println("📡 API: Placa detectada recibida");
  setPlateDetected(true);
  
  server.send(200, "application/json", 
              "{\"status\":\"success\",\"message\":\"Plate detection activated\",\"servo_will_open\":true}");
}

void handlePlateLost() {
  /**
   * Endpoint: POST /plate-lost  
   * Llamado cuando el sistema de Python pierde la detección
   */
  Serial.println("📡 API: Pérdida de placa recibida");
  setPlateDetected(false);
  
  server.send(200, "application/json", 
              "{\"status\":\"success\",\"message\":\"Plate detection deactivated\",\"servo_will_close\":true}");
}
