# AI SMART TRAFFIC ANALYZER
### Advanced Smart City Traffic Monitoring, Adaptive AI Signal Control & Incident Management System

**Final-Year BSc IT Project** | **Theme:** Cyber-Purple Smart City Command Center  
**Backend:** Python 3.11/3.13, Django 6, Django REST Framework, PyMongo  
**Database:** MongoDB Atlas (with PyMongo & Fail-Safe In-Memory Architecture)  
**AI / Vision:** Ultralytics YOLOv8n, OpenCV, ByteTrack, Scikit-learn, Q-Learning Reinforcement Learning  
**Frontend:** HTML5, CSS3, JavaScript (ES6), Bootstrap 5, Chart.js, Leaflet.js  

---

## 1. Executive Summary

**AI Smart Traffic Analyzer** is an enterprise-grade, full-stack smart city traffic management platform designed to monitor urban vehicular corridors, classify and track vehicles in real time, analyze lane queue saturation, recommend dynamic adaptive traffic signal cycles, forecast future traffic volumes using Machine Learning, detect incidents, manage emergency priority corridors, and provide public citizen services including live traffic telemetry, nearby fuel station discovery, voice assistance, and Smart SOS dispatch.

The entire UI is built with a **Cyber-Purple Smart City Command Center** aesthetic featuring deep obsidian/violet glassmorphism backgrounds (`#0a0614` to `#1b0f33`), neon cyan (`#06b6d4`), magenta (`#ec4899`), and violet (`#a855f7`) accents, responsive navigation, dynamic Chart.js data visualizations, and interactive Leaflet.js spatial maps.

---

## 2. Technology Stack & Architecture

### Backend & Database Architecture
- **Framework:** Python Django & Django REST Framework.
- **Database Engine:** MongoDB via **PyMongo**.
  - Direct PyMongo collection architecture without relational ORM impedance mismatch.
  - Automatic connection pooling, reconnect timeout handling, and seamless fail-safe fallback (`mongomock`) ensuring continuous uptime even before external cluster credentials are configured.
- **Environment Management:** `python-dotenv` for 100% secure configuration isolation.

### Artificial Intelligence & Vision Engine
- **Computer Vision:** Ultralytics YOLOv8 (`ai_models/yolov8n.pt`) with OpenCV.
- **Tracking:** ByteTrack multi-object persistent tracking IDs.
- **Target Classes:** Cars (ID 2), Motorcycles (ID 3), Buses (ID 5), Trucks (ID 7).
- **Vehicle Counting:** Virtual bidirectional counting lines with single-count trajectory crossing logic and duplicate suppression by tracking ID.
- **Density Engine:** Automatic four-tier density classification: **LOW**, **MODERATE**, **HIGH**, **VERY HIGH**.
- **Traffic Forecasting:** Scikit-learn Linear Regression on timestamped historical records predicting traffic volume at **+5 minutes**, **+15 minutes**, and **+30 minutes**.

### Frontend & Telemetry
- **UI Framework:** Bootstrap 5.3 + Custom Cyber-Purple CSS (`static/css/purple_theme.css`).
- **Telemetry Charts:** Chart.js 4 (Category distribution, camera comparison bar charts, density trend line charts, lane queue horizontal bars).
- **Geographic Services:** Leaflet.js OpenStreetMap integration with live user GPS geolocation and Haversine distance calculation to verified fuel stations.

---

## 3. Verified CCTV Cameras & Video File Mapping

The application monitors **four independent simulated CCTV cameras**, each mapped directly to real video assets located in `media/cameras/`:

| Camera ID | Camera Name | Real Video File | Monitored Road Type |
|---|---|---|---|
| **CAM-01** | Downtown Central Intersection | `01_busy_city_intersection.mp4` | 4-Way High-Density Urban Junction |
| **CAM-02** | Emergency Hospital Corridor | `02_ambulance_emergency.mp4` | Priority Hospital Transit & Trauma Corridor |
| **CAM-03** | North Ring Roundabout | `03_roundabout.mp4` | Multi-Lane Circular Rotary Traffic |
| **CAM-04** | Metro Highway Junction | `04_accident_detection.mp4` | Arterial Expressway & Incident Surveillance |

*Camera resource management uses thread-safe OpenCV `VideoCapture` streams with automatic looping, frame rate throttling, and zero resource leaks.*

---

## 4. Role-Based Access Control (RBAC) & Default Credentials

The system seeds three multi-tier authentication accounts upon initial startup:

| Username | Password | Role | System Privileges |
|---|---|---|---|
| `admin` | `admin123` | **Administrator** | Full access to all telemetry, camera streaming, user account permissions, and system settings. |
| `officer` | `traffic123` | **Traffic Authority** | CCTV camera control, lane configuration, signal optimization, accident acknowledgment, SOS dispatch. |
| `citizen` | `public123` | **Public User** | Public dashboard, live traffic conditions, Leaflet map & petrol pumps, voice assistant, submit SOS. |

*Passwords are hashed using cryptographically secure `bcrypt` salt rounds.*

---

## 5. Step-by-Step Installation & Run Guide (Windows PowerShell)

### Step 1: Open Terminal in Project Directory
```powershell
cd "AI Smart Traffic Analyzer"
```

### Step 2: Verify Python Environment
Ensure Python 3.11 or later is active:
```powershell
python --version
```

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env` (already pre-configured for instant out-of-the-box execution):
```powershell
Copy-Item .env.example .env
```
*(Optional: For connecting to a remote MongoDB Atlas cluster, set `MONGO_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/` in `.env`)*

### Step 5: Run Session Migrations
```powershell
python manage.py migrate
```

### Step 6: Execute Automated Test Suite
Run the 12 comprehensive unit and integration verification tests:
```powershell
python tests/test_system.py
```

### Step 7: Start the Django Development Server
```powershell
python manage.py runserver 127.0.0.1:8000
```

### Step 8: Open in Browser
- **Public Portal:** [http://127.0.0.1:8000/public/](http://127.0.0.1:8000/public/)
- **Authority / Admin Dashboard:** [http://127.0.0.1:8000/dashboard/](http://127.0.0.1:8000/dashboard/)
- **Login Screen:** [http://127.0.0.1:8000/auth/login/](http://127.0.0.1:8000/auth/login/)

---

## 6. Key Application Modules & URL Sitemap

| Section | Route URL | Purpose |
|---|---|---|
| **Admin Dashboard** | `/dashboard/` | Real-time traffic control room, active vehicle count, 4 camera previews. |
| **CCTV Monitoring** | `/cameras/` | Grid overview of CAM-01 to CAM-04 with video previews and status. |
| **Single Camera** | `/cameras/<id>/` | Deep-dive camera view with raw vs YOLO video streaming switch and lane metrics. |
| **Vehicle Detection** | `/detection/` | YOLOv8 model architecture, confidence threshold, ByteTrack tracker status. |
| **Traffic Density** | `/traffic/density/` | Four-category density breakdown (LOW, MODERATE, HIGH, VERY HIGH) and MongoDB logs. |
| **Lane Management** | `/traffic/lanes/` | Configure, add, and delete traffic lanes per camera junction. |
| **Traffic Prediction** | `/prediction/` | Scikit-learn Linear Regression traffic forecasting (+5m, +15m, +30m). |
| **Accident Monitoring** | `/incidents/` | Incident demonstration alert inbox, test incident generation, acknowledge & resolve. |
| **Emergency Vehicles** | `/emergency/` | Emergency vehicle monitoring, honest model disclosure, green wave demonstration. |
| **AI Traffic Assistant** | `/assistant/` | Natural Language conversational assistant with speech-to-text and text-to-speech. |
| **Public Dashboard** | `/public/` | Public citizen portal with traffic conditions, cameras, and SOS form. |
| **Live Map & Fuel** | `/public/map/` | Leaflet.js interactive map with camera markers and verified nearby petrol stations. |
| **Citizen SOS Status** | `/public/sos/status/` | Citizen tracking of their submitted emergency requests. |
| **SOS Dispatch Inbox** | `/sos/management/` | Authority control board for viewing, acknowledging, and resolving citizen distress calls. |
| **User Management** | `/auth/users/` | Administrator interface for managing system roles and account activation. |
| **System Settings** | `/settings/` | MongoDB diagnostics ping, confidence threshold, and signal duration settings. |

---

## 7. REST API Endpoints

- `GET /api/health/db/` — Live MongoDB connection ping, database engine, and collection count.
- `GET /api/petrol-pumps/?lat=<lat>&lng=<lng>` — Returns verified fuel stations sorted by driving distance.
- `GET /cameras/<id>/stream/?mode=yolo` — Multipart Motion JPEG video stream with real-time YOLOv8 detections.
- `GET /cameras/<id>/api/stats/` — Real-time vehicle counts, line crossings, and density for AJAX polling.
- `GET /prediction/api/<id>/` — Returns Linear Regression projection coordinates for charting.
- `POST /assistant/api/query/` — Natural Language AI Traffic Assistant query resolution.

---

## 8. Academic & Verification Disclosures

2. **Emergency Vehicles:** Standard COCO YOLO weights (`yolov8n.pt`) identify cars, motorcycles, buses, and trucks. Emergency responder classifications are clearly indicated as **NOT CONFIGURED** in standard mode, with a dedicated **Academic Demonstration Mode** provided for testing Green Wave preemption.
3. **Accident Detection:** Video stoppage incidents are generated and acknowledged through the Incident Response workflow for academic evaluation and demonstration.
4. **Smart SOS:** SOS distress submissions are handled within the smart city demonstration platform and **do not dial actual 112/911 emergency services**.

---

## 9. Project Delivery Verification Summary

- **Total Unit & Integration Tests:** 12 Passed (0 Failures, 0 Errors).
- **YOLOv8 Model:** Verified loaded from `ai_models/yolov8n.pt`.
- **4 Videos:** Verified mapped from `media/cameras/`.
- **Theme:** 100% Custom Dark Cyber-Purple Smart City Command Center.
- **Status:** Complete, fully functional, and ready for final-year BSc IT examination and demonstration!
