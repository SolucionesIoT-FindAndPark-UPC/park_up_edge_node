from fastapi import FastAPI, UploadFile, File
import os
import tempfile
import uuid
from dotenv import load_dotenv

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

from schemas.edge import (
    OccupancyRequest,
    MonitoringRequest,
    CameraStreamRequest,
    StreamProcessingRequest,
    StreamControlRequest,
)

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

app = FastAPI()

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
        print(f"[CALLBACK] Plate detected: {result}")
        # You can add additional logic here, like sending to backend or logging
    
    return start_stream_processing(
        camera_id=data.cameraId, 
        stream_url=data.streamUrl, 
        plate_recognizer=recognizer,
        callback=plate_detected_callback
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
        print(f"[TEST CALLBACK] Plate detected: {result}")
    
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
