# 🤖 CONTROL AUTOMÁTICO DEL SERVO - DOCUMENTACIÓN

## 🎯 **NUEVO SISTEMA IMPLEMENTADO:**

El servo ahora se controla **automáticamente** basado en la detección de placas:

- **✅ Placa detectada = `true`** → Servo se abre a **90°**
- **❌ Sin placa = `false`** → Servo se cierra a **0°**

---

## 🔄 **FLUJO DE FUNCIONAMIENTO:**

```
1. Sistema detecta placa → 
2. Envía POST /plate-detected → 
3. ESP32 recibe señal → 
4. Servo se abre automáticamente (90°) →
5. Sistema pierde placa → 
6. Envía POST /plate-lost → 
7. ESP32 recibe señal → 
8. Servo se cierra automáticamente (0°)
```

---

## 📡 **NUEVOS ENDPOINTS DEL ESP32:**

### **POST /plate-detected**
```json
{
  "plate": "ABC123",
  "timestamp": 1704567890.123,
  "detected": true
}
```
**Resultado:** Servo se abre a 90°

### **POST /plate-lost**
```json
{
  "timestamp": 1704567890.123,
  "detected": false
}
```
**Resultado:** Servo se cierra a 0°

### **GET /servo-status**
```json
{
  "servo_connected": true,
  "servo_pin": 14,
  "status": "ready",
  "plate_detected": false,
  "servo_open": false,
  "pwm_frequency": 50,
  "pulse_range": "500-2500us"
}
```

---

## 🔧 **MODIFICACIONES REALIZADAS:**

### **1. ESP32 Code (`ESP32_SERVO_CODE.ino`):**
- ✅ Variables de estado: `plateDetected`, `servoOpen`
- ✅ Funciones automáticas: `updateServoBasedOnPlate()`
- ✅ Timeout de 5 segundos sin detección
- ✅ Nuevos endpoints: `/plate-detected`, `/plate-lost`
- ✅ Logs detallados para debugging

### **2. Python Code (`simple_esp32_detector.py`):**
- ✅ Función: `send_plate_detected(plate)`
- ✅ Función: `send_plate_lost()`
- ✅ Monitor mejorado con control automático
- ✅ Estado de detección: `current_plate_detected`

---

## 🚀 **CÓMO USAR:**

### **Paso 1: Subir código al ESP32**
1. Abre Arduino IDE
2. Copia el código de `ESP32_SERVO_CODE.ino`
3. Sube al ESP32

### **Paso 2: Conectar servo**
```
ESP32 Pin    →    Servo
GPIO 14      →    Señal (naranja)
5V           →    VCC (rojo)
GND          →    GND (negro)
```

### **Paso 3: Probar sistema automático**
```bash
python test_automatic_servo.py
```

### **Paso 4: Ejecutar detección real**
```bash
python simple_esp32_detector.py
```

---

## 📊 **LOGS ESPERADOS:**

### **En el ESP32 (Monitor Serie):**
```
📡 API: Placa detectada recibida
🚗 PLACA DETECTADA - Activando servo
🚪 ABRIENDO SERVO AUTOMÁTICAMENTE
✅ Servo abierto automáticamente (90°)

📡 API: Pérdida de placa recibida
🚪 CERRANDO SERVO AUTOMÁTICAMENTE
✅ Servo cerrado automáticamente (0°)
```

### **En el Python:**
```
🚗 [14:30:15] PLACA #1: "ABC123"
[SERVO] 🚗 Enviando detección de placa: ABC123
[SERVO] ✅ Detección enviada - Servo se abrirá automáticamente
    ✅ Señal enviada: SERVO ABRIENDO...

🚫 Placa perdida - Enviando señal de cierre...
[SERVO] 🚫 Enviando pérdida de detección
[SERVO] ✅ Pérdida enviada - Servo se cerrará automáticamente
    ✅ Señal enviada: SERVO CERRANDO...
```

---

## ⚙️ **CONFIGURACIÓN AVANZADA:**

### **Cambiar timeout de detección:**
```cpp
// En ESP32_SERVO_CODE.ino
const unsigned long plateTimeout = 3000;  // 3 segundos en lugar de 5
```

### **Cambiar ángulos del servo:**
```cpp
// Abrir
myservo.write(120);  // 120° en lugar de 90°

// Cerrar
myservo.write(10);   // 10° en lugar de 0°
```

### **Desactivar test automático:**
```cpp
bool servoTestEnabled = false;  // Desactivar test cada 10 segundos
```

---

## 🔍 **TROUBLESHOOTING:**

### **❌ Servo no se mueve:**
1. Verificar conexiones físicas
2. Revisar logs del Monitor Serie
3. Probar con `test_automatic_servo.py`
4. Verificar alimentación del servo (5V)

### **❌ Error "Servo not attached":**
1. Verificar librería ESP32Servo instalada
2. Probar con otro pin GPIO
3. Reiniciar ESP32

### **❌ Sistema no detecta placas:**
1. Verificar servidor FastAPI funcionando
2. Revisar URL del servidor en `simple_esp32_detector.py`
3. Verificar cámara ESP32 funcionando

---

## ✅ **VENTAJAS DEL NUEVO SISTEMA:**

1. **🤖 Totalmente automático** - No necesita intervención manual
2. **⚡ Respuesta rápida** - Control directo ESP32 ↔ Servo
3. **🔄 Estado persistente** - Recuerda si hay placa detectada
4. **⏰ Timeout inteligente** - Auto-cierre si no hay detección
5. **🔍 Debugging completo** - Logs detallados en ambos sistemas
6. **🛡️ Robusto** - Manejo de errores y reconexión

---

## 🎯 **RESULTADO FINAL:**

**Ahora cuando detectes una placa:**
1. ✅ Sistema Python detecta placa
2. ✅ Envía señal automática al ESP32
3. ✅ ESP32 abre servo a 90°
4. ✅ Cuando pierde la placa, cierra a 0°
5. ✅ Todo automático, sin intervención manual

¡**El sistema está listo para funcionar completamente automático!** 🚗✨
