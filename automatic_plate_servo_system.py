#!/usr/bin/env python3
"""
Sistema Automático de Control de Servo basado en Detección de Placas
======================================================================

Este sistema:
1. Detecta placas en tiempo real usando la API de detección
2. Automáticamente envía señales al ESP32 para controlar el servo
3. valor = true → placa detectada → servo abre (90°)
4. valor = false → no hay placa → servo cierra (0°)
5. Incluye logging completo y manejo de errores

Uso:
    python automatic_plate_servo_system.py

Requisitos:
    - ESP32 con código de servo funcionando
    - FastAPI server de detección ejecutándose
    - Conexión WiFi estable
"""

import requests
import time
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import threading
import signal
import sys

# ========== CONFIGURACIÓN ==========
SERVER_URL = "http://localhost:8000"  # FastAPI server de detección
ESP32_IP = "192.168.18.93"            # IP del ESP32
DETECTION_INTERVAL = 1.0              # Intervalo de detección en segundos
AUTO_CLOSE_TIMEOUT = 3.0              # Tiempo sin detección para cerrar servo
LOG_LEVEL = logging.INFO

# Configurar logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automatic_servo.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AutomaticServoSystem:
    def __init__(self):
        self.running = False
        self.last_detection_time = 0
        self.current_plate = None
        self.servo_open = False
        self.detection_count = 0
        self.error_count = 0
        
    def start(self):
        """Iniciar el sistema automático"""
        logger.info("🚀 Iniciando Sistema Automático de Control de Servo")
        
        # Verificar conexiones iniciales
        if not self._test_detection_server():
            logger.error("❌ No se puede conectar al servidor de detección")
            return False
            
        if not self._test_esp32_connection():
            logger.error("❌ No se puede conectar al ESP32")
            return False
            
        # Configurar manejo de señales para parada limpia
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.running = True
        logger.info("✅ Sistema iniciado exitosamente")
        
        # Iniciar loop principal
        try:
            self._main_loop()
        except KeyboardInterrupt:
            logger.info("👋 Deteniendo sistema por interrupción del usuario")
        except Exception as e:
            logger.error(f"💥 Error crítico en el sistema: {e}")
        finally:
            self._cleanup()
            
        return True
    
    def _main_loop(self):
        """Loop principal del sistema"""
        logger.info("🔄 Iniciando loop principal de detección")
        
        while self.running:
            try:
                # 1. Detectar placas
                detected_plate = self._detect_plate()
                current_time = time.time()
                
                # 2. Procesar detección
                if detected_plate:
                    # PLACA DETECTADA → valor = true → abrir servo
                    self._handle_plate_detected(detected_plate, current_time)
                else:
                    # NO HAY PLACA → verificar si cerrar servo
                    self._handle_no_plate_detected(current_time)
                
                # 3. Esperar intervalo
                time.sleep(DETECTION_INTERVAL)
                
            except Exception as e:
                self.error_count += 1
                logger.error(f"❌ Error en loop principal: {e}")
                
                # Si hay muchos errores consecutivos, pausar más tiempo
                if self.error_count > 5:
                    logger.warning("⚠️ Muchos errores, pausando 10 segundos...")
                    time.sleep(10)
                    self.error_count = 0
                else:
                    time.sleep(1)
    
    def _detect_plate(self) -> Optional[str]:
        """Detectar placa usando la API"""
        try:
            # Usar endpoint de detección directa
            response = requests.get(
                f"{SERVER_URL}/detect-realtime",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verificar si hay detección
                if data.get("detected") and data.get("plates"):
                    plates = data["plates"]
                    if plates and len(plates) > 0:
                        plate_number = plates[0].get("text", "").strip()
                        if plate_number:
                            return plate_number
                
                return None
                
            else:
                logger.warning(f"⚠️ Respuesta de detección: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.warning("⏱️ Timeout en detección de placa")
            return None
        except requests.exceptions.ConnectionError:
            logger.warning("🔌 Error de conexión con servidor de detección")
            return None
        except Exception as e:
            logger.error(f"❌ Error detectando placa: {e}")
            return None
    
    def _handle_plate_detected(self, plate_number: str, current_time: float):
        """Manejar cuando se detecta una placa"""
        self.last_detection_time = current_time
        self.detection_count += 1
        
        # Si es una nueva placa o el servo está cerrado
        if self.current_plate != plate_number or not self.servo_open:
            self.current_plate = plate_number
            
            logger.info(f"🎯 PLACA DETECTADA: {plate_number} (#{self.detection_count})")
            
            # valor = true → Enviar señal para abrir servo
            if self._send_plate_detected_signal(plate_number):
                self.servo_open = True
                logger.info("✅ Servo ABIERTO (90°)")
            else:
                logger.error("❌ Error enviando señal de apertura")
        
        # Reset contador de errores en detección exitosa
        self.error_count = 0
    
    def _handle_no_plate_detected(self, current_time: float):
        """Manejar cuando NO se detecta placa"""
        # Si hay un timeout sin detección y el servo está abierto
        if (self.servo_open and 
            self.last_detection_time > 0 and 
            (current_time - self.last_detection_time) > AUTO_CLOSE_TIMEOUT):
            
            logger.info(f"⏰ Sin detección por {AUTO_CLOSE_TIMEOUT}s, cerrando servo")
            
            # valor = false → Enviar señal para cerrar servo
            if self._send_plate_lost_signal():
                self.servo_open = False
                self.current_plate = None
                logger.info("✅ Servo CERRADO (0°)")
            else:
                logger.error("❌ Error enviando señal de cierre")
    
    def _send_plate_detected_signal(self, plate_number: str) -> bool:
        """Enviar señal de placa detectada al ESP32"""
        try:
            url = f"http://{ESP32_IP}/plate-detected"
            payload = {
                "plate": plate_number,
                "timestamp": time.time(),
                "detected": True,
                "action": "open_servo"
            }
            
            response = requests.post(
                url, 
                json=payload,
                timeout=3
            )
            
            if response.status_code == 200:
                logger.debug(f"📤 Señal enviada al ESP32: valor=true, placa={plate_number}")
                return True
            else:
                logger.warning(f"⚠️ ESP32 respuesta: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error enviando señal de detección: {e}")
            return False
    
    def _send_plate_lost_signal(self) -> bool:
        """Enviar señal de placa perdida al ESP32"""
        try:
            url = f"http://{ESP32_IP}/plate-lost"
            payload = {
                "detected": False,
                "timestamp": time.time(),
                "action": "close_servo"
            }
            
            response = requests.post(
                url,
                json=payload, 
                timeout=3
            )
            
            if response.status_code == 200:
                logger.debug("📤 Señal enviada al ESP32: valor=false")
                return True
            else:
                logger.warning(f"⚠️ ESP32 respuesta: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error enviando señal de pérdida: {e}")
            return False
    
    def _test_detection_server(self) -> bool:
        """Probar conexión con servidor de detección"""
        try:
            logger.info(f"🔍 Probando conexión con servidor de detección: {SERVER_URL}")
            response = requests.get(f"{SERVER_URL}/health", timeout=5)
            
            if response.status_code == 200:
                logger.info("✅ Servidor de detección conectado")
                return True
            else:
                logger.error(f"❌ Servidor responde con código: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error conectando con servidor: {e}")
            return False
    
    def _test_esp32_connection(self) -> bool:
        """Probar conexión con ESP32"""
        try:
            logger.info(f"🔧 Probando conexión con ESP32: {ESP32_IP}")
            response = requests.get(f"http://{ESP32_IP}/servo-status", timeout=5)
            
            if response.status_code == 200:
                logger.info("✅ ESP32 conectado")
                logger.info(f"📋 Estado del servo: {response.text}")
                return True
            else:
                logger.error(f"❌ ESP32 responde con código: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error conectando con ESP32: {e}")
            return False
    
    def _signal_handler(self, signum, frame):
        """Manejar señales del sistema para parada limpia"""
        logger.info(f"📡 Señal recibida: {signum}")
        self.running = False
    
    def _cleanup(self):
        """Limpieza final del sistema"""
        logger.info("🧹 Ejecutando limpieza final...")
        
        # Cerrar servo si está abierto
        if self.servo_open:
            logger.info("🔒 Cerrando servo antes de salir...")
            self._send_plate_lost_signal()
        
        # Mostrar estadísticas
        logger.info(f"📊 Estadísticas finales:")
        logger.info(f"   - Detecciones totales: {self.detection_count}")
        logger.info(f"   - Errores totales: {self.error_count}")
        logger.info("👋 Sistema detenido correctamente")

def main():
    """Función principal"""
    print("=" * 60)
    print("   SISTEMA AUTOMÁTICO DE CONTROL DE SERVO")
    print("   Detección de Placas → Control Automático")
    print("=" * 60)
    print()
    print("🎯 Lógica:")
    print("   • Placa detectada (valor=true)  → Servo ABRE (90°)")
    print("   • Sin placa (valor=false)       → Servo CIERRA (0°)")
    print("   • Timeout automático después de 3 segundos")
    print()
    print("⚙️ Configuración:")
    print(f"   • Servidor detección: {SERVER_URL}")
    print(f"   • ESP32 IP: {ESP32_IP}")
    print(f"   • Intervalo detección: {DETECTION_INTERVAL}s")
    print(f"   • Timeout auto-cierre: {AUTO_CLOSE_TIMEOUT}s")
    print()
    print("🔧 Para detener: Ctrl+C")
    print("=" * 60)
    print()
    
    # Crear e iniciar sistema
    system = AutomaticServoSystem()
    system.start()

if __name__ == "__main__":
    main()
