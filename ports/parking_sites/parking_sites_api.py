from fastapi import APIRouter, Body
from adapters.parking_sites.parking_state_updater import update_parking_status

router = APIRouter()

@router.post("/edge/parking/sites")
def parking_site_status(parking_id: int = Body(...), has_car: bool = Body(...)):
    result = update_parking_status(parking_id, has_car)
    return {"message": "Parking site updated", "data": result}
