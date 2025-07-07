# 🔧 DIAGNÓSTICO DEL SERVO - SOLUCIÓN PASO A PASO

## ❌ **PROBLEMA ACTUAL:**
- El sistema responde "abriendo puerta" 
- Pero el servo no se mueve físicamente
- El código se ejecuta pero no hay movimiento

---

## 🔍 **CAMBIOS REALIZADOS EN EL CÓDIGO:**

### **1. Pin cambiado de GPIO 14 → GPIO 12**
```cpp
const int servoPin = 12;  // Más seguro que GPIO 14
```

### **2. Inicialización mejorada del servo:**
```cpp
ESP32PWM::allocateTimer(0);
myservo.setPeriodHertz(50);
myservo.attach(servoPin, 500, 2500);
```

### **3. Debugging extensivo agregado**
- Logs detallados en cada función
- Test automático cada 10 segundos
- Verificación de conexión del servo

---

## 🔌 **CONEXIONES FÍSICAS CORRECTAS:**

```
ESP32-CAM Pin    →    Servo Motor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GPIO 12 (NEW!)   →    Señal (Naranja/Amarillo)
5V               →    VCC (Rojo)  
GND              →    GND (Negro/Marrón)
```

### **⚠️ IMPORTANTE:**
- **NO usar GPIO 14** (conflicto con cámara)
- **Usar GPIO 12** (pin seguro)
- **Verificar alimentación**: El servo necesita 5V estables

---

## 🚨 **PASOS DE DIAGNÓSTICO:**

### **PASO 1: Subir el código corregido**
1. Copia el código actualizado a Arduino IDE
2. Verifica que la conexión esté en **GPIO 12**
3. Sube el código al ESP32

### **PASO 2: Verificar logs en Monitor Serie**
Busca estos mensajes:
```
✅ ESPERADO:
Servo inicializado en pin 12 - Posición: 0°
=== TEST AUTOMÁTICO DEL SERVO ===
Moviendo a 45°...
Moviendo a 0°...

❌ SI VES ESTO:
❌ ERROR: Servo no está conectado
```

### **PASO 3: Test manual**
```bash
python test_servo_post_upload.py
```

---

## 🔧 **TROUBLESHOOTING POR SÍNTOMAS:**

### **📋 Síntoma 1: "Servo no está conectado"**
**Causa:** Problema de inicialización
**Solución:**
- Verificar librería ESP32Servo instalada
- Probar con otro pin GPIO (13, 15, 2)

### **📋 Síntoma 2: Logs OK pero servo no se mueve**
**Causa:** Problema de hardware
**Solución:**
- Verificar conexiones físicas
- Probar con multímetro en pin GPIO 12
- Verificar que el servo funcione (probarlo con Arduino UNO)

### **📋 Síntoma 3: Servo se mueve erráticamente**
**Causa:** Problema de alimentación
**Solución:**
- Usar fuente externa de 5V para el servo
- Conectar solo la señal al ESP32
- Verificar que GND esté común

---

## 🧪 **TEST DE VOLTAJE:**

Con multímetro en GPIO 12:
- **En reposo:** ~0V
- **Al enviar señal:** Pulsos PWM de 3.3V
- **Frecuencia:** 50 Hz (20ms periodo)

---

## 📝 **CÓDIGO DE TEST SIMPLE:**

Si quieres probar solo el servo sin cámara:

```cpp
#include <ESP32Servo.h>

Servo testServo;
const int pin = 12;

void setup() {
  Serial.begin(115200);
  testServo.attach(pin);
  Serial.println("Test iniciado");
}

void loop() {
  Serial.println("Moviendo a 0°");
  testServo.write(0);
  delay(1000);
  
  Serial.println("Moviendo a 90°");
  testServo.write(90);
  delay(1000);
  
  Serial.println("Moviendo a 180°");
  testServo.write(180);
  delay(1000);
}
```

---

## ✅ **CONFIRMACIÓN DE ÉXITO:**

Cuando funcione, verás en los logs:
```
🚪 === INICIANDO APERTURA DE PUERTA ===
Pin del servo: 12
✅ Servo conectado correctamente
Enviando señal PWM para abrir (90°)...
Señal PWM enviada: 90°
🚪 === APERTURA COMPLETADA ===
```

**Y el servo se moverá físicamente** 🎯
