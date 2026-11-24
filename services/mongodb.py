import os
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_mongo_client = None
_db_instance = None
_is_mock = False

MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "ai_smart_traffic_analyzer")
MONGO_TIMEOUT_MS = int(os.getenv("MONGO_TIMEOUT_MS", "3000"))

def get_db():
    """
    Returns the active MongoDB database instance using PyMongo.
    Gracefully falls back to mongomock if local/remote MongoDB is unreachable,
    ensuring zero-downtime execution and continuous availability.
    """
    global _mongo_client, _db_instance, _is_mock

    if _db_instance is not None:
        return _db_instance

    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

        logger.info(f"Connecting to MongoDB at {MONGO_URI} (db: {MONGO_DB_NAME})")
        client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=MONGO_TIMEOUT_MS,
            connectTimeoutMS=MONGO_TIMEOUT_MS,
        )
        # Test connection with ping
        client.admin.command('ping')
        _mongo_client = client
        _db_instance = client[MONGO_DB_NAME]
        _is_mock = False
        logger.info("Successfully connected to live MongoDB server.")
        return _db_instance
    except Exception as e:
        logger.warning(
            f"Live MongoDB connection failed ({e}). Falling back to in-memory mongomock for fail-safe execution."
        )
        try:
            import mongomock
            client = mongomock.MongoClient()
            _mongo_client = client
            _db_instance = client[MONGO_DB_NAME]
            _is_mock = True
            logger.info("Mongomock fail-safe in-memory database initialized.")
            return _db_instance
        except Exception as mock_err:
            logger.error(f"Failed to initialize mongomock: {mock_err}")
            raise

def is_mock_db():
    """Returns True if running on mongomock fallback, False if live MongoDB."""
    global _is_mock
    if _db_instance is None:
        get_db()
    return _is_mock

def get_collection(collection_name: str):
    """Retrieves a specific PyMongo collection."""
    db = get_db()
    return db[collection_name]

def check_db_connection():
    """
    Diagnostic function to check database connectivity, ping, and collection count.
    """
    db = get_db()
    status = {
        "status": "connected",
        "database_name": MONGO_DB_NAME,
        "is_fallback_mock": is_mock_db(),
        "uri_configured": bool(MONGO_URI),
        "timestamp": datetime.utcnow().isoformat(),
        "collections": []
    }
    try:
        if not is_mock_db() and _mongo_client:
            _mongo_client.admin.command('ping')
            status["ping"] = "pong"
            status["server_info"] = "Live MongoDB Atlas/Cluster"
        else:
            status["ping"] = "in-memory"
            status["server_info"] = "Fail-Safe In-Memory Mock Database"

        status["collections"] = list(db.list_collection_names())
        return status
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "is_fallback_mock": is_mock_db()
        }

def seed_initial_data_if_empty():
    """
    Seeds initial system data (admin user, camera records, lanes, settings)
    if the collections are empty.
    """
    import bcrypt
    db = get_db()

    # 1. Seed Default Users if empty (Traffic Authority & Public Citizen)
    users_col = db["users"]
    if users_col.count_documents({}) == 0:
        salt = bcrypt.gensalt()

        # Traffic Authority User
        auth_pw = bcrypt.hashpw("traffic123".encode('utf-8'), salt).decode('utf-8')
        auth_doc = {
            "username": "officer",
            "email": "officer@traffic.gov",
            "password": auth_pw,
            "full_name": "Traffic Control Officer Sharma",
            "role": "Traffic Authority",
            "phone": "+91 98765 12345",
            "created_at": datetime.utcnow(),
            "is_active": True
        }
        users_col.insert_one(auth_doc)

        # Public Citizen User
        pub_pw = bcrypt.hashpw("public123".encode('utf-8'), salt).decode('utf-8')
        pub_doc = {
            "username": "citizen",
            "email": "citizen@gmail.com",
            "password": pub_pw,
            "full_name": "Rahul Verma",
            "role": "Public User",
            "phone": "+91 98111 22334",
            "created_at": datetime.utcnow(),
            "is_active": True
        }
        users_col.insert_one(pub_doc)
        logger.info("Default seed users created: officer (Traffic Authority), citizen (Public User)")

    # 2. Seed Default Camera Records if empty
    cameras_col = db["cameras"]
    if cameras_col.count_documents({}) == 0:
        default_cameras = [
            {
                "camera_id": "CAM-01",
                "name": "Downtown Central Intersection",
                "location": "MG Road & Grand Avenue Junction",
                "latitude": 19.0760,
                "longitude": 72.8777,
                "video_file": "01_busy_city_intersection.mp4",
                "status": "Active",
                "fps": 25,
                "resolution": "1280x720",
                "created_at": datetime.utcnow(),
                "description": "High-density four-way urban junction with heavy passenger vehicle traffic."
            },
            {
                "camera_id": "CAM-02",
                "name": "Emergency Hospital Corridor",
                "location": "City General Hospital - Trauma Way",
                "latitude": 19.0825,
                "longitude": 72.8850,
                "video_file": "02_ambulance_emergency.mp4",
                "status": "Active",
                "fps": 25,
                "resolution": "1280x720",
                "created_at": datetime.utcnow(),
                "description": "Priority emergency vehicle corridor monitoring ambulance and hospital transit."
            },
            {
                "camera_id": "CAM-03",
                "name": "North Ring Roundabout",
                "location": "North Ring Road Circle & Expressway Bypass",
                "latitude": 19.0890,
                "longitude": 72.8680,
                "video_file": "03_roundabout.mp4",
                "status": "Active",
                "fps": 25,
                "resolution": "1280x720",
                "created_at": datetime.utcnow(),
                "description": "Rotary traffic circulation monitoring merging lanes and weaving sections."
            },
            {
                "camera_id": "CAM-04",
                "name": "Metro Highway Junction",
                "location": "Western Express Highway Flyover Pier 14",
                "latitude": 19.0650,
                "longitude": 72.8550,
                "video_file": "04_accident_detection.mp4",
                "status": "Active",
                "fps": 25,
                "resolution": "1280x720",
                "created_at": datetime.utcnow(),
                "description": "Fast-moving arterial highway sector with incident monitoring capabilities."
            }
        ]
        cameras_col.insert_many(default_cameras)
        logger.info("Default 4 camera records registered in database.")

    # 3. Seed Default Lanes if empty
    lanes_col = db["lanes"]
    if lanes_col.count_documents({}) == 0:
        default_lanes = [
            {"camera_id": "CAM-01", "lane_number": 1, "name": "Lane 1 - Left Turn", "direction": "Northbound", "capacity": 15},
            {"camera_id": "CAM-01", "lane_number": 2, "name": "Lane 2 - Straight", "direction": "Northbound", "capacity": 20},
            {"camera_id": "CAM-01", "lane_number": 3, "name": "Lane 3 - Right Turn", "direction": "Northbound", "capacity": 15},
            {"camera_id": "CAM-02", "lane_number": 1, "name": "Lane 1 - Emergency Lane", "direction": "Eastbound", "capacity": 10},
            {"camera_id": "CAM-02", "lane_number": 2, "name": "Lane 2 - Regular Transit", "direction": "Eastbound", "capacity": 18},
            {"camera_id": "CAM-03", "lane_number": 1, "name": "Lane 1 - Inner Ring", "direction": "Circulatory", "capacity": 16},
            {"camera_id": "CAM-03", "lane_number": 2, "name": "Lane 2 - Outer Ring", "direction": "Circulatory", "capacity": 16},
            {"camera_id": "CAM-04", "lane_number": 1, "name": "Lane 1 - Fast Lane", "direction": "Southbound", "capacity": 22},
            {"camera_id": "CAM-04", "lane_number": 2, "name": "Lane 2 - Middle Lane", "direction": "Southbound", "capacity": 22},
            {"camera_id": "CAM-04", "lane_number": 3, "name": "Lane 3 - Service Ramp", "direction": "Southbound", "capacity": 14},
        ]
        lanes_col.insert_many(default_lanes)
        logger.info("Default lane configurations seeded.")

    # 4. Seed System Settings if empty
    settings_col = db["system_settings"]
    if settings_col.count_documents({}) == 0:
        settings_doc = {
            "app_name": "AI Smart Traffic Analyzer",
            "version": "2.0.0",
            "theme": "purple_command_center",
            "confidence_threshold": 0.35,
            "density_thresholds": {
                "low": 5,
                "moderate": 12,
                "high": 22
            },
            "signal_timings": {
                "min_green": 15,
                "max_green": 90,
                "yellow": 4,
                "all_red": 2
            },
            "emergency_priority_enabled": True,
            "qlearning_active": True,
            "updated_at": datetime.utcnow()
        }
        settings_col.insert_one(settings_doc)
        logger.info("System settings initialized.")
