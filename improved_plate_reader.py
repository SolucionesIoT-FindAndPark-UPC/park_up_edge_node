#!/usr/bin/env python3
"""
Lectura de placas ESP32 - Versión Mejorada
Captura imágenes individuales del ESP32 usando requests
"""

import requests
import tempfile
import os
import uuid
import time
import sys

# Add the current directory to the path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the recognizer
from adapters.fast_alpr_recognizer import FastALPRRecognizer

def capture_and_analyze():
    """Capturar imagen del ESP32 y analizarla"""
    
    print("🚗 Lector de Placas ESP32 - Versión Mejorada")
    print("📍 IP: 192.168.18.85")
    print("🔗 Endpoint: /capture")
    print("=" * 50)
    
    # Initialize recognizer
    print("🔧 Inicializando reconocedor de placas...")
    try:
        recognizer = FastALPRRecognizer()
        print("✅ Reconocedor inicializado correctamente")
    except Exception as e:
        print(f"❌ Error inicializando reconocedor: {e}")
        return
    
    esp32_url = "http://192.168.18.85/capture"
    
    print(f"\n🔍 Comenzando captura desde: {esp32_url}")
    print("⏰ Capturando una imagen cada 5 segundos")
    print("🎯 Presiona Ctrl+C para detener")
    print("-" * 50)
    
    capture_count = 0
    plates_detected = 0
    
    try:
        while True:
            capture_count += 1
            print(f"\n📸 Captura #{capture_count}")
            
            try:
                # Capture image using requests
                print("🔗 Solicitando imagen al ESP32...")
                response = requests.get(esp32_url, timeout=10)
                
                if response.status_code == 200:
                    print(f"✅ Imagen recibida ({len(response.content)} bytes)")
                    
                    # Save to temporary file
                    temp_path = os.path.join(tempfile.gettempdir(), f"esp32_capture_{uuid.uuid4()}.jpg")
                    
                    with open(temp_path, 'wb') as f:
                        f.write(response.content)
                    
                    print(f"💾 Imagen guardada: {temp_path}")
                    
                    # Analyze with recognizer
                    print("🔍 Analizando imagen para placas...")
                    plate_text = recognizer.recognize(temp_path)
                    
                    # Clean up
                    os.remove(temp_path)
                    
                    if plate_text and plate_text != "No plate detected":
                        plates_detected += 1
                        print("🎯" + "="*50)
                        print(f"🚗 ¡PLACA DETECTADA! -> '{plate_text}'")
                        print(f"📊 Total placas encontradas: {plates_detected}")
                        print("🎯" + "="*50)
                        
                        # You can add additional actions here:
                        # - Send to database
                        # - Send notification
                        # - Log to file
                        # - etc.
                        
                    else:
                        print("📋 No se detectaron placas en esta imagen")
                    
                else:
                    print(f"❌ Error HTTP: {response.status_code}")
                    
            except requests.RequestException as e:
                print(f"❌ Error de conexión: {e}")
                print("💡 Verifica que el ESP32 esté encendido y accesible")
                
            except Exception as e:
                print(f"❌ Error procesando imagen: {e}")
            
            # Wait before next capture
            print("⏳ Esperando 5 segundos...")
            time.sleep(5)
            
    except KeyboardInterrupt:
        print(f"\n🛑 Deteniendo captura de placas...")
        print("📊 RESUMEN FINAL:")
        print(f"   🖼️  Capturas realizadas: {capture_count}")
        print(f"   🚗 Placas detectadas: {plates_detected}")
        if plates_detected > 0:
            print(f"   📈 Tasa de detección: {(plates_detected/capture_count)*100:.1f}%")
        print("✅ ¡Sesión finalizada!")

def test_esp32_connection():
    """Test ESP32 connection first"""
    print("🧪 Probando conexión con ESP32...")
    try:
        response = requests.get("http://192.168.18.85/capture", timeout=5)
        if response.status_code == 200:
            print(f"✅ ESP32 responde correctamente ({len(response.content)} bytes)")
            return True
        else:
            print(f"❌ ESP32 respondió con código: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ No se pudo conectar al ESP32: {e}")
        print("💡 Verifica:")
        print("   - ESP32 esté encendido")
        print("   - IP correcta: 192.168.18.85")
        print("   - Acceso desde navegador: http://192.168.18.85/")
        return False

if __name__ == "__main__":
    if test_esp32_connection():
        print()
        capture_and_analyze()
    else:
        print("\n❌ No se puede continuar sin conexión al ESP32")
