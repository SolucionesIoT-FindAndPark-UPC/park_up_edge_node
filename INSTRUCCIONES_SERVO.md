# 🔧 INSTRUCCIONES PARA SOLUCIONAR EL SERVO

## ❌ **PROBLEMA ACTUAL:**
```
⚠️ Servo responde con código: 404
⚠️ Continuando sin servo...
```

**CAUSA:** El ESP32 no tiene el código del servo. Solo tiene el código de cámara original.

---

## ✅ **SOLUCIÓN PASO A PASO:**

### **PASO 1: Preparar Arduino IDE**

1. **Abre Arduino IDE**
2. **Instala la librería ESP32Servo:**
   - Ve a: Herramientas → Administrar Bibliotecas
   - Busca: "ESP32Servo"
   - Instala la librería de Kevin Harrington

### **PASO 2: Configurar el ESP32**

1. **Conecta el ESP32 a la PC** (cable USB)
2. **Configura Arduino IDE:**
   - Herramientas → Placa → ESP32 Arduino → AI Thinker ESP32-CAM
   - Herramientas → Puerto → (selecciona tu puerto COM)
   - Herramientas → Upload Speed → 115200

### **PASO 3: Subir el Código**

1. **Abre el archivo:** `ESP32_SERVO_CODE.ino` (que está en tu carpeta del proyecto)
2. **Copia todo el código** y pégalo en Arduino IDE
3. **Modifica si es necesario:**
   - WiFi SSID: `"ARIANAVR"` ✅ (correcto)
   - WiFi Password: `"ev@rt2801"` ✅ (correcto)
   - Servo Pin: `14` (puedes cambiarlo si usas otro pin)

4. **Sube el código:**
   - Presiona el botón **RESET** en el ESP32
   - Haz clic en **Subir** en Arduino IDE
   - Si hay error, presiona **BOOT** mientras subes

### **PASO 4: Conectar el Servo**

**Conexiones físicas:**
```
ESP32-CAM    →    Servo
GPIO 14      →    Señal (naranja/amarillo)
5V           →    VCC (rojo)
GND          →    GND (negro/marrón)
```

### **PASO 5: Verificar**

1. **Abre el Monitor Serie** (115200 baudios)
2. **Busca estos mensajes:**
   ```
   WiFi connected
   Camera Ready! Use 'http://192.168.18.85' to connect
   Servo initialized at position 0°
   ```

3. **Ejecuta el test:**
   ```bash
   python test_servo_post_upload.py
   ```

---

## 🎯 **RESULTADO ESPERADO:**

**ANTES (actual):**
```
❌ Error 404 - Nothing matches the given URI
```

**DESPUÉS (cuando funcione):**
```
✅ Servo responde correctamente
📋 Respuesta: {"status":"success","action":"opened","message":"Gate opened","position":90}
```

---

## 🚨 **TROUBLESHOOTING:**

### **Si no puedes subir el código:**
- Mantén presionado **BOOT** mientras haces clic en **Subir**
- Verifica que el cable USB esté bien conectado
- Prueba con otro cable USB

### **Si el servo no se mueve:**
- Verifica las conexiones físicas
- Asegúrate de que el servo esté alimentado (5V)
- Prueba con otro pin GPIO (cambiar `servoPin = 14`)

### **Si hay error de WiFi:**
- Verifica que SSID y password sean correctos
- Asegúrate de que el ESP32 esté cerca del router

---

## 📝 **CÓDIGO CLAVE AGREGADO:**

El código nuevo incluye estos endpoints:

- **POST /open** → Abre el servo a 90°
- **POST /close** → Cierra el servo a 0°  
- **GET /servo-status** → Estado del servo

---

## ✅ **CONFIRMACIÓN:**

Una vez subido el código, cuando detectes una placa verás:

```
[INFO] Detected plate 'ABC123' from camera esp32_192_168_18_85
[SERVO] Sending open request for plate: ABC123
[SERVO] Door opened successfully for plate: ABC123
```

En lugar de:
```
[SERVO] Timeout opening door for plate: ABC123
```
