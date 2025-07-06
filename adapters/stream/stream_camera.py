import cv2
import numpy as np
import tempfile
import os
import uuid
import threading
import time
from typing import Optional, Callable

# Base de datos temporal para cámaras
stream_db = {}
# Active stream processors
active_processors = {}

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
    def __init__(self, camera_id: str, stream_url: str, plate_recognizer, callback: Optional[Callable] = None):
        self.camera_id = camera_id
        self.stream_url = stream_url
        self.plate_recognizer = plate_recognizer
        self.callback = callback
        self.running = False
        self.thread = None
        self.last_processed = 0
        self.process_interval = 3  # Process frame every 3 seconds
        
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
                result = {
                    "cameraId": self.camera_id,
                    "plate": plate_text,
                    "timestamp": time.time()
                }
                
                print(f"[INFO] Detected plate '{plate_text}' from camera {self.camera_id}")
                
                if self.callback:
                    self.callback(result)
                    
        except Exception as e:
            print(f"[ERROR] Frame processing error: {str(e)}")

def start_stream_processing(camera_id: str, stream_url: str, plate_recognizer, callback: Optional[Callable] = None):
    if camera_id in active_processors:
        return active_processors[camera_id].start_processing()
    
    processor = StreamProcessor(camera_id, stream_url, plate_recognizer, callback)
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
