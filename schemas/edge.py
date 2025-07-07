from pydantic import BaseModel

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

class StreamProcessingRequest(BaseModel):
    cameraId: str
    streamUrl: str
    processInterval: int = 3  # seconds between plate recognition attempts
    servoUrl: str = None  # URL del servo motor para abrir la puerta

class StreamControlRequest(BaseModel):
    cameraId: str

# ---------- 5. USERS SYNCHRONIZATION ----------

class UserSyncRequest(BaseModel):
    force_sync: bool = False

class UserSyncResponse(BaseModel):
    success: bool
    message: str
    users_count: int
    users: list = []

class UserResponse(BaseModel):
    id: int
    username: str
    roles: list[str] = []


