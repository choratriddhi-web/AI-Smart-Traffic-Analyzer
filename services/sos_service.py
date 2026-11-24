import logging
from datetime import datetime
from bson import ObjectId
from services.mongodb import get_collection

logger = logging.getLogger(__name__)

class SmartSOSService:
    """
    Handles emergency SOS requests submitted by public citizens,
    coordinates with the Traffic Authority dispatch board,
    and updates resolution status.
    """

    @staticmethod
    def create_sos(user_id: str, name: str, phone: str, category: str, details: str, lat: float = None, lng: float = None, address: str = None):
        col = get_collection("sos_requests")
        count = col.count_documents({}) + 1
        ticket_no = f"SOS-{datetime.utcnow().strftime('%Y%m%d')}-{count:04d}"

        doc = {
            "ticket_number": ticket_no,
            "user_id": user_id,
            "user_name": name,
            "contact_phone": phone,
            "emergency_category": category,
            "details": details,
            "latitude": lat,
            "longitude": lng,
            "address": address or "GPS Geolocation Provided",
            "status": "Pending",  # Pending -> Acknowledged -> Resolved
            "created_at": datetime.utcnow(),
            "acknowledged_by": None,
            "acknowledged_at": None,
            "resolved_at": None,
            "resolution_notes": None,
            "is_alerted": False,
            "disclaimer": "PROJECT DEMONSTRATION – SOS DOES NOT CONTACT REAL EMERGENCY SERVICES."
        }
        res = col.insert_one(doc)
        doc["id"] = str(res.inserted_id)
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc

    @staticmethod
    def get_all_requests():
        col = get_collection("sos_requests")
        requests = list(col.find().sort("created_at", -1))
        for r in requests:
            r["id"] = str(r["_id"])
            if "_id" in r:
                r["_id"] = str(r["_id"])
        return requests

    @staticmethod
    def get_user_requests(user_id: str):
        col = get_collection("sos_requests")
        requests = list(col.find({"user_id": user_id}).sort("created_at", -1))
        for r in requests:
            r["id"] = str(r["_id"])
            if "_id" in r:
                r["_id"] = str(r["_id"])
        return requests

    @staticmethod
    def get_pending_alerts():
        """
        Retrieves active pending SOS requests formatted cleanly for JSON serialization.
        """
        col = get_collection("sos_requests")
        pending = list(col.find({"status": "Pending"}).sort("created_at", -1).limit(5))
        results = []
        for p in pending:
            created_str = p["created_at"].strftime("%H:%M:%S") if isinstance(p.get("created_at"), datetime) else str(p.get("created_at", ""))
            results.append({
                "id": str(p["_id"]),
                "ticket_number": p.get("ticket_number", ""),
                "user_name": p.get("user_name", "Citizen"),
                "contact_phone": p.get("contact_phone", ""),
                "emergency_category": p.get("emergency_category", "Emergency SOS"),
                "details": p.get("details", ""),
                "address": p.get("address", "GPS Coordinates Shared"),
                "latitude": p.get("latitude"),
                "longitude": p.get("longitude"),
                "created_at": created_str,
                "status": p.get("status", "Pending")
            })
        return results

    @staticmethod
    def get_request_by_id(mongo_id: str):
        col = get_collection("sos_requests")
        req = col.find_one({"_id": ObjectId(mongo_id)})
        if req:
            req["id"] = str(req["_id"])
            if "_id" in req:
                req["_id"] = str(req["_id"])
        return req

    @staticmethod
    def update_status(mongo_id: str, status: str, officer_name: str, notes: str = None):
        col = get_collection("sos_requests")
        update_doc = {"status": status, "updated_at": datetime.utcnow()}
        if status == "Acknowledged":
            update_doc["acknowledged_by"] = officer_name
            update_doc["acknowledged_at"] = datetime.utcnow()
        elif status == "Resolved":
            update_doc["resolved_at"] = datetime.utcnow()
            if notes:
                update_doc["resolution_notes"] = notes

        col.update_one({"_id": ObjectId(mongo_id)}, {"$set": update_doc})
