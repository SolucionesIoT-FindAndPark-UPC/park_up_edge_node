from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os
import tempfile
import uuid
import json
import time

# Cambiar aquí el recognizer
from adapters.fast_alpr_recognizer import FastALPRRecognizer
recognizer = FastALPRRecognizer()

from adapters.parking_sites.parking_state_updater import update_parking_status
from adapters.monitoring.monitoring_analytics import register_monitoring
from adapters.stream.stream_camera import (
    save_stream_url, 
    start_stream_processing, 
    stop_stream_processing, 
    get_active_streams
)

from adapters.users.user_sync import (
    copy_users,
    get_cached_users,
    get_user_by_id,
    get_user_by_email
)

# Import mock database functions
from adapters.users.mock_user_database import (
    copy_users_from_mock,
    get_user_by_id_mock,
    get_user_by_email_mock,
    get_user_by_plate
)

from schemas.edge import (
    OccupancyRequest,
    MonitoringRequest,
    CameraStreamRequest,
    StreamProcessingRequest,
    StreamControlRequest,
    UserSyncRequest,
    UserSyncResponse,
    UserResponse,
)

# Additional imports for mock testing
from pydantic import BaseModel

# Hybrid function to get users from either mock or MySQL
def get_user_hybrid(user_id: int = None, email: str = None, use_mock: bool = True):
    """
    Get user from mock database first, fallback to MySQL if needed
    """
    if use_mock:
        try:
            if user_id:
                return get_user_by_id_mock(user_id)
            elif email:
                return get_user_by_email_mock(email)
        except Exception as e:
            print(f"Mock database failed, trying MySQL: {e}")
    
    # Fallback to MySQL
    try:
        if user_id:
            return get_user_by_id(user_id)
        elif email:
            return get_user_by_email(email)
    except Exception as e:
        print(f"MySQL also failed: {e}")
        return None

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

app = FastAPI()

# Global variable to store last detected plate
last_detected_plate = {"plate": "", "timestamp": 0, "confidence": 0}
# Variable to track unique detections
detection_history = []

@app.get("/", response_class=HTMLResponse)
async def get_plate_recognition_interface():
    """Interfaz web para reconocimiento de placas en tiempo real"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Reconocimiento de Placas - Park Up</title>
        <meta charset="UTF-8">
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f0f0f0;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                text-align: center;
                color: #333;
                margin-bottom: 30px;
            }
            .upload-area {
                border: 3px dashed #ddd;
                border-radius: 10px;
                padding: 40px;
                text-align: center;
                margin: 20px 0;
                background-color: #fafafa;
                transition: all 0.3s ease;
            }
            .upload-area:hover {
                border-color: #007bff;
                background-color: #f0f8ff;
            }
            .upload-area.dragover {
                border-color: #007bff;
                background-color: #e6f3ff;
            }
            input[type="file"] {
                display: none;
            }
            .upload-btn {
                background-color: #007bff;
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                margin: 10px;
            }
            .upload-btn:hover {
                background-color: #0056b3;
            }
            .result {
                margin: 20px 0;
                padding: 20px;
                border-radius: 5px;
                text-align: center;
                font-size: 18px;
                min-height: 60px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .result.success {
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                color: #155724;
            }
            .result.error {
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                color: #721c24;
            }
            .result.waiting {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                color: #856404;
            }
            .plate-display {
                font-size: 32px;
                font-weight: bold;
                font-family: 'Courier New', monospace;
                letter-spacing: 3px;
                padding: 20px;
                background-color: #000;
                color: #fff;
                border-radius: 10px;
                margin: 20px 0;
                text-align: center;
                min-height: 80px;
                display: flex;
                align-items: center;
                justify-content: center;
                border: 3px solid #ffcc00;
            }
            .loading {
                display: none;
                text-align: center;
                margin: 20px 0;
            }
            .spinner {
                border: 4px solid #f3f3f3;
                border-radius: 50%;
                border-top: 4px solid #3498db;
                width: 40px;
                height: 40px;
                animation: spin 2s linear infinite;
                margin: 0 auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .instructions {
                background-color: #e7f3ff;
                border: 1px solid #b8daff;
                color: #004085;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }
            .auto-detect {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 20px;
                border-radius: 5px;
                margin: 20px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚗 Reconocimiento de Placas</h1>
            
            <div class="instructions">
                <strong>Instrucciones:</strong><br>
                1. Haz clic en "Seleccionar Imagen" o arrastra una foto de la placa<br>
                2. La placa se detectará automáticamente<br>
                3. El número aparecerá en la pantalla negra de abajo
            </div>

            <div class="upload-area" id="uploadArea">
                <p>📷 Arrastra una imagen aquí o haz clic para seleccionar</p>
                <button class="upload-btn" onclick="document.getElementById('fileInput').click()">
                    Seleccionar Imagen
                </button>
                <input type="file" id="fileInput" accept="image/*" onchange="uploadImage(this.files[0])">
            </div>

            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Analizando imagen...</p>
            </div>

            <div class="result waiting" id="result">
                Selecciona una imagen para detectar la placa
            </div>

            <div class="plate-display" id="plateDisplay">
                - - - - - -
            </div>

            <div class="auto-detect">
                <h3>🔄 Detección Automática</h3>
                <p>Estado de la cámara en tiempo real: <span id="streamStatus">Detenido</span></p>
                <button class="upload-btn" onclick="startAutoDetection()">Iniciar Detección Automática</button>
                <button class="upload-btn" onclick="stopAutoDetection()">Detener Detección</button>
                <div id="autoResult"></div>
            </div>
        </div>

        <script>
            const uploadArea = document.getElementById('uploadArea');
            const fileInput = document.getElementById('fileInput');
            const loading = document.getElementById('loading');
            const result = document.getElementById('result');
            const plateDisplay = document.getElementById('plateDisplay');
            const streamStatus = document.getElementById('streamStatus');
            const autoResult = document.getElementById('autoResult');

            // Drag and drop functionality
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });

            uploadArea.addEventListener('dragleave', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    uploadImage(files[0]);
                }
            });

            async function uploadImage(file) {
                if (!file) return;

                loading.style.display = 'block';
                result.className = 'result waiting';
                result.textContent = 'Procesando imagen...';
                plateDisplay.textContent = 'ANALIZANDO...';

                const formData = new FormData();
                formData.append('file', file);

                try {
                    const response = await fetch('/edge/plate-recognition', {
                        method: 'POST',
                        body: formData
                    });

                    const data = await response.json();
                    
                    loading.style.display = 'none';

                    if (response.ok) {
                        if (data.plate && data.plate !== 'No plate detected') {
                            result.className = 'result success';
                            result.textContent = `✅ Placa detectada: ${data.plate}`;
                            plateDisplay.textContent = data.plate;
                        } else {
                            result.className = 'result error';
                            result.textContent = '❌ No se detectó ninguna placa en la imagen';
                            plateDisplay.textContent = 'NO DETECTADA';
                        }
                    } else {
                        throw new Error(data.detail || 'Error en el servidor');
                    }
                } catch (error) {
                    loading.style.display = 'none';
                    result.className = 'result error';
                    result.textContent = `❌ Error: ${error.message}`;
                    plateDisplay.textContent = 'ERROR';
                }
            }

            // Auto detection functions
            let autoDetectionInterval = null;

            async function startAutoDetection() {
                try {
                    const response = await fetch('/edge/camera/stream/test/auto_camera');
                    if (response.ok) {
                        streamStatus.textContent = 'Activo';
                        streamStatus.style.color = 'green';
                        
                        // Start polling for results
                        autoDetectionInterval = setInterval(checkAutoResults, 2000);
                    }
                } catch (error) {
                    console.error('Error starting auto detection:', error);
                }
            }

            async function stopAutoDetection() {
                try {
                    const response = await fetch('/edge/camera/stream/stop-processing', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({cameraId: 'auto_camera'})
                    });
                    
                    streamStatus.textContent = 'Detenido';
                    streamStatus.style.color = 'red';
                    
                    if (autoDetectionInterval) {
                        clearInterval(autoDetectionInterval);
                        autoDetectionInterval = null;
                    }
                } catch (error) {
                    console.error('Error stopping auto detection:', error);
                }
            }

            async function checkAutoResults() {
                try {
                    const response = await fetch('/edge/plate-recognition/last-result');
                    if (response.ok) {
                        const data = await response.json();
                        if (data.plate && data.plate !== '' && data.timestamp > 0) {
                            plateDisplay.textContent = data.plate;
                            autoResult.innerHTML = `<p style="color: green;">🔄 Última detección: ${data.plate} (${new Date(data.timestamp * 1000).toLocaleTimeString()})</p>`;
                        }
                    }
                } catch (error) {
                    console.error('Error checking auto results:', error);
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/edge/plate-recognition")
async def recognize_plate_upload(file: UploadFile = File(...)):
    """Reconocer placa desde imagen subida"""
    global last_detected_plate, detection_history
    
    try:
        contents = await file.read()
        ext = os.path.splitext(file.filename)[1].lower()
        temp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}{ext}")

        with open(temp_path, 'wb') as f:
            f.write(contents)

        plate_text = recognizer.recognize(temp_path)
        current_time = time.time()
        
        # Update last detected plate with current detection
        last_detected_plate = {
            "plate": plate_text if plate_text != "No plate detected" else "",
            "timestamp": current_time,
            "confidence": 1.0
        }
        
        # Add to detection history
        detection_history.append({
            "plate": plate_text,
            "timestamp": current_time,
            "source": "upload"
        })
        
        # Keep only last 10 detections
        if len(detection_history) > 10:
            detection_history = detection_history[-10:]
        
        # Clean up temp file
        os.remove(temp_path)
        
        return {"plate": plate_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.get("/edge/plate-recognition/last-result")
async def get_last_plate_result():
    """Obtener el último resultado de detección de placa"""
    return last_detected_plate

@app.get("/edge/plate-recognition/last-plate-string")
async def get_last_plate_string():
    """Obtener solo la última placa detectada como string simple"""
    if last_detected_plate["plate"] and last_detected_plate["plate"] != "No plate detected":
        return {"plate": last_detected_plate["plate"]}
    return {"plate": ""}

@app.get("/edge/plate-recognition/history")
async def get_detection_history():
    """Obtener historial de detecciones"""
    return {"history": detection_history}

@app.post("/edge/plate-recognition/clear-cache")
async def clear_detection_cache():
    """Limpiar cache de detecciones"""
    global last_detected_plate, detection_history
    last_detected_plate = {"plate": "", "timestamp": 0, "confidence": 0}
    detection_history = []
    return {"message": "Cache cleared successfully"}

@app.get("/edge/plate-recognition/debug")
async def get_debug_info():
    """Información de debug para detección"""
    return {
        "last_detected": last_detected_plate,
        "history_count": len(detection_history),
        "recent_history": detection_history[-3:] if detection_history else []
    }

@app.get("/edge/esp32/start/{esp32_ip}")
async def quick_start_esp32(esp32_ip: str):
    """Inicio rápido para ESP32 CAM con IP específica"""
    global last_detected_plate
    
    camera_id = f"esp32_{esp32_ip.replace('.', '_')}"
    stream_url = f"http://{esp32_ip}/capture"
    
    def esp32_callback(result):
        global last_detected_plate
        plate = result.get("plate", "")
        if plate and plate != "No plate detected":
            last_detected_plate = {
                "plate": plate,
                "timestamp": result.get("timestamp", time.time()),
                "confidence": 1.0
            }
            print(f"🚗 ESP32 DETECTÓ: {plate}")
    
    return start_stream_processing(
        camera_id=camera_id,
        stream_url=stream_url,
        plate_recognizer=recognizer,
        callback=esp32_callback
    )

@app.post("/edge/parking/circulation")
async def recognize_plate(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        ext = os.path.splitext(file.filename)[1].lower()
        temp_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}{ext}")

        with open(temp_path, 'wb') as f:
            f.write(contents)

        plate_text = recognizer.recognize(temp_path)
        return {"plate": plate_text}

    except Exception as e:
        return {"error": str(e)}

@app.post("/edge/parking/sites/occupancy")
async def change_occupancy(data: OccupancyRequest):
    return update_parking_status(data.siteId, data.occupied)

@app.post("/edge/monitoring/data")
async def post_monitoring_data(data: MonitoringRequest):
    return register_monitoring(data.siteId, data.metric, data.value)

@app.post("/edge/camera/stream")
async def live_video_stream(data: CameraStreamRequest):
    return save_stream_url(data.cameraId, data.streamUrl)

@app.post("/edge/camera/stream/start-processing")
async def start_stream_plate_recognition(data: StreamProcessingRequest):
    """Start processing ESP32 cam stream for automatic plate recognition"""
    def plate_detected_callback(result):
        global last_detected_plate, detection_history
        plate = result.get("plate", "")
        current_time = result.get("timestamp", time.time())
        
        print(f"[CALLBACK] Plate detected: {plate} at {current_time}")
        
        # Always update with current detection (even if empty)
        last_detected_plate = {
            "plate": plate if plate != "No plate detected" else "",
            "timestamp": current_time,
            "confidence": 1.0
        }
        
        # Add to history only if valid plate
        if plate and plate != "No plate detected":
            detection_history.append({
                "plate": plate,
                "timestamp": current_time,
                "source": "stream"
            })
            
            # Keep only last 10 detections
            if len(detection_history) > 10:
                detection_history = detection_history[-10:]
    
    return start_stream_processing(
        camera_id=data.cameraId, 
        stream_url=data.streamUrl, 
        plate_recognizer=recognizer,
        callback=plate_detected_callback,
        servo_url=data.servoUrl
    )

@app.post("/edge/camera/stream/stop-processing")
async def stop_stream_plate_recognition(data: StreamControlRequest):
    """Stop processing ESP32 cam stream"""
    return stop_stream_processing(data.cameraId)

@app.get("/edge/camera/stream/status")
async def get_stream_status():
    """Get status of all active stream processors"""
    return get_active_streams()

@app.get("/edge/camera/stream/test/{camera_id}")
async def test_esp32_stream(camera_id: str):
    """Test endpoint to quickly start processing a common ESP32 cam URL format"""
    # Common ESP32 cam stream URL format
    esp32_stream_url = f"http://192.168.18.85/capture"  # Updated to use the working endpoint
    
    def plate_detected_callback(result):
        global last_detected_plate
        print(f"[TEST CALLBACK] Plate detected: {result}")
        # Update global variable for web interface
        last_detected_plate = {
            "plate": result.get("plate", ""),
            "timestamp": result.get("timestamp", time.time()),
            "confidence": 1.0
        }
    
    return start_stream_processing(
        camera_id=camera_id,
        stream_url=esp32_stream_url,
        plate_recognizer=recognizer,
        callback=plate_detected_callback
    )

@app.post("/edge/parking/circulation/esp32/{camera_id}")
async def start_esp32_circulation_monitoring(camera_id: str, stream_url: str = "http://192.168.18.85/capture"):
    """
    Start monitoring ESP32 cam stream for parking circulation (plate detection)
    This endpoint combines stream processing with your circulation detection workflow
    """
    def circulation_callback(result):
        print(f"[CIRCULATION] Vehicle detected with plate '{result['plate']}' from camera {result['cameraId']}")
        # Here you can add logic to:
        # - Update parking site occupancy
        # - Send data to backend
        # - Log vehicle entry/exit
        # - Send notifications
    
    return start_stream_processing(
        camera_id=camera_id,
        stream_url=stream_url,
        plate_recognizer=recognizer,
        callback=circulation_callback
    )

@app.delete("/edge/parking/circulation/esp32/{camera_id}")
async def stop_esp32_circulation_monitoring(camera_id: str):
    """Stop monitoring ESP32 cam stream for parking circulation"""
    return stop_stream_processing(camera_id)

# ---------- USERS SYNCHRONIZATION ENDPOINTS ----------

@app.post("/edge/users/sync", response_model=UserSyncResponse)
async def sync_users_from_mysql(data: UserSyncRequest):
    """
    Synchronize users from MySQL database to edge node and backend
    This will copy all active users from the MySQL database
    """
    try:
        result = copy_users()
        return UserSyncResponse(
            success=result["success"],
            message=result["message"],
            users_count=result["users_count"],
            users=result.get("users", [])
        )
    except Exception as e:
        return UserSyncResponse(
            success=False,
            message=f"Error during user synchronization: {str(e)}",
            users_count=0,
            users=[]
        )

@app.get("/edge/users/cached")
async def get_cached_users_list():
    """Get list of cached users - tries mock database first, then MySQL cache"""
    try:
        # First try mock database
        try:
            users = copy_users_from_mock()
            if users:
                return {
                    "success": True,
                    "users_count": len(users),
                    "users": users,
                    "source": "mock_database"
                }
        except Exception as e:
            print(f"Mock database failed, trying MySQL cache: {e}")
        
        # Fallback to MySQL cache
        users = get_cached_users()
        return {
            "success": True,
            "users_count": len(users),
            "users": users,
            "source": "mysql_cache"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error getting cached users: {str(e)}",
            "users_count": 0,
            "users": []
        }

@app.get("/edge/users/{user_id}", response_model=UserResponse)
async def get_user_by_id_endpoint(user_id: int):
    """Get specific user by ID - tries mock database first, then MySQL"""
    try:
        # First try mock database
        user = get_user_hybrid(user_id=user_id, use_mock=True)
        
        if user:
            # Return only the fields that match Java UserResource
            return UserResponse(
                id=user["id"],
                username=user["username"],
                roles=user.get("roles", ["user"])
            )
        else:
            raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user: {str(e)}")

@app.get("/edge/users/email/{email}", response_model=UserResponse)
async def get_user_by_email_endpoint(email: str):
    """Get specific user by email - tries mock database first, then MySQL"""
    try:
        # First try mock database
        user = get_user_hybrid(email=email, use_mock=True)
        
        if user:
            # Return only the fields that match Java UserResource
            return UserResponse(
                id=user["id"],
                username=user["username"],
                roles=user.get("roles", ["user"])
            )
        else:
            raise HTTPException(status_code=404, detail=f"User with email {email} not found")
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user: {str(e)}")

# ---------- USER MANAGEMENT ENDPOINTS ----------

# Additional model for plate detection
class PlateDetectionRequest(BaseModel):
    license_plate: str
    camera_id: str

@app.get("/edge/users/{user_id}", response_model=UserResponse)
async def get_user_by_id_endpoint(user_id: int):
    """Get specific user by ID - tries mock database first, then MySQL"""
    try:
        # First try mock database
        user = get_user_hybrid(user_id=user_id, use_mock=True)
        
        if user:
            # Return only the fields that match Java UserResource
            return UserResponse(
                id=user["id"],
                username=user["username"],
                roles=user.get("roles", ["user"])
            )
        else:
            raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user: {str(e)}")

@app.get("/edge/users/list/all")
async def get_all_users():
    """Get all users - returns complete user information from mock database or MySQL"""
    try:
        # First try mock database
        try:
            users = copy_users_from_mock()
            if users:
                return {
                    "success": True,
                    "users_count": len(users),
                    "users": users,
                    "source": "mock_database",
                    "message": f"Retrieved {len(users)} users from mock database"
                }
        except Exception as e:
            print(f"Mock database failed, trying MySQL: {e}")
        
        # Fallback to MySQL
        try:
            # Force a sync from MySQL if no mock data
            result = copy_users()
            if result.get("success", False):
                users = result.get("users", [])
                return {
                    "success": True,
                    "users_count": len(users),
                    "users": users,
                    "source": "mysql_database",
                    "message": f"Retrieved {len(users)} users from MySQL"
                }
        except Exception as mysql_error:
            print(f"MySQL also failed: {mysql_error}")
            
        # If both fail, return empty
        return {
            "success": False,
            "users_count": 0,
            "users": [],
            "source": "none",
            "message": "Both mock and MySQL databases failed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting all users: {str(e)}")

@app.get("/detect-realtime")
async def detect_realtime_plates():
    """
    Endpoint para detección de placas en tiempo real
    Retorna el estado actual de detección compatible con el sistema automático
    """
    global last_detected_plate
    
    current_time = time.time()
    
    # Verificar si hay una detección reciente (últimos 5 segundos)
    if (last_detected_plate["timestamp"] > 0 and 
        (current_time - last_detected_plate["timestamp"]) < 5.0):
        
        plate_text = last_detected_plate["plate"]
        
        # Si hay una placa válida detectada
        if plate_text and plate_text != "" and plate_text != "No plate detected":
            return {
                "detected": True,
                "plates": [{
                    "text": plate_text,
                    "confidence": last_detected_plate.get("confidence", 1.0) * 100,
                    "timestamp": last_detected_plate["timestamp"]
                }],
                "timestamp": current_time,
                "status": "plate_detected",
                "message": f"Placa detectada: {plate_text}"
            }
    
    # No hay detección válida o es muy antigua
    return {
        "detected": False,
        "plates": [],
        "timestamp": current_time,
        "status": "no_detection",
        "message": "No se detectaron placas"
    }

@app.get("/health")
async def health_check():
    """Endpoint de salud para verificar que el servidor esté funcionando"""
    return {
        "status": "ok",
        "timestamp": time.time(),
        "service": "Park Up Edge Node",
        "version": "1.0.0"
    }

@app.on_event("startup")
async def startup_event():
    """Configuración inicial al iniciar el servidor"""
    print("🚀 Iniciando Park Up Edge Node...")
    print("📋 Configurando detección automática de placas...")
    
    # Iniciar detección automática de placas desde ESP32
    try:
        # Usar el endpoint existente para iniciar el stream
        esp32_ip = "192.168.18.93"
        camera_id = "auto_detection_camera"
        stream_url = f"http://{esp32_ip}/capture"
        
        def realtime_callback(result):
            global last_detected_plate, detection_history
            plate = result.get("plate", "")
            current_time = result.get("timestamp", time.time())
            
            print(f"🎯 [TIEMPO REAL] Placa: '{plate}' - Tiempo: {current_time}")
            
            # Actualizar detección global
            last_detected_plate = {
                "plate": plate if plate != "No plate detected" else "",
                "timestamp": current_time,
                "confidence": 1.0
            }
            
            # Agregar al historial solo si es válida
            if plate and plate != "No plate detected" and plate != "":
                detection_history.append({
                    "plate": plate,
                    "timestamp": current_time,
                    "source": "realtime_auto"
                })
                
                # Mantener solo las últimas 10 detecciones
                if len(detection_history) > 10:
                    detection_history = detection_history[-10:]
                
                print(f"✅ [GUARDADO] Placa '{plate}' agregada al historial")
        
        # Iniciar procesamiento automático
        result = start_stream_processing(
            camera_id=camera_id,
            stream_url=stream_url,
            plate_recognizer=recognizer,
            callback=realtime_callback
        )
        
        if result.get("success"):
            print(f"✅ Detección automática iniciada: {stream_url}")
        else:
            print(f"⚠️ No se pudo iniciar detección automática: {result.get('message', 'Error desconocido')}")
            
    except Exception as e:
        print(f"❌ Error iniciando detección automática: {e}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando servidor FastAPI en puerto 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
