import cv2
import numpy as np
import tempfile
import os
import uuid
import threading
import time
import requests
import json
from typing import Optional, Callable

# Base de datos temporal para cámaras
stream_db = {}
# Active stream processors
active_processors = {}

def send_servo_open_request(plate_number: str, servo_url: str = None):
    """
    Envía una solicitud para abrir la puerta del servo motor cuando se detecta una placa
    """
    try:
        # URL por defecto del servo (puedes cambiarla según tu configuración)
        if not servo_url:
            servo_url = "http://192.168.1.100/open"  # Cambia esta IP por la de tu ESP32 con servo
        
        # Datos a enviar al servo
        payload = {
            "action": "open",
            "plate": plate_number,
            "timestamp": time.time()
        }
        
        print(f"[SERVO] Sending open request for plate: {plate_number}")
        
        # Enviar solicitud POST al servo
        response = requests.post(
            servo_url, 
            json=payload, 
            timeout=5,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            print(f"[SERVO] Door opened successfully for plate: {plate_number}")
            return {"status": "success", "message": "Door opened", "plate": plate_number}
        else:
            print(f"[SERVO] Failed to open door. Status: {response.status_code}")
            return {"status": "error", "message": f"HTTP {response.status_code}", "plate": plate_number}
            
    except requests.exceptions.Timeout:
        print(f"[SERVO] Timeout opening door for plate: {plate_number}")
        return {"status": "error", "message": "Timeout", "plate": plate_number}
    except Exception as e:
        print(f"[SERVO] Error opening door for plate {plate_number}: {str(e)}")
        return {"status": "error", "message": str(e), "plate": plate_number}

def save_stream_url(camera_id: str, stream_url: str):
    stream_db[camera_id] = {
        "url": stream_url
    }

    return {
        "cameraId": camera_id,
        "streamUrl": stream_url,
        "status": "saved"
    }

class StreamProcessor:
    def __init__(self, camera_id: str, stream_url: str, plate_recognizer, callback: Optional[Callable] = None, servo_url: str = None):
        self.camera_id = camera_id
        self.stream_url = stream_url
        self.plate_recognizer = plate_recognizer
        self.callback = callback
        self.servo_url = servo_url  # URL del servo motor
        self.running = False
        self.thread = None
        self.last_processed = 0
        # Reducir intervalo para ESP32 CAM - procesar cada 2 segundos
        self.process_interval = 2  # Process frame every 2 seconds for faster detection
        self.frame_count = 0
        # Historial de placas para evitar abrir repetidamente
        self.recent_plates = {}  # {plate: timestamp}
        self.plate_cooldown = 30  # 30 segundos antes de procesar la misma placa otra vez
        
    def start_processing(self):
        if self.running:
            return {"status": "already_running"}
            
        self.running = True
        self.thread = threading.Thread(target=self._process_stream)
        self.thread.daemon = True
        self.thread.start()
        
        active_processors[self.camera_id] = self
        
        return {
            "cameraId": self.camera_id,
            "status": "processing_started",
            "streamUrl": self.stream_url
        }
    
    def stop_processing(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        if self.camera_id in active_processors:
            del active_processors[self.camera_id]
            
        return {
            "cameraId": self.camera_id,
            "status": "processing_stopped"
        }
    
    def _process_stream(self):
        # Para ESP32 CAM, usar requests para obtener imágenes en lugar de cv2.VideoCapture
        if "capture" in self.stream_url:
            self._process_esp32_stream()
        else:
            self._process_video_stream()
    
    def _process_esp32_stream(self):
        """Procesar stream específico de ESP32 CAM"""
        print(f"[INFO] Started ESP32 processing for camera {self.camera_id}")
        
        while self.running:
            try:
                current_time = time.time()
                
                if current_time - self.last_processed >= self.process_interval:
                    # Obtener imagen de ESP32
                    response = requests.get(self.stream_url, timeout=10)
                    
                    if response.status_code == 200:
                        # Convertir bytes a imagen
                        import numpy as np
                        from PIL import Image
                        import io
                        
                        # Cargar imagen desde bytes
                        image = Image.open(io.BytesIO(response.content))
                        frame = np.array(image)
                        
                        # Procesar frame
                        self._process_frame(frame)
                        self.last_processed = current_time
                        self.frame_count += 1
                        
                        print(f"[INFO] ESP32 frame #{self.frame_count} processed for {self.camera_id}")
                    else:
                        print(f"[WARNING] ESP32 returned status {response.status_code}")
                
                time.sleep(0.5)  # Esperar menos tiempo entre intentos
                
            except Exception as e:
                print(f"[ERROR] ESP32 processing error for {self.camera_id}: {str(e)}")
                time.sleep(2)
        
        print(f"[INFO] Stopped ESP32 processing for camera {self.camera_id}")
    
    def _process_video_stream(self):
        """Procesar stream de video tradicional"""
        cap = cv2.VideoCapture(self.stream_url)
        
        if not cap.isOpened():
            print(f"[ERROR] Could not open stream: {self.stream_url}")
            return
            
        print(f"[INFO] Started processing stream for camera {self.camera_id}")
        
        while self.running:
            try:
                ret, frame = cap.read()
                if not ret:
                    print(f"[WARNING] Failed to read frame from {self.camera_id}")
                    time.sleep(1)
                    continue
                
                current_time = time.time()
                if current_time - self.last_processed >= self.process_interval:
                    self._process_frame(frame)
                    self.last_processed = current_time
                
                time.sleep(0.1)  # Small delay to prevent excessive CPU usage
                
            except Exception as e:
                print(f"[ERROR] Stream processing error for {self.camera_id}: {str(e)}")
                time.sleep(1)
        
        cap.release()
        print(f"[INFO] Stopped processing stream for camera {self.camera_id}")
        cap = cv2.VideoCapture(self.stream_url)
        
        if not cap.isOpened():
            print(f"[ERROR] Could not open stream: {self.stream_url}")
            return
            
        print(f"[INFO] Started processing stream for camera {self.camera_id}")
        
        while self.running:
            try:
                ret, frame = cap.read()
                if not ret:
                    print(f"[WARNING] Failed to read frame from {self.camera_id}")
                    time.sleep(1)
                    continue
                
                current_time = time.time()
                if current_time - self.last_processed >= self.process_interval:
                    self._process_frame(frame)
                    self.last_processed = current_time
                
                time.sleep(0.1)  # Small delay to prevent excessive CPU usage
                
            except Exception as e:
                print(f"[ERROR] Stream processing error for {self.camera_id}: {str(e)}")
                time.sleep(1)
        
        cap.release()
        print(f"[INFO] Stopped processing stream for camera {self.camera_id}")
    
    def _process_frame(self, frame):
        try:
            # Save frame to temporary file
            ext = '.jpg'
            temp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}{ext}")
            
            cv2.imwrite(temp_path, frame)
            
            # Recognize plate
            plate_text = self.plate_recognizer.recognize(temp_path)
            
            # Clean up temp file
            os.remove(temp_path)
            
            if plate_text and plate_text != "No plate detected":
                current_time = time.time()
                
                # Verificar si la placa ya fue procesada recientemente
                if plate_text in self.recent_plates:
                    time_since_last = current_time - self.recent_plates[plate_text]
                    if time_since_last < self.plate_cooldown:
                        print(f"[INFO] Plate '{plate_text}' detected but still in cooldown ({int(self.plate_cooldown - time_since_last)}s remaining)")
                        return
                
                # Actualizar historial de placas
                self.recent_plates[plate_text] = current_time
                
                # Limpiar placas antiguas del historial
                self._cleanup_plate_history(current_time)
                
                result = {
                    "cameraId": self.camera_id,
                    "plate": plate_text,
                    "timestamp": current_time
                }
                
                print(f"[INFO] Detected plate '{plate_text}' from camera {self.camera_id}")
                
                # Enviar solicitud al servo motor para abrir la puerta
                if self.servo_url:
                    servo_result = send_servo_open_request(plate_text, self.servo_url)
                    result["servo_response"] = servo_result
                    print(f"[INFO] Servo response: {servo_result}")
                else:
                    # Usar URL por defecto si no se especificó una
                    servo_result = send_servo_open_request(plate_text)
                    result["servo_response"] = servo_result
                
                if self.callback:
                    self.callback(result)
                    
        except Exception as e:
            print(f"[ERROR] Frame processing error: {str(e)}")
    
    def _cleanup_plate_history(self, current_time):
        """Limpiar placas antiguas del historial para evitar acumulación de memoria"""
        plates_to_remove = []
        for plate, timestamp in self.recent_plates.items():
            if current_time - timestamp > self.plate_cooldown * 2:  # Limpiar después del doble del cooldown
                plates_to_remove.append(plate)
        
        for plate in plates_to_remove:
            del self.recent_plates[plate]

def start_stream_processing(camera_id: str, stream_url: str, plate_recognizer, callback: Optional[Callable] = None, servo_url: str = None):
    if camera_id in active_processors:
        return active_processors[camera_id].start_processing()
    
    processor = StreamProcessor(camera_id, stream_url, plate_recognizer, callback, servo_url)
    return processor.start_processing()

def stop_stream_processing(camera_id: str):
    if camera_id in active_processors:
        return active_processors[camera_id].stop_processing()
    
    return {
        "cameraId": camera_id,
        "status": "not_running"
    }

def get_active_streams():
    return {
        "active_cameras": list(active_processors.keys()),
        "total_active": len(active_processors)
    }
