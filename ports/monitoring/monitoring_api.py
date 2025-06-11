from fastapi import APIRouter, Body
from adapters.monitoring.monitoring_analytics import register_monitoring

router = APIRouter()

@router.post("/edge/monitoring")
def monitoring(monitoring_id: int = Body(...), time: float = Body(...)):
    result = register_monitoring(monitoring_id, time)
    return {"message": "Monitoring updated", "data": result}
