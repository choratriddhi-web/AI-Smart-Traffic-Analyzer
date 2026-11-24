import logging
from datetime import datetime
from bson import ObjectId
from services.mongodb import get_collection

logger = logging.getLogger(__name__)

class IncidentManagementService:
    """
    Manages accident detection demonstration, incident alerting,
    authority acknowledgment, and resolution workflows.
    """

    @staticmethod
    def get_all_incidents():
        inc_col = get_collection("incidents")
        incidents = list(inc_col.find().sort("timestamp", -1))
        for inc in incidents:
            inc["id"] = str(inc["_id"])
        return incidents

    @staticmethod
    def get_active_count():
        inc_col = get_collection("incidents")
        return inc_col.count_documents({"status": {"$in": ["Active", "Acknowledged"]}})

    @staticmethod
    def create_incident(camera_id: str, category: str, location: str, description: str, method: str = "Demonstration Mode"):
        inc_col = get_collection("incidents")
        count = inc_col.count_documents({}) + 1
        incident_id = f"INC-{datetime.utcnow().year}-{count:03d}"

        doc = {
            "incident_id": incident_id,
            "camera_id": camera_id,
            "category": category,
            "location": location,
            "description": description,
            "detection_method": method,
            "status": "Active",   # Active -> Acknowledged -> Resolved
            "timestamp": datetime.utcnow(),
            "acknowledged_by": None,
            "acknowledged_at": None,
            "resolved_at": None,
            "resolution_notes": None,
            "is_demonstration": True
        }
        res = inc_col.insert_one(doc)
        doc["id"] = str(res.inserted_id)
        return doc

    @staticmethod
    def acknowledge_incident(mongo_id: str, officer_name: str):
        inc_col = get_collection("incidents")
        inc_col.update_one(
            {"_id": ObjectId(mongo_id)},
            {"$set": {
                "status": "Acknowledged",
                "acknowledged_by": officer_name,
                "acknowledged_at": datetime.utcnow()
            }}
        )

    @staticmethod
    def resolve_incident(mongo_id: str, notes: str):
        inc_col = get_collection("incidents")
        inc_col.update_one(
            {"_id": ObjectId(mongo_id)},
            {"$set": {
                "status": "Resolved",
                "resolved_at": datetime.utcnow(),
                "resolution_notes": notes
            }}
        )

    @staticmethod
    def seed_demo_incident_if_empty():
        inc_col = get_collection("incidents")
        if inc_col.count_documents({}) == 0:
            IncidentManagementService.create_incident(
                camera_id="CAM-04",
                category="Vehicle Collision / Stoppage",
                location="Western Express Highway Flyover Pier 14",
                description="Simulated multi-vehicle collision detected in lane 2. Traffic decelerating rapidly.",
                method="Demonstration Engine (Simulation)"
            )
