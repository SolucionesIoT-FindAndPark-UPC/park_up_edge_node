#!/usr/bin/env python3
"""
Script para configurar ESP32 CAM y detectar placas automáticamente
"""
import requests
import time
import json

SERVER_URL = "http://localhost:8000"

def setup_esp32_cam():
    """Configurar y conectar ESP32 CAM"""
    print("🔧 Configurando ESP32 CAM para detección de placas")
    print("=" * 50)
    
    # Solicitar IP de la ESP32
    while True:
        esp32_ip = input("📡 Ingresa la IP de tu ESP32 CAM (ej: 192.168.1.100): ").strip()
        if esp32_ip:
            break
        print("❌ Debes ingresar una IP válida")
    
    # Construir URL del stream
    stream_url = f"http://{esp32_ip}/capture"
    camera_id = f"esp32_{esp32_ip.replace('.', '_')}"
    
    print(f"\n📷 Configurando cámara:")
    print(f"   • ID: {camera_id}")
    print(f"   • Stream URL: {stream_url}")
    
    return camera_id, stream_url

def test_esp32_connection(stream_url):
    """Probar conexión con ESP32"""
    print(f"\n🔍 Probando conexión con ESP32...")
    
    try:
        response = requests.get(stream_url, timeout=10)
        if response.status_code == 200:
            print("✅ Conexión exitosa con ESP32 CAM")
            return True
        else:
            print(f"❌ ESP32 respondió con código: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("❌ Timeout - ESP32 no responde (revisa la IP)")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar con ESP32 (revisa la IP y que esté encendida)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def start_plate_detection(camera_id, stream_url):
    """Iniciar detección de placas en tiempo real"""
    print(f"\n🚀 Iniciando detección automática de placas...")
    
    try:
        # Crear payload para el endpoint
        payload = {
            "cameraId": camera_id,
            "streamUrl": stream_url
        }
        
        # Iniciar procesamiento
        response = requests.post(
            f"{SERVER_URL}/edge/camera/stream/start-processing", 
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Detección iniciada exitosamente!")
            print(f"   • Estado: {result.get('status', 'unknown')}")
            print(f"   • Cámara ID: {result.get('cameraId', 'unknown')}")
            return True
        else:
            print(f"❌ Error al iniciar: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def monitor_plate_detection():
    """Monitorear placas detectadas en tiempo real"""
    print("\n🔄 MONITOREANDO PLACAS EN TIEMPO REAL")
    print("=" * 50)
    print("Enfoca tu ESP32 CAM hacia una placa...")
    print("Presiona Ctrl+C para detener\n")
    
    last_plate = ""
    last_timestamp = 0
    
    try:
        while True:
            try:
                # Obtener último resultado
                response = requests.get(f"{SERVER_URL}/edge/plate-recognition/last-result")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verificar si hay una nueva placa detectada
                    if (data['plate'] and 
                        data['plate'] != "No plate detected" and 
                        data['plate'] != last_plate and 
                        data['timestamp'] > last_timestamp):
                        
                        # Formatear timestamp
                        detection_time = time.strftime('%H:%M:%S', time.localtime(data['timestamp']))
                        
                        # Mostrar placa detectada
                        print(f"🚗 [{detection_time}] PLACA DETECTADA: {data['plate']}")
                        print(f"   └─ String: '{data['plate']}'")
                        
                        # Actualizar valores
                        last_plate = data['plate']
                        last_timestamp = data['timestamp']
                
                time.sleep(0.5)  # Verificar cada 500ms para respuesta rápida
                
            except requests.exceptions.ConnectionError:
                print("❌ Perdida de conexión con el servidor")
                break
            except Exception as e:
                print(f"❌ Error durante monitoreo: {e}")
                time.sleep(1)
                
    except KeyboardInterrupt:
        print(f"\n⏹️ Monitoreo detenido")
        return True

def stop_plate_detection(camera_id):
    """Detener detección de placas"""
    print(f"\n⏹️ Deteniendo detección para cámara {camera_id}...")
    
    try:
        payload = {"cameraId": camera_id}
        response = requests.post(
            f"{SERVER_URL}/edge/camera/stream/stop-processing", 
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Detección detenida exitosamente")
            return True
        else:
            print(f"❌ Error al detener: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def get_detection_status():
    """Obtener estado de las cámaras activas"""
    try:
        response = requests.get(f"{SERVER_URL}/edge/camera/stream/status")
        if response.status_code == 200:
            status = response.json()
            print(f"\n📊 Estado del sistema:")
            print(f"   • Cámaras activas: {status['total_active']}")
            if status['active_cameras']:
                print(f"   • IDs activos: {', '.join(status['active_cameras'])}")
            return status
        else:
            print(f"❌ Error obteniendo estado: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    print("🚗 ESP32 CAM - Detector de Placas Automático")
    print("=" * 50)
    
    camera_id = None
    stream_url = None
    detection_active = False
    
    while True:
        print(f"\n{'🟢 ACTIVO' if detection_active else '🔴 INACTIVO'} | Opciones:")
        print("1. Configurar ESP32 CAM")
        print("2. Probar conexión")
        print("3. Iniciar detección automática")
        print("4. Monitorear placas detectadas")
        print("5. Detener detección")
        print("6. Ver estado del sistema")
        print("7. Salir")
        
        choice = input("\nElige una opción (1-7): ").strip()
        
        if choice == "1":
            camera_id, stream_url = setup_esp32_cam()
            
        elif choice == "2":
            if not stream_url:
                print("❌ Primero configura la ESP32 CAM (opción 1)")
            else:
                test_esp32_connection(stream_url)
                
        elif choice == "3":
            if not camera_id or not stream_url:
                print("❌ Primero configura la ESP32 CAM (opción 1)")
            else:
                if start_plate_detection(camera_id, stream_url):
                    detection_active = True
                    
        elif choice == "4":
            if not detection_active:
                print("❌ Primero inicia la detección (opción 3)")
            else:
                monitor_plate_detection()
                
        elif choice == "5":
            if detection_active and camera_id:
                if stop_plate_detection(camera_id):
                    detection_active = False
            else:
                print("❌ No hay detección activa")
                
        elif choice == "6":
            get_detection_status()
            
        elif choice == "7":
            if detection_active and camera_id:
                print("🛑 Deteniendo detección antes de salir...")
                stop_plate_detection(camera_id)
            print("👋 ¡Hasta luego!")
            break
            
        else:
            print("❌ Opción no válida")

if __name__ == "__main__":
    main()
