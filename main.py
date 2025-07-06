from fastapi import FastAPI, UploadFile, File, HTTPException
from dotenv import load_dotenv
import os
import tempfile
import uuid

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
            "message": "No users found in mock database or MySQL",
            "users_count": 0,
            "users": [],
            "source": "none"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error getting all users: {str(e)}",
            "users_count": 0,
            "users": []
        }

@app.get("/edge/users/list/simplified")
async def get_all_users_simplified():
    """Get all users with simplified format (only id, username, roles) compatible with Java UserResource"""
    try:
        # Get all users first
        all_users_response = await get_all_users()
        
        if not all_users_response.get("success", False):
            return all_users_response
        
        users = all_users_response.get("users", [])
        
        # Transform to simplified format
        simplified_users = []
        for user in users:
            simplified_user = {
                "id": user.get("id"),
                "username": user.get("username"),
                "roles": user.get("roles", ["user"])
            }
            simplified_users.append(simplified_user)
        
        return {
            "success": True,
            "users_count": len(simplified_users),
            "users": simplified_users,
            "source": all_users_response.get("source", "unknown"),
            "message": f"Retrieved {len(simplified_users)} users in simplified format"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error getting simplified users: {str(e)}",
            "users_count": 0,
            "users": []
        }

@app.get("/edge/users/plate/{license_plate}")
async def get_user_by_license_plate(license_plate: str):
    """Get user by license plate from mock database"""
    try:
        user = get_user_by_plate(license_plate)
        if user:
            return UserResponse(
                id=user["id"],
                username=user["username"],
                roles=user.get("roles", ["user"])
            )
        else:
            raise HTTPException(status_code=404, detail=f"No user found for license plate: {license_plate}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user by plate: {str(e)}")

# ---------- BASIC ENDPOINTS ----------

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Park Up Edge Node API", "version": "1.0.0"}

@app.get("/hello/{name}")
async def say_hello(name: str):
    """Simple hello endpoint for testing"""
    return {"message": f"Hello {name}!"}
