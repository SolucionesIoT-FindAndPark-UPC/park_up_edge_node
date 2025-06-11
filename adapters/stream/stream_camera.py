# Base de datos temporal para cámaras
stream_db = {}

def save_stream_url(camera_id: str, stream_url: str):
    stream_db[camera_id] = {
        "url": stream_url
    }

    return {
        "cameraId": camera_id,
        "streamUrl": stream_url,
        "status": "saved"
    }
