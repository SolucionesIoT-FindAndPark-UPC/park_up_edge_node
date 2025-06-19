import datetime

# Simulamos una "base de datos" temporal en memoria
parking_db = {}

def update_parking_status(site_id: str, occupied: bool):
    if site_id not in parking_db:
        parking_db[site_id] = {}

    parking_db[site_id]["occupied"] = occupied
    parking_db[site_id]["last_updated"] = datetime.datetime.now().isoformat()

    return {
        "siteId": site_id,
        "occupied": occupied,
        "timestamp": parking_db[site_id]["last_updated"]
    }
