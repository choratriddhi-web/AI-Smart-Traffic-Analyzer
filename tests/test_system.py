import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

import cv2
import numpy as np
from services.mongodb import get_db, check_db_connection, seed_initial_data_if_empty, get_collection
from services.camera_service import get_all_camera_details, CameraStreamManager
from services.yolo_service import YOLOVehicleDetector, VEHICLE_CLASS_MAP
from services.traffic_service import TrafficAnalyzerService
from services.signal_service import AISignalRecommendationEngine
from services.qlearning_service import QLearningTrafficAgent
from services.prediction_service import TrafficPredictionService
from services.incident_service import IncidentManagementService
from services.emergency_service import EmergencyVehicleService
from services.assistant_service import AITrafficAssistant
from services.sos_service import SmartSOSService
from config.views import haversine_distance

class SmartTrafficSystemTestSuite(unittest.TestCase):
    """
    Comprehensive Test Suite for AI Smart Traffic Analyzer.
    """

    @classmethod
    def setUpClass(cls):
        seed_initial_data_if_empty()

    def test_01_mongodb_connection(self):
        """Verify MongoDB connection and diagnostic status."""
        status = check_db_connection()
        self.assertIn(status["status"], ["connected", "ok"])
        self.assertIsNotNone(status.get("collections"))
        print("\n[PASS] Test 1: MongoDB connection and health check succeeded.")

    def test_02_default_users_seeded(self):
        """Verify Traffic Authority and Public Citizen accounts exist."""
        users_col = get_collection("users")
        officer = users_col.find_one({"username": "officer"})
        citizen = users_col.find_one({"username": "citizen"})

        self.assertIsNotNone(officer, "Traffic authority account must be seeded")
        self.assertEqual(officer["role"], "Traffic Authority")
        self.assertIsNotNone(citizen, "Public citizen account must be seeded")
        self.assertEqual(citizen["role"], "Public User")
        print("[PASS] Test 2: Two-portal authentication accounts (Traffic Authority & Public Citizen) verified.")

    def test_03_four_cameras_registry(self):
        """Verify all 4 CCTV cameras exist and have video files on disk."""
        cameras = get_all_camera_details()
        self.assertEqual(len(cameras), 4, "Must contain exactly 4 cameras (CAM-01 to CAM-04)")

        cam_ids = [c["camera_id"] for c in cameras]
        self.assertListEqual(cam_ids, ["CAM-01", "CAM-02", "CAM-03", "CAM-04"])

        for c in cameras:
            self.assertTrue(c["file_exists"], f"Video file for {c['camera_id']} ({c['video_file']}) must exist on disk")
        print("[PASS] Test 3: Four simulated CCTV cameras and video files verified.")

    def test_04_yolo_model_loading(self):
        """Verify YOLOv8 model initializes properly."""
        detector = YOLOVehicleDetector.get_detector()
        self.assertIsNotNone(detector.model, "YOLOv8 model must load weights successfully")
        self.assertIn("car", VEHICLE_CLASS_MAP.values())
        self.assertIn("motorcycle", VEHICLE_CLASS_MAP.values())
        self.assertIn("bus", VEHICLE_CLASS_MAP.values())
        self.assertIn("truck", VEHICLE_CLASS_MAP.values())
        print("[PASS] Test 4: YOLOv8 model loading and target classes verified.")

    def test_05_camera_frame_reading_and_inference(self):
        """Verify reading a real frame from CAM-01 and running YOLO detection."""
        cam_mgr = CameraStreamManager.get_manager("CAM-01")
        frame = cam_mgr.get_frame()
        self.assertIsNotNone(frame, "Should successfully read video frame from CAM-01")
        self.assertEqual(len(frame.shape), 3, "Frame must be a valid 3-channel image")

        detector = YOLOVehicleDetector.get_detector()
        detections = detector.detect_and_track(frame, confidence_threshold=0.25, track=False)
        self.assertIsInstance(detections, list)
        print(f"[PASS] Test 5: Real YOLO inference on CAM-01 frame succeeded ({len(detections)} vehicles detected).")

    def test_06_traffic_density_calculation(self):
        """Verify density categorization logic."""
        traffic_svc = TrafficAnalyzerService.get_service()
        low_cat, _ = traffic_svc.calculate_density(4)
        mod_cat, _ = traffic_svc.calculate_density(9)
        high_cat, _ = traffic_svc.calculate_density(16)
        vhigh_cat, _ = traffic_svc.calculate_density(28)

        self.assertEqual(low_cat, "LOW")
        self.assertEqual(mod_cat, "MODERATE")
        self.assertEqual(high_cat, "HIGH")
        self.assertEqual(vhigh_cat, "VERY HIGH")
        print("[PASS] Test 6: Traffic density classification verified.")

    def test_07_adaptive_signal_recommendation(self):
        """Verify AI signal timing calculations."""
        rec = AISignalRecommendationEngine.calculate_recommendation(
            camera_id="CAM-01",
            vehicle_count=18,
            max_queue=7,
            density_category="HIGH",
            wait_time_sec=40
        )
        self.assertIn("SIMULATED", rec["simulated_label"])
        self.assertGreaterEqual(rec["green_duration"], 15)
        self.assertLessEqual(rec["green_duration"], 90)
        self.assertIn("explanation", rec)
        print(f"[PASS] Test 7: AI Signal Recommendation calculated ({rec['green_duration']}s green duration).")

    def test_08_qlearning_simulation(self):
        """Verify Reinforcement Learning Q-learning comparative simulation."""
        agent = QLearningTrafficAgent()
        sim = agent.run_comparison_simulation(initial_queue=12, initial_density="HIGH", steps=15)
        self.assertIn("fixed_time", sim)
        self.assertIn("q_learning", sim)
        self.assertGreater(sim["improvements"]["waiting_time_reduction_percent"], 0)
        print(f"[PASS] Test 8: Q-Learning simulation verified ({sim['improvements']['waiting_time_reduction_percent']}% delay reduction).")

    def test_09_linear_regression_prediction(self):
        """Verify ML traffic prediction for +5m, +15m, +30m."""
        pred = TrafficPredictionService.predict_traffic("CAM-01")
        self.assertIn("5m", pred["predictions"])
        self.assertIn("15m", pred["predictions"])
        self.assertIn("30m", pred["predictions"])
        self.assertGreater(pred["predictions"]["5m"]["predicted_volume"], 0)
        print(f"[PASS] Test 9: ML Traffic volume prediction (+5m: {pred['predictions']['5m']['predicted_volume']} veh).")

    def test_10_ai_traffic_assistant_truthfulness(self):
        """Verify conversational assistant answers accurately from services."""
        ans1 = AITrafficAssistant.ask("What is the current traffic density?")
        self.assertIn("traffic_density", ans1["intent"])
        self.assertIn("density", ans1["answer"].lower())

        ans2 = AITrafficAssistant.ask("Which camera has maximum traffic?")
        self.assertIn("maximum_traffic", ans2["intent"])
        self.assertTrue(any(c in ans2["answer"] for c in ["CAM-01", "CAM-02", "CAM-03", "CAM-04"]))
        print("[PASS] Test 10: AI Traffic Assistant query resolution verified.")

    def test_11_smart_sos_ticket_lifecycle(self):
        """Verify citizen SOS ticket creation, retrieval, and authority resolution."""
        ticket = SmartSOSService.create_sos(
            user_id="test_user",
            name="Pooja Sharma",
            phone="+91 99887 76655",
            category="Medical Emergency",
            details="Ambulance needed near signal",
            lat=19.0760,
            lng=72.8777
        )
        self.assertEqual(ticket["status"], "Pending")

        SmartSOSService.update_status(ticket["id"], "Acknowledged", "Officer Verma")
        updated = SmartSOSService.get_request_by_id(ticket["id"])
        self.assertEqual(updated["status"], "Acknowledged")
        self.assertEqual(updated["acknowledged_by"], "Officer Verma")
        print("[PASS] Test 11: Smart SOS emergency ticket lifecycle verified.")

    def test_12_haversine_petrol_pump_distance(self):
        """Verify GPS distance calculation to nearest fuel station."""
        dist = haversine_distance(19.0760, 72.8777, 19.0755, 72.8785)
        self.assertGreater(dist, 0)
        self.assertLess(dist, 1.0) # Within 1 km
        print(f"[PASS] Test 12: Haversine distance verified ({dist} km).")

if __name__ == '__main__':
    unittest.main()
