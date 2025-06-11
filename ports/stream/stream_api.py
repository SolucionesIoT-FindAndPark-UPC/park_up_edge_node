from fastapi import APIRouter, Body
from adapters.stream.stream_camera import save_stream_url

router = APIRouter()

@router.post("/edge/stream")
def stream_input(stream_id: int = Body(...), url: str = Body(...)):
    result = save_stream_url(stream_id, url)
    return {"message": "Stream saved", "data": result}
