# Park Up Edge Node - Testing con Mock Database

## 🎯 Descripción

Este proyecto incluye una **base de datos simulada (mock database)** completa que permite realizar pruebas exhaustivas del sistema de estacionamiento sin necesidad de una base de datos MySQL real. Es perfecto para desarrollo, testing, demos y validación de funcionalidades.

## 🚀 Inicio Rápido

### 1. Configurar el Entorno

**Windows:**
```powershell
# Ejecutar setup automático
.\setup_windows.bat

# O manualmente:
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

**Linux/macOS:**
```bash
# Ejecutar setup automático
chmod +x setup_linux.sh
./setup_linux.sh

# O manualmente:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Iniciar el Servidor

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Ejecutar Tests Automatizados

**Opción A - Script Automatizado:**
```powershell
# Windows
.\run_tests.bat

# Linux/macOS  
chmod +x run_tests.sh
./run_tests.sh
```

**Opción B - Python Directo:**
```bash
python test_mock_database.py
```

## 📋 Tests Disponibles

### Tests Automatizados (Python)
- ✅ `test_mock_database.py` - Suite completa de tests automatizados
- ✅ Verificación de endpoints básicos
- ✅ Validación del mock database
- ✅ Tests de búsqueda de usuarios
- ✅ Simulación de detección de placas
- ✅ Estadísticas del sistema
- ✅ Flujo completo de estacionamiento

### Tests Manuales (HTTP)
- 📄 `test_mock_database.http` - Tests específicos del mock database
- 📄 `test_main.http` - Tests generales de la API
- 📄 `test_users.http` - Tests de sincronización de usuarios
- 📄 `test_esp32_stream.http` - Tests de cámara ESP32

## 👥 Usuarios de Prueba

El mock database incluye estos usuarios para testing:

| ID | Username | Email | Roles | Vehículo | Estado |
|---|---|---|---|---|---|
| 1 | admin | admin@parkup.com | ADMIN, USER | ABC123 (Toyota) | Activo |
| 2 | manager1 | manager@parkup.com | MANAGER, USER | XYZ789 (Honda) | Activo |
| 3 | operator1 | operator@parkup.com | OPERATOR | - | Activo |
| 4 | user1 | user1@example.com | USER | DEF456 (Ford) | Activo |
| 5 | user2 | user2@example.com | USER | GHI789 (Nissan) | Activo |
| 6 | supervisor | supervisor@parkup.com | SUPERVISOR, OPERATOR | - | Activo |
| 7 | guest | guest@example.com | GUEST | - | Inactivo |

## 🚗 Vehículos de Prueba

| Placa | Propietario | Modelo |
|---|---|---|
| ABC123 | admin | Toyota Camry |
| XYZ789 | manager1 | Honda Civic |
| DEF456 | user1 | Ford Focus |
| GHI789 | user2 | Nissan Altima |

## 🔗 Endpoints Principales

### Mock Database
```http
GET /edge/users/test/mock          # Test del mock database
GET /edge/users/cached             # Obtener usuarios en cache
GET /edge/users/{id}               # Buscar por ID
GET /edge/users/email/{email}      # Buscar por email
GET /edge/users/plate/{plate}      # Buscar por placa
GET /edge/mock/stats               # Estadísticas
```

### Simulación
```http
POST /edge/mock/simulate-plate-detection  # Simular detección
POST /edge/parking/circulation/with-user-lookup  # Reconocer + buscar usuario
```

### ESP32 Integration
```http
POST /edge/camera/stream/start-processing  # Iniciar stream
POST /edge/camera/stream/stop-processing   # Detener stream  
GET /edge/camera/stream/status             # Estado de streams
```

## 📊 Casos de Prueba

### Caso 1: Usuario Conocido
```http
POST /edge/mock/simulate-plate-detection
{
    "license_plate": "ABC123",
    "camera_id": "entrance"
}
```
**Resultado Esperado:** Usuario admin encontrado, acceso otorgado

### Caso 2: Vehículo Desconocido
```http
POST /edge/mock/simulate-plate-detection
{
    "license_plate": "UNKNOWN999", 
    "camera_id": "entrance"
}
```
**Resultado Esperado:** Usuario no encontrado, vehículo desconocido

### Caso 3: Flujo Completo con Imagen
```http
POST /edge/parking/circulation/with-user-lookup
# Sube imagen con placa
```
**Resultado Esperado:** Placa reconocida + usuario encontrado (si coincide)

## 🛠️ Troubleshooting

### Servidor No Responde
```bash
# Verificar que el servidor esté corriendo
curl http://localhost:8000/

# Si no responde, iniciar servidor
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Import Errors
```bash
# Verificar entorno virtual activado
# Windows: .\venv\Scripts\activate
# Linux/macOS: source venv/bin/activate

# Reinstalar dependencias
pip install -r requirements.txt
```

### Tests Fallan
```bash
# Ejecutar test individual
python -c "import requests; print(requests.get('http://localhost:8000/').json())"

# Verificar logs del servidor
# El servidor debe mostrar logs de las peticiones
```

## 📈 Interpretación de Resultados

### Test Exitoso
```
✅ Mock database connection: Mock database connection successful
✅ Cached users: 6 usuarios
✅ ID 1 (admin): admin
✅ Placa ABC123: admin
✅ Placa conocida ABC123: Usuario: Sí, Acceso: granted
```

### Estadísticas Típicas
```json
{
    "total_users": 7,
    "active_users": 6,
    "inactive_users": 1,
    "vehicles": 4,
    "roles_distribution": {
        "USER": 4,
        "ADMIN": 1,
        "MANAGER": 1,
        "OPERATOR": 2,
        "SUPERVISOR": 1,
        "GUEST": 1
    }
}
```

## 🔄 Integración con ESP32

El mock database funciona perfectamente con cámaras ESP32:

1. **Stream Real + Mock Data**: Cámara ESP32 captura placas reales que se buscan en mock database
2. **Testing Sin Hardware**: Simula detecciones sin cámara real
3. **Desarrollo**: Prueba flujos completos sin dependencias externas

## 📝 Logging

El sistema incluye logging detallado:

```
🎭 Mock database initialized with 6 users
👤 Found user by ID 1: admin
🚗 Found user by license plate ABC123: admin
📊 Retrieved 6 active users from mock database
```

## 🎉 Beneficios del Mock Database

- ✅ **Sin Dependencias**: No requiere MySQL ni configuración externa
- ✅ **Datos Consistentes**: Mismos usuarios para todas las pruebas
- ✅ **Desarrollo Rápido**: Testing inmediato sin setup complejo
- ✅ **Demos**: Perfecto para mostrar funcionalidades
- ✅ **CI/CD**: Ideal para pipelines de integración continua
- ✅ **Educación**: Excelente para aprender el sistema

## 🔜 Próximos Pasos

1. **Conectar MySQL Real**: Configurar `.env` con credenciales MySQL
2. **Poblar Datos Reales**: Usar `database_schema.sql` para estructura
3. **Modo Híbrido**: Combinar mock para testing y MySQL para producción
4. **Automatización**: Integrar tests en CI/CD pipeline
