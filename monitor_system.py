#!/usr/bin/env python3
"""
Monitor del Sistema de Servo Automático
=======================================

Script para monitorear en tiempo real el estado del sistema:
- Estado del servidor de detección
- Estado del ESP32 y servo
- Detecciones en tiempo real
- Logs del sistema

Uso:
    python monitor_system.py
"""

import requests
import time
import json
from datetime import datetime
import os

# Configuración
SERVER_URL = "http://localhost:8000"
ESP32_IP = "192.168.18.93"
REFRESH_INTERVAL = 2  # segundos

def clear_screen():
    """Limpiar pantalla"""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_server_status():
    """Obtener estado del servidor de detección"""
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=3)
        return {
            "status": "🟢 ONLINE" if response.status_code == 200 else f"🟡 ERROR {response.status_code}",
            "response_time": response.elapsed.total_seconds()
        }
    except Exception as e:
        return {
            "status": "🔴 OFFLINE",
            "error": str(e)
        }

def get_esp32_status():
    """Obtener estado del ESP32"""
    try:
        response = requests.get(f"http://{ESP32_IP}/servo-status", timeout=3)
        if response.status_code == 200:
            return {
                "status": "🟢 ONLINE",
                "servo_info": response.text,
                "response_time": response.elapsed.total_seconds()
            }
        else:
            return {
                "status": f"🟡 ERROR {response.status_code}",
                "response_time": response.elapsed.total_seconds()
            }
    except Exception as e:
        return {
            "status": "🔴 OFFLINE",
            "error": str(e)
        }

def get_detection_status():
    """Obtener estado de detección actual"""
    try:
        response = requests.get(f"{SERVER_URL}/detect-realtime", timeout=3)
        if response.status_code == 200:
            data = response.json()
            detected = data.get("detected", False)
            
            if detected and data.get("plates"):
                plates = data["plates"]
                plate_info = []
                for plate in plates:
                    text = plate.get("text", "")
                    confidence = plate.get("confidence", 0)
                    plate_info.append(f"{text} ({confidence:.1f}%)")
                
                return {
                    "detected": True,
                    "plates": plate_info,
                    "count": len(plates),
                    "raw_data": data
                }
            else:
                return {
                    "detected": False,
                    "plates": [],
                    "count": 0
                }
        else:
            return {
                "error": f"HTTP {response.status_code}"
            }
    except Exception as e:
        return {
            "error": str(e)
        }

def read_recent_logs():
    """Leer logs recientes del sistema automático"""
    log_file = "automatic_servo.log"
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Obtener las últimas 5 líneas
                recent_lines = lines[-5:] if len(lines) >= 5 else lines
                return [line.strip() for line in recent_lines]
        except Exception as e:
            return [f"Error leyendo logs: {e}"]
    else:
        return ["No hay archivo de logs disponible"]

def display_status():
    """Mostrar estado completo del sistema"""
    clear_screen()
    
    print("=" * 80)
    print("   MONITOR DEL SISTEMA DE SERVO AUTOMÁTICO")
    print("=" * 80)
    print(f"⏰ Actualización: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    # Estado del servidor de detección
    print("🔍 SERVIDOR DE DETECCIÓN")
    print("-" * 40)
    server_status = get_server_status()
    print(f"Estado: {server_status['status']}")
    if 'response_time' in server_status:
        print(f"Tiempo respuesta: {server_status['response_time']:.3f}s")
    if 'error' in server_status:
        print(f"Error: {server_status['error']}")
    print()
    
    # Estado del ESP32
    print("🔧 ESP32 Y SERVO")
    print("-" * 40)
    esp32_status = get_esp32_status()
    print(f"Estado: {esp32_status['status']}")
    if 'response_time' in esp32_status:
        print(f"Tiempo respuesta: {esp32_status['response_time']:.3f}s")
    if 'servo_info' in esp32_status:
        print(f"Info servo: {esp32_status['servo_info']}")
    if 'error' in esp32_status:
        print(f"Error: {esp32_status['error']}")
    print()
    
    # Estado de detección
    print("🎯 DETECCIÓN EN TIEMPO REAL")
    print("-" * 40)
    detection_status = get_detection_status()
    if 'error' in detection_status:
        print(f"❌ Error: {detection_status['error']}")
    else:
        if detection_status['detected']:
            print("🟢 PLACA DETECTADA")
            print(f"   Cantidad: {detection_status['count']}")
            for i, plate in enumerate(detection_status['plates'], 1):
                print(f"   Placa {i}: {plate}")
            print("   → Servo debería estar ABIERTO (90°)")
        else:
            print("🔴 NO HAY DETECCIÓN")
            print("   → Servo debería estar CERRADO (0°)")
    print()
    
    # Logs recientes
    print("📋 LOGS RECIENTES")
    print("-" * 40)
    recent_logs = read_recent_logs()
    for log_line in recent_logs:
        # Truncar líneas muy largas
        if len(log_line) > 70:
            log_line = log_line[:67] + "..."
        print(f"   {log_line}")
    print()
    
    # Instrucciones
    print("=" * 80)
    print("🔄 Auto-actualización cada 2 segundos | Ctrl+C para salir")
    print("💡 Para iniciar sistema automático: python automatic_plate_servo_system.py")
    print("=" * 80)

def main():
    """Función principal del monitor"""
    print("Iniciando monitor del sistema...")
    print("Presiona Ctrl+C para salir")
    
    try:
        while True:
            display_status()
            time.sleep(REFRESH_INTERVAL)
    except KeyboardInterrupt:
        clear_screen()
        print("👋 Monitor detenido")
        print()

if __name__ == "__main__":
    main()
