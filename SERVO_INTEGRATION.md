# Integración Servo Motor - Documentación

## Descripción

El sistema ahora incluye funcionalidad para controlar un servo motor automáticamente cuando se detecta una placa. Esto es útil para abrir barreras o puertas de estacionamiento.

## Características Principales

### 1. Detección Automática con Servo
- Cuando se detecta una placa válida, se envía automáticamente una solicitud HTTP al servo motor
- Sistema de cooldown para evitar múltiples activaciones de la misma placa (30 segundos por defecto)
- Manejo de errores y timeouts de red

### 2. Configuración Flexible
- URL del servo configurable por cámara
- URL por defecto: `http://192.168.1.100/open`
- Timeout de 5 segundos para solicitudes al servo

### 3. Historial de Placas
- Evita activaciones repetidas de la misma placa
- Auto-limpieza del historial para optimizar memoria

## Configuración del Servo Motor

### Hardware ESP32 + Servo
Tu ESP32 con servo debe exponer un endpoint HTTP que acepte solicitudes POST:

```cpp
// Ejemplo de código ESP32 con servo
#include <WiFi.h>
#include <WebServer.h>
#include <ESP32Servo.h>

Servo myServo;
WebServer server(80);

void handleOpen() {
  // Abrir servo (90 grados)
  myServo.write(90);
  delay(1000);
  
  // Cerrar servo después de 3 segundos
  delay(3000);
  myServo.write(0);
  
  server.send(200, "application/json", "{\"status\":\"success\",\"action\":\"door_opened\"}");
}

void setup() {
  myServo.attach(9); // Pin del servo
  server.on("/open", HTTP_POST, handleOpen);
  server.begin();
}
```

## Uso de la API

### Iniciar Stream con Servo

```bash
curl -X POST "http://localhost:8000/edge/camera/stream/start-processing" \
  -H "Content-Type: application/json" \
  -d '{
    "cameraId": "parking-gate-1",
    "streamUrl": "http://192.168.1.50/capture",
    "servoUrl": "http://192.168.1.100/open",
    "processInterval": 2
  }'
```

### Respuesta del Sistema

Cuando se detecta una placa, el callback incluirá información del servo:

```json
{
  "cameraId": "parking-gate-1",
  "plate": "ABC123",
  "timestamp": 1704567890.123,
  "servo_response": {
    "status": "success",
    "message": "Door opened",
    "plate": "ABC123"
  }
}
```

## Protocolo de Comunicación con Servo

### Solicitud al Servo
```json
POST /open
Content-Type: application/json

{
  "action": "open",
  "plate": "ABC123",
  "timestamp": 1704567890.123
}
```

### Respuesta Esperada del Servo
```json
{
  "status": "success",
  "action": "door_opened",
  "message": "Gate opened for plate ABC123"
}
```

## Configuración de Red

### IPs de Ejemplo
- **API Principal**: `http://localhost:8000`
- **ESP32 Cámara**: `http://192.168.1.50/capture`
- **ESP32 Servo**: `http://192.168.1.100/open`

Asegúrate de que:
1. Todos los dispositivos estén en la misma red
2. Los ESP32 tengan IPs estáticas o reservadas en el router
3. El firewall permita comunicación HTTP entre dispositivos

## Logs del Sistema

### Detección Exitosa
```
[INFO] Detected plate 'ABC123' from camera parking-gate-1
[SERVO] Sending open request for plate: ABC123
[SERVO] Door opened successfully for plate: ABC123
```

### Placa en Cooldown
```
[INFO] Plate 'ABC123' detected but still in cooldown (25s remaining)
```

### Error de Servo
```
[SERVO] Failed to open door. Status: 404
[SERVO] Error opening door for plate ABC123: Connection timeout
```

## Troubleshooting

### Problemas Comunes

1. **Servo no responde**
   - Verificar IP del servo
   - Comprobar conectividad de red
   - Revisar logs del ESP32 servo

2. **Múltiples activaciones**
   - El sistema tiene cooldown de 30 segundos
   - Verificar que el reconocimiento de placas no tenga falsos positivos

3. **Timeout de red**
   - Aumentar timeout en el código si la red es lenta
   - Verificar estabilidad de la conexión WiFi

### Debugging

Para probar manualmente el servo:

```python
from adapters.stream.stream_camera import send_servo_open_request

result = send_servo_open_request("TEST123", "http://192.168.1.100/open")
print(result)
```

## Personalización

### Cambiar Cooldown de Placas
```python
# En StreamProcessor.__init__()
self.plate_cooldown = 60  # 60 segundos en lugar de 30
```

### URL de Servo por Defecto
```python
# En send_servo_open_request()
servo_url = "http://tu-ip-servo/open"
```

### Timeout de Red
```python
# En send_servo_open_request()
response = requests.post(servo_url, json=payload, timeout=10)  # 10 segundos
```
