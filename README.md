# Smart Energy Management System (SEMS)

**Your Space. Your Energy. Your Security.**

SEMS (Smart Energy Management System) is an IoT-based prototype designed to monitor electricity consumption, detect room occupancy and support intelligent appliance management.

The project currently targets two environments at the Indian Institute of Technology Madras Zanzibar:

- One hostel room
- One classroom

The software prototype uses simulated sensor readings to demonstrate the communication between the data simulator, FastAPI backend, PostgreSQL database and Base44 frontend. Physical hardware integration is planned for the next development stage.

---

## System Architecture

The intended system architecture connects occupancy sensors and an energy meter to a central microcontroller, which communicates with the backend and website.

### Data Flow

**Current software prototype:**

```text
Python Simulator
       |
       v
POST /api/sensor-data
       |
       v
FastAPI Backend
       |
       v
PostgreSQL Database
       |
       v
Base44 Frontend
       |
       v
SEMS Dashboard
```

**Planned hardware architecture:**

```text
mmWave Occupancy Sensors
          +
PZEM-004T Energy Meter
          |
          v
     ESP32 Controller
          |
        Wi-Fi
          |
          v
    FastAPI Backend
          |
          v
  PostgreSQL Database
          |
          v
    SEMS Website
```

The ESP32 acts as the central microcontroller. It collects readings from the separate sensors and energy meter and transmits the information to the backend.

The proposed hardware system also includes relays/contactors, suitable power supplies, wiring and electrical protection devices for appliance management.

---

## Project Features

### 1. Room Monitoring
- Monitor occupancy status.
- Support monitoring of the hostel room and classroom.
- Display room-related information through the dashboard.

### 2. Energy Monitoring
- Display electricity readings.
- Visualize energy consumption.
- Retrieve historical readings.
- Support room-level energy comparisons.

### 3. Appliance Management
- Provide interfaces for managing lights, fans and air conditioners.
- Support the planned communication between the website, ESP32 and electrical control hardware.

*Physical appliance switching has not yet been validated.*

### 4. Occupancy-Based Security
- Includes a manually controlled Away Mode.
- Generates a security event when occupancy is detected while Away Mode is active.
- Supports browser-based notifications.

*Automatic phone geofencing and mobile push notifications are planned improvements.*

### 5. Separate User and Administrator Portals
- Administrator portal for overall system monitoring and management.
- User portal for room-specific monitoring and available controls.

---

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Simulator and backend development |
| FastAPI | Backend API and communication |
| PostgreSQL | Database management |
| React | Frontend development |
| TanStack Router | Frontend navigation |
| Base44 | Website development environment |
| ESP32 | Planned hardware communication and data collection |
| mmWave Sensors | Planned occupancy detection |
| PZEM-004T V3.0 | Planned electricity measurement |
| Relays and Contactors | Planned appliance control |
| Plotly | Data visualization |

---

## Repository Structure

```text
SEMS/
│
├── backend/
│   └── main.py
│
├── simulator/
│   └── simulate.py
│
├── requirements.txt
├── render.yaml
├── .env.example
├── .gitignore
└── README.md
```

The Base44 frontend is hosted separately and is not included in this repository.

The previous Streamlit dashboard has been removed. Base44 is the intended frontend for the project.

---

## Getting Started

### Prerequisites

Before running the project, make sure you have:

- Python 3.10 or later
- PostgreSQL
- Git
- Visual Studio Code or another code editor

### 1. Clone the Repository

```bash
git clone https://github.com/Given-Kangwa/SEMS.git
cd SEMS
```

### 2. Create a Virtual Environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Database

Create a PostgreSQL database.

Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

Open `.env` and enter the appropriate database connection settings.

### 5. Start the FastAPI Backend

From the project root:

```bash
python -m uvicorn backend.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

The API creates the `sensor_readings` table on startup.

### 6. Start the Simulator

Open a second terminal and activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Run the simulator:

```bash
python -m simulator.simulate
```

The simulator sends sample readings for both the hostel room and classroom every two seconds.

To change the simulator configuration, use:

| Variable | Purpose |
|---|---|
| `SEMS_API_URL` | Changes the API address |
| `SIMULATOR_INTERVAL_SECONDS` | Changes the interval between readings |

---

## API Endpoints

The FastAPI backend exposes the following endpoints:

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API root |
| GET | `/api/rooms` | Retrieves the latest reading for each supported room |
| GET | `/api/rooms/hostel_room` | Retrieves the latest hostel-room reading |
| GET | `/api/rooms/classroom` | Retrieves the latest classroom reading |
| GET | `/api/energy?limit=100` | Retrieves recent historical energy readings |
| POST | `/api/sensor-data` | Submits a sensor reading |

### Sensor Data Submission

The `/api/sensor-data` endpoint accepts the following fields:

```json
{
  "room_id": "hostel_room",
  "occupancy": true,
  "people_count": 1,
  "mmwave_presence": true,
  "light": true,
  "fan": false,
  "ac": false,
  "voltage": 230.0,
  "current": 1.5,
  "power": 345.0,
  "energy_kwh": 1.25
}
```

The values above are illustrative sample data, not actual hardware measurements.

The historical energy endpoint supports a maximum of 500 readings and optional room filtering:

```text
/api/energy?limit=100&room_id=hostel_room
```

Supported room IDs:

- `hostel_room`
- `classroom`

---

## Connecting the Base44 Frontend

The Base44 application communicates with the FastAPI backend through its deployed API URL.

For the frontend to access the backend:

1. Deploy the FastAPI service.
2. Deploy the PostgreSQL database.
3. Configure the backend to allow requests from the exact Base44 application origin.
4. Configure the Base44 frontend to use the deployed API base URL.

Set the following environment variable on the API service:

```env
BASE44_ALLOWED_ORIGINS=https://your-app.base44.app
```

If multiple frontend origins are required, separate them with commas.

The simulator can also be configured to send readings to the deployed backend by setting:

```env
SEMS_API_URL=https://your-api.onrender.com
```

Use the actual deployed API address in place of the example.

---

## Deployment on Render

The repository includes a `render.yaml` configuration for deploying the API service and PostgreSQL database through Render.

### Deployment Steps

1. Push the repository to GitHub.
2. Sign in to [Render](https://render.com/).
3. Select **New → Blueprint**.
4. Connect the SEMS GitHub repository.
5. Configure `BASE44_ALLOWED_ORIGINS` with the exact Base44 application origin.
6. Complete the deployment.
7. Open the deployed API URL followed by `/docs` to verify that the API is accessible.

**Important deployment considerations:**

- Render's free web services may sleep when idle.
- Render's free PostgreSQL database expires 30 days after creation.
- Upgrade the database or move it to another hosting service before expiry if long-term data storage is required.

See the [Render Free Instance Limits](https://render.com/docs/free) for details.

---

## Current Development Status

| Component | Status |
|---|---|
| FastAPI backend | Developed |
| PostgreSQL integration | Developed |
| Python data simulator | Developed |
| Base44 frontend | Developed and preview-tested |
| Administrator and user portals | Developed |
| Energy monitoring interfaces | Developed |
| Room monitoring interfaces | Developed |
| Away Mode security prototype | Developed |
| mmWave hardware integration | Pending |
| PZEM-004T hardware integration | Pending |
| ESP32 integration | Pending |
| Physical appliance control | Pending |
| Live sensor-data validation | Pending |
| Mobile geofencing and push notifications | Planned |

The current prototype uses simulated readings. Physical hardware integration and validation remain part of the next development stage.

---

## Known Limitations

- The simulator is currently the data producer; physical sensors are not yet connected.
- The API currently has no user authentication.
- A physical appliance-control endpoint has not yet been implemented.
- Appliance-control interfaces do not establish that physical appliances have switched.
- Browser notifications depend on browser permission and the dashboard being open.
- Automatic phone geofencing and background push notifications are not yet available.
- The current deployment configuration is intended for prototype testing rather than public production use.

**Security note:** Do not expose the current unauthenticated API publicly for sensitive or production use. Authentication, authorization and appropriate deployment security must be implemented before production deployment.

---

## Future Development

The next development stage will focus on:

1. Integrating the ESP32 microcontroller.
2. Connecting the mmWave occupancy sensors.
3. Integrating the PZEM-004T energy meter.
4. Implementing and safely testing relay/contactor-based appliance control.
5. Replacing simulated readings with live hardware data.
6. Improving security alerts through mobile geofencing and push notifications.
7. Testing the system in the selected hostel room and classroom.
8. Evaluating energy consumption using real baseline and post-implementation data.

---

## Project Information

**Project:** Smart Energy Management System (SEMS)  
**Institution:** Indian Institute of Technology Madras Zanzibar  
**GitHub Repository:** [Given-Kangwa/SEMS](https://github.com/Given-Kangwa/SEMS)  
**Frontend:** Base44  
**Backend:** FastAPI  
**Database:** PostgreSQL  

**SEMS – Your Space. Your Energy. Your Security.**