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
from adapters.stream.stream_camera import save_stream_url

from schemas.edge import (
    OccupancyRequest,
    MonitoringRequest,
    CameraStreamRequest,
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
