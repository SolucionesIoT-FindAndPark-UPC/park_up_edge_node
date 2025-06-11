# Simulamos una base temporal para monitoreo
monitoring_db = {}

def register_monitoring(site_id: str, metric: str, value: float):
    if site_id not in monitoring_db:
        monitoring_db[site_id] = []

    monitoring_entry = {
        "metric": metric,
        "value": value
    }

    monitoring_db[site_id].append(monitoring_entry)

    return {
        "siteId": site_id,
        "registered": monitoring_entry,
        "entries": len(monitoring_db[site_id])
    }
