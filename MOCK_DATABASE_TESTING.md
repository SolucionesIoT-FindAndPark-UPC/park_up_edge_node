# Mock Database Testing Guide

## Overview

El sistema Park Up Edge Node incluye una base de datos simulada (mock database) que permite realizar pruebas completas sin necesidad de una conexión MySQL real. Esto es especialmente útil para desarrollo, testing y demostraciones.

## Características del Mock Database

### Usuarios de Prueba Incluidos

1. **Admin** (ID: 1)
   - Username: `admin`
   - Email: `admin@parkup.com`
   - Roles: `["ADMIN", "USER"]`
   - Vehículo: ABC123 (Toyota Camry)

2. **Manager** (ID: 2)
   - Username: `manager1`
   - Email: `manager@parkup.com`
   - Roles: `["MANAGER", "USER"]`
   - Vehículo: XYZ789 (Honda Civic)

3. **Operator** (ID: 3)
   - Username: `operator1`
   - Email: `operator@parkup.com`
   - Roles: `["OPERATOR"]`

4. **Usuario Regular** (ID: 4)
   - Username: `user1`
   - Email: `user1@example.com`
   - Roles: `["USER"]`
   - Vehículo: DEF456 (Ford Focus)

5. **Usuario Regular 2** (ID: 5)
   - Username: `user2`
   - Email: `user2@example.com`
   - Roles: `["USER"]`
   - Vehículo: GHI789 (Nissan Altima)

6. **Supervisor** (ID: 6)
   - Username: `supervisor`
   - Email: `supervisor@parkup.com`
   - Roles: `["SUPERVISOR", "OPERATOR"]`

7. **Guest** (ID: 7)
   - Username: `guest`
   - Email: `guest@example.com`
   - Roles: `["GUEST"]`
   - Status: Inactivo (para pruebas de usuarios deshabilitados)

### Vehículos de Prueba

- **ABC123** → Usuario admin (Toyota Camry)
- **XYZ789** → Usuario manager1 (Honda Civic)
- **DEF456** → Usuario user1 (Ford Focus)
- **GHI789** → Usuario user2 (Nissan Altima)

## Endpoints Disponibles para Testing

### 1. Test del Mock Database
```http
GET /edge/users/test/mock
```
Verifica la conexión y devuelve usuarios de muestra.

### 2. Obtener Todos los Usuarios
```http
GET /edge/users/cached
```
Devuelve todos los usuarios activos en cache.

### 3. Buscar por ID
```http
GET /edge/users/{user_id}
```
Ejemplo: `GET /edge/users/1` para obtener el admin.

### 4. Buscar por Email
```http
GET /edge/users/email/{email}
```
Ejemplo: `GET /edge/users/email/admin@parkup.com`

### 5. Buscar por Placa de Vehículo
```http
GET /edge/users/plate/{license_plate}
```
Ejemplo: `GET /edge/users/plate/ABC123` para encontrar al admin.

### 6. Reconocimiento de Placa con Búsqueda de Usuario
```http
POST /edge/parking/circulation/with-user-lookup
Content-Type: multipart/form-data
```
Sube una imagen, reconoce la placa y busca al usuario asociado.

### 7. Simular Detección de Placa
```http
POST /edge/mock/simulate-plate-detection
Content-Type: application/json

{
    "license_plate": "ABC123",
    "camera_id": "cam_entrance_01"
}
```
Simula la detección de una placa sin necesidad de cámara real.

### 8. Estadísticas del Mock Database
```http
GET /edge/mock/stats
```
Devuelve estadísticas completas sobre usuarios, roles y vehículos.

## Casos de Prueba Recomendados

### Test 1: Verificación Básica
1. Ejecutar `GET /edge/users/test/mock`
2. Verificar que devuelve `success: true`
3. Confirmar que hay usuarios de muestra

### Test 2: Búsqueda de Usuarios
1. Buscar admin por ID: `GET /edge/users/1`
2. Buscar manager por email: `GET /edge/users/email/manager@parkup.com`
3. Intentar buscar usuario inexistente: `GET /edge/users/999`

### Test 3: Flujo de Estacionamiento Completo
1. Simular detección de placa conocida: `POST /edge/mock/simulate-plate-detection` con `ABC123`
2. Verificar que devuelve información del admin
3. Verificar que `access: "granted"`

### Test 4: Vehículo No Registrado
1. Simular detección de placa desconocida: `POST /edge/mock/simulate-plate-detection` con `UNKNOWN999`
2. Verificar que `user_found: false`
3. Verificar que `access: "unknown_vehicle"`

### Test 5: Usuario Inactivo
1. Buscar usuario guest (ID: 7): `GET /edge/users/7`
2. Verificar que no se encuentra (usuario inactivo)

### Test 6: Estadísticas
1. Ejecutar `GET /edge/mock/stats`
2. Verificar conteos de usuarios por rol
3. Verificar lista de placas disponibles

## Integración con Cámara ESP32

El mock database funciona perfectamente con la integración de cámara ESP32:

1. **Captura Real + Mock Users**: 
   - La cámara ESP32 captura placas reales
   - El sistema busca esos números de placa en el mock database
   - Si coincide, devuelve información del usuario simulado

2. **Testing Sin Hardware**:
   - Usa endpoints de simulación para probar sin cámara
   - Simula diferentes escenarios de acceso
   - Prueba flujos completos de entrada/salida

## Ventajas del Mock Database

✅ **No requiere MySQL**: Funciona sin base de datos externa
✅ **Datos consistentes**: Siempre los mismos usuarios para pruebas
✅ **Rápido**: Respuestas inmediatas en memoria
✅ **Completo**: Incluye roles, vehículos y casos edge
✅ **Realista**: Simula estructura real de base de datos
✅ **Testing**: Perfecto para desarrollo y demos

## Cambiar Entre Mock y MySQL

Para cambiar entre mock database y MySQL real, simplemente:

1. **Mock Mode**: No configures credenciales MySQL en `.env`
2. **MySQL Mode**: Configura credenciales MySQL en `.env` y usa endpoints `/edge/users/sync`

El sistema detecta automáticamente qué modo usar basado en la configuración disponible.

## Archivos de Test Incluidos

- `test_mock_database.http`: Tests específicos del mock database
- `test_users.http`: Tests de sincronización MySQL
- `test_esp32_stream.http`: Tests de cámara ESP32
- `test_main.http`: Tests generales de API

## Próximos Pasos

Una vez que hayas probado con el mock database, puedes:

1. Conectar una base de datos MySQL real
2. Poblar con datos reales
3. Cambiar a modo production
4. Mantener el mock para testing continuo

El mock database es perfecto para demostrar todas las capacidades del sistema sin depender de infraestructura externa.
