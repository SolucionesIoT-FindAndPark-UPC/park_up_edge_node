# Sistema Automático de Control de Servo
## Detección de Placas → Control Automático del Servo

### 🎯 **FUNCIONAMIENTO**

El sistema funciona de manera **completamente automática**:

1. **Placa detectada** → `valor = true` → **Servo ABRE** (90°)
2. **Sin placa** → `valor = false` → **Servo CIERRA** (0°)
3. **Timeout automático**: Si no se detecta placa por 3 segundos, el servo se cierra automáticamente

---

## 🚀 **PASOS PARA USAR EL SISTEMA**

### **1. Verificar que todo esté funcionando**

Primero, asegúrate de que todos los componentes están activos:

```powershell
# 1. Iniciar el servidor de detección FastAPI
python main.py

# 2. En otra terminal, probar las conexiones
python test_automatic_system.py
```

### **2. Iniciar el Sistema Automático**

Una vez que todo esté probado, inicia el sistema automático:

```powershell
python automatic_plate_servo_system.py
```

**¡Eso es todo!** El sistema ahora:
- ✅ Detecta placas automáticamente cada segundo
- ✅ Envía automáticamente señales al ESP32
- ✅ Controla el servo basado en las detecciones
- ✅ Registra todo en logs para debugging

### **3. Monitorear el Sistema (Opcional)**

Para ver el estado en tiempo real, abre otra terminal:

```powershell
python monitor_system.py
```

---

## 📋 **ARCHIVOS DEL SISTEMA**

| Archivo | Descripción |
|---------|-------------|
| `automatic_plate_servo_system.py` | **🎯 SISTEMA PRINCIPAL** - Detecta y controla automáticamente |
| `test_automatic_system.py` | 🔧 Tests para verificar conexiones y funcionamiento |
| `monitor_system.py` | 📊 Monitor en tiempo real del estado del sistema |
| `ESP32_SERVO_CODE.ino` | 🔧 Código del ESP32 con endpoints de control |

---

## ⚙️ **CONFIGURACIÓN**

### **Variables importantes** (en `automatic_plate_servo_system.py`):

```python
SERVER_URL = "http://localhost:8000"    # FastAPI server
ESP32_IP = "192.168.18.93"              # IP del ESP32
DETECTION_INTERVAL = 1.0                # Detectar cada 1 segundo
AUTO_CLOSE_TIMEOUT = 3.0                # Cerrar servo tras 3s sin detección
```

### **Endpoints del ESP32**:

- `GET /servo-status` - Estado actual del servo
- `POST /open` - Abrir servo manualmente
- `POST /close` - Cerrar servo manualmente
- `POST /plate-detected` - **🎯 Automático**: Placa detectada (abre servo)
- `POST /plate-lost` - **🎯 Automático**: Placa perdida (cierra servo)

---

## 🔍 **DEBUGGING Y LOGS**

### **Logs automáticos**

El sistema crea automáticamente el archivo `automatic_servo.log` con información detallada:

```
2024-01-15 10:30:15 - INFO - 🎯 PLACA DETECTADA: ABC123 (#1)
2024-01-15 10:30:15 - INFO - ✅ Servo ABIERTO (90°)
2024-01-15 10:30:20 - INFO - ⏰ Sin detección por 3.0s, cerrando servo
2024-01-15 10:30:20 - INFO - ✅ Servo CERRADO (0°)
```

### **Verificar estado manualmente**

```powershell
# Probar conexión con ESP32
curl http://192.168.18.93/servo-status

# Probar servidor de detección
curl http://localhost:8000/health

# Ver detección en tiempo real
curl http://localhost:8000/detect-realtime
```

---

## 🛠️ **TROUBLESHOOTING**

### **Problema: No se detectan placas**

1. ✅ Verificar que FastAPI esté corriendo: `http://localhost:8000`
2. ✅ Probar detección manual: `http://localhost:8000/detect-realtime`
3. ✅ Verificar cámara conectada y funcionando

### **Problema: Servo no se mueve**

1. ✅ Verificar conexión ESP32: `http://192.168.18.85/servo-status`
2. ✅ Probar control manual: `python test_automatic_system.py`
3. ✅ Verificar conexión física del servo en GPIO 12
4. ✅ Revisar logs del ESP32 en Serial Monitor

### **Problema: Sistema no responde**

1. ✅ Verificar logs: `tail -f automatic_servo.log`
2. ✅ Usar monitor: `python monitor_system.py`
3. ✅ Reiniciar sistema: Ctrl+C y volver a ejecutar

---

## 📊 **FLUJO COMPLETO DEL SISTEMA**

```
[Cámara] → [FastAPI] → [Sistema Automático] → [ESP32] → [Servo]
    ↓           ↓              ↓                ↓         ↓
  Imagen   Detección     valor=true/false   HTTP     Abre/Cierra
                         cada 1 segundo    Request    90° / 0°
```

### **Secuencia de eventos**:

1. **Sistema inicia** → Verifica conexiones
2. **Loop detectar** → Cada 1 segundo consulta `/detect-realtime`
3. **Placa detectada** → POST `/plate-detected` → Servo abre (90°)
4. **Sin placa por 3s** → POST `/plate-lost` → Servo cierra (0°)
5. **Logs todo** → Para debugging y monitoreo

---

## 🎮 **COMANDOS RÁPIDOS**

```powershell
# Iniciar sistema completo (3 terminales)
# Terminal 1: Servidor
python main.py

# Terminal 2: Sistema automático  
python automatic_plate_servo_system.py

# Terminal 3: Monitor (opcional)
python monitor_system.py
```

---

## ✅ **CHECKLIST ANTES DE USAR**

- [ ] FastAPI server ejecutándose en puerto 8000
- [ ] ESP32 conectado y respondiendo en IP 192.168.18.93
- [ ] Servo conectado a GPIO 12 del ESP32
- [ ] Cámara funcionando y detectando placas
- [ ] WiFi estable para ESP32 y PC

Una vez que todos los ítems estén ✅, simplemente ejecuta:

```powershell
python automatic_plate_servo_system.py
```

**¡Y el sistema funcionará automáticamente!** 🚀
