from pydantic import BaseModel, Field
from typing import Literal


# ---------- 1. PARKING CIRCULATION ----------

class PhotoRequest(BaseModel):
    photo: str = Field(..., description="Base64-encoded photo")
    action: Literal["entry", "exit"]

# ---------- 2. PARKING SITES ----------

class OccupancyRequest(BaseModel):
    siteId: str
    occupied: bool

# ---------- 3. MONITORING ----------

class MonitoringRequest(BaseModel):
    siteId: str
    metric: str
    value: float

# ---------- 4. CAMERA INTERFACES ----------

class CameraStreamRequest(BaseModel):
    cameraId: str
    streamUrl: str

class CameraUploadRequest(BaseModel):
    cameraId: str
    timestamp: str
    video: str  # base64-encoded video


