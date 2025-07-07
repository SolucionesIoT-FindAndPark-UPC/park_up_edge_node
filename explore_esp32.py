#!/usr/bin/env python3
"""
Explorar endpoints disponibles en el ESP32
"""
import requests

SERVO_IP = "192.168.18.85"

def explore_endpoints():
    """Explorar qué endpoints están disponibles"""
    print(f"🔍 Explorando ESP32 en {SERVO_IP}")
    
    # Endpoints comunes para ESP32
    endpoints = [
        "/",
        "/servo", 
        "/move",
        "/open",
        "/close",
        "/control",
        "/status",
        "/gpio",
        "/pwm",
        "/test"
    ]
    
    print("\n📋 Endpoints encontrados:")
    available = []
    
    for endpoint in endpoints:
        url = f"http://{SERVO_IP}{endpoint}"
        try:
            response = requests.get(url, timeout=3)
            status = "✅" if response.status_code == 200 else "⚠️"
            print(f"{status} {endpoint:10} - {response.status_code} - {response.text[:50]}...")
            if response.status_code in [200, 405]:  # 405 = Method not allowed (pero existe)
                available.append(endpoint)
        except:
            print(f"❌ {endpoint:10} - No responde")
    
    if available:
        print(f"\n🎯 Endpoints disponibles: {', '.join(available)}")
        
        # Probar el root con más detalle
        try:
            response = requests.get(f"http://{SERVO_IP}/", timeout=5)
            print(f"\n📄 Contenido del root (/):")
            print("-" * 30)
            print(response.text)
            print("-" * 30)
        except:
            pass
    else:
        print("\n❌ No se encontraron endpoints disponibles")

if __name__ == "__main__":
    explore_endpoints()
