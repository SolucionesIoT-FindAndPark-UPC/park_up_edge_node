#!/usr/bin/env python3
"""
Diagnóstico específico del servo - Debug profundo
"""
import requests
import time
import json

SERVO_IP = "192.168.18.85"
SERVO_URL = f"http://{SERVO_IP}/open"

def test_servo_detailed():
    """Test detallado del servo con múltiples métodos"""
    print("🔍 DIAGNÓSTICO DETALLADO DEL SERVO")
    print("=" * 50)
    
    # 1. Test de ping básico
    print(f"1️⃣ Probando conectividad básica a {SERVO_IP}...")
    import subprocess
    try:
        result = subprocess.run(['ping', '-n', '1', SERVO_IP], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Ping exitoso - El ESP32 está en la red")
        else:
            print("❌ Ping falló - ESP32 no responde en la red")
            return False
    except Exception as e:
        print(f"❌ Error en ping: {e}")
        return False
    
    # 2. Test HTTP básico (GET al root)
    print(f"\n2️⃣ Probando servidor web en {SERVO_IP}...")
    try:
        response = requests.get(f"http://{SERVO_IP}/", timeout=5)
        print(f"✅ Servidor web responde - Código: {response.status_code}")
        print(f"📋 Contenido: {response.text[:100]}...")
    except requests.exceptions.Timeout:
        print("❌ Timeout - El servidor web no responde")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ No hay servidor web corriendo en puerto 80")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # 3. Test del endpoint /open con GET
    print(f"\n3️⃣ Probando endpoint /open con GET...")
    try:
        response = requests.get(f"{SERVO_URL}", timeout=5)
        print(f"📊 GET /open - Código: {response.status_code}")
        print(f"📋 Respuesta: {response.text}")
        
        if response.status_code == 405:
            print("ℹ️ Método GET no permitido - Probablemente solo acepta POST")
        elif response.status_code == 200:
            print("✅ GET funciona - El endpoint existe")
            
    except Exception as e:
        print(f"❌ Error en GET: {e}")
    
    # 4. Test del endpoint /open con POST (sin datos)
    print(f"\n4️⃣ Probando POST sin datos...")
    try:
        response = requests.post(f"{SERVO_URL}", timeout=5)
        print(f"📊 POST vacío - Código: {response.status_code}")
        print(f"📋 Respuesta: {response.text}")
        
        if response.status_code == 200:
            print("🎉 ¡POST vacío funciona! El servo debería haberse movido")
            
    except Exception as e:
        print(f"❌ Error en POST vacío: {e}")
    
    # 5. Test del endpoint /open con JSON
    print(f"\n5️⃣ Probando POST con JSON...")
    try:
        payload = {
            "action": "open",
            "plate": "DEBUG123",
            "timestamp": time.time()
        }
        
        response = requests.post(f"{SERVO_URL}", 
                               json=payload, 
                               headers={'Content-Type': 'application/json'},
                               timeout=5)
        
        print(f"📊 POST con JSON - Código: {response.status_code}")
        print(f"📋 Respuesta: {response.text}")
        print(f"📋 Headers respuesta: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("🎉 ¡POST con JSON funciona! El servo debería haberse movido")
            return True
            
    except Exception as e:
        print(f"❌ Error en POST con JSON: {e}")
    
    # 6. Test con diferentes formatos
    print(f"\n6️⃣ Probando otros formatos...")
    
    # Formato form-data
    try:
        response = requests.post(f"{SERVO_URL}", 
                               data={'action': 'open', 'plate': 'FORM123'},
                               timeout=5)
        print(f"📊 POST form-data - Código: {response.status_code}")
        if response.status_code == 200:
            print("✅ Form-data funciona")
    except Exception as e:
        print(f"❌ Error form-data: {e}")
    
    # Formato texto plano
    try:
        response = requests.post(f"{SERVO_URL}", 
                               data="open",
                               headers={'Content-Type': 'text/plain'},
                               timeout=5)
        print(f"📊 POST texto - Código: {response.status_code}")
        if response.status_code == 200:
            print("✅ Texto plano funciona")
    except Exception as e:
        print(f"❌ Error texto: {e}")
    
    return False

def test_other_endpoints():
    """Probar otros endpoints comunes del ESP32"""
    print(f"\n🔍 EXPLORANDO OTROS ENDPOINTS")
    print("=" * 30)
    
    common_endpoints = [
        "/",
        "/status", 
        "/servo",
        "/move",
        "/control",
        "/open",
        "/close",
        "/test"
    ]
    
    for endpoint in common_endpoints:
        url = f"http://{SERVO_IP}{endpoint}"
        try:
            response = requests.get(url, timeout=3)
            print(f"✅ {endpoint:10} - {response.status_code} - {response.text[:50]}...")
        except:
            print(f"❌ {endpoint:10} - No responde")

if __name__ == "__main__":
    print("🚗 DIAGNÓSTICO SERVO ESP32")
    print(f"🎯 Target: {SERVO_IP}")
    print(f"🔗 URL completa: {SERVO_URL}")
    print()
    
    # Test principal
    success = test_servo_detailed()
    
    # Explorar endpoints
    test_other_endpoints()
    
    print(f"\n{'='*50}")
    if success:
        print("🎉 SERVO FUNCIONANDO CORRECTAMENTE")
    else:
        print("❌ SERVO TIENE PROBLEMAS")
        print("\n💡 POSIBLES SOLUCIONES:")
        print("1. Verifica el código del ESP32 (debe tener servidor web)")
        print("2. Verifica que el endpoint sea exactamente '/open'")
        print("3. Verifica que acepte métodos POST")
        print("4. Revisa los logs del monitor serie del ESP32")
        print("5. Prueba con un browser: http://192.168.18.85/")
