from fastapi import FastAPI
import httpx
import base64
from schemas.edge import PhotoRequest, OccupancyRequest, MonitoringRequest, CameraStreamRequest, \
    CameraUploadRequest

app = FastAPI()

# 1. PARKING CIRCULATION

@app.post("/edge/parking/circulation")
async def get_photo(data: PhotoRequest):
    # Mock logic here
    return {"success": True}

def verify_plate(plate):
    url = "http://backend-host:8000/edge/parking/verify-plate"
    payload = {"plate": plate}
    r = httpx.post(url, json=payload)
    print(r.json())

# 2. PARKING SITES

@app.post("/edge/parking/sites/occupancy")
async def change_occupancy(data: OccupancyRequest):
    return {"status": "OK"}

# 3. MONITORING

@app.post("/edge/monitoring/data")
async def post_monitoring_data(data: MonitoringRequest):
    return {"status": "OK"}

# 4. INTERFACES

@app.post("/edge/camera/stream")
async def live_video_stream(data: CameraStreamRequest):
    return {"received": True}

def upload_video_to_backend(video):
    url = "http://backend-host:8000/edge/parking/verify-plate"
    payload = {"video": video}
    r = httpx.post(url, json=payload)
    print(r.json())