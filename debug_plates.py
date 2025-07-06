#!/usr/bin/env python3
"""
Script simple para depurar detección de placas en tiempo real
"""
import requests
import time

SERVER_URL = "http://localhost:8000"

def clear_cache():
    """Limpiar cache de detecciones"""
    try:
        response = requests.post(f"{SERVER_URL}/edge/plate-recognition/clear-cache")
        if response.status_code == 200:
            print("✅ Cache limpiado")
        else:
            print("❌ Error limpiando cache")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_with_image():
    """Probar con imagen de ejemplo"""
    image_path = "assets/carplate.jpeg"
    
    print("\n🧪 Probando con imagen...")
    clear_cache()  # Limpiar cache antes
    
    try:
        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{SERVER_URL}/edge/plate-recognition", files=files)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Resultado: '{result['plate']}'")
        else:
            print(f"❌ Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def monitor_real_time():
    """Monitorear en tiempo real con debug"""
    print("\n🔄 Monitoreando detección en tiempo real")
    print("Presiona Ctrl+C para parar\n")
    
    last_timestamp = 0
    
    try:
        while True:
            try:
                # Obtener info de debug
                response = requests.get(f"{SERVER_URL}/edge/plate-recognition/debug")
                if response.status_code == 200:
                    data = response.json()
                    last_detected = data['last_detected']
                    
                    # Si hay nueva detección
                    if last_detected['timestamp'] > last_timestamp:
                        detection_time = time.strftime('%H:%M:%S', time.localtime(last_detected['timestamp']))
                        
                        print(f"🚗 [{detection_time}] Nueva detección:")
                        print(f"   └─ Placa: '{last_detected['plate']}'")
                        
                        if data['recent_history']:
                            print(f"   └─ Historial reciente: {len(data['recent_history'])} detecciones")
                        
                        last_timestamp = last_detected['timestamp']
                    
                    # Mostrar punto para indicar que está activo
                    else:
                        print(".", end="", flush=True)
                
                time.sleep(1)
                
            except requests.exceptions.ConnectionError:
                print("\n❌ Conexión perdida")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                break
                
    except KeyboardInterrupt:
        print("\n⏹️ Monitoreo detenido")

def show_status():
    """Mostrar estado actual"""
    try:
        debug_response = requests.get(f"{SERVER_URL}/edge/plate-recognition/debug")
        stream_response = requests.get(f"{SERVER_URL}/edge/camera/stream/status")
        
        if debug_response.status_code == 200:
            debug_data = debug_response.json()
            print(f"\n📊 Estado de detección:")
            print(f"   • Última placa: '{debug_data['last_detected']['plate']}'")
            print(f"   • Timestamp: {debug_data['last_detected']['timestamp']}")
            print(f"   • Detecciones en historial: {debug_data['history_count']}")
        
        if stream_response.status_code == 200:
            stream_data = stream_response.json()
            print(f"\n📹 Estado de cámaras:")
            print(f"   • Cámaras activas: {stream_data['total_active']}")
            if stream_data['active_cameras']:
                print(f"   • IDs: {', '.join(stream_data['active_cameras'])}")
        
    except Exception as e:
        print(f"❌ Error obteniendo estado: {e}")

def main():
    print("🔍 Debug de Detección de Placas")
    print("=" * 40)
    
    while True:
        print("\nOpciones:")
        print("1. Limpiar cache")
        print("2. Probar con imagen")
        print("3. Monitorear tiempo real")
        print("4. Ver estado actual")
        print("5. Salir")
        
        choice = input("\nElige (1-5): ").strip()
        
        if choice == "1":
            clear_cache()
        elif choice == "2":
            test_with_image()
        elif choice == "3":
            monitor_real_time()
        elif choice == "4":
            show_status()
        elif choice == "5":
            print("👋 ¡Adiós!")
            break
        else:
            print("❌ Opción inválida")

if __name__ == "__main__":
    main()
