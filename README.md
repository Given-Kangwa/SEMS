# Smart Energy Management System (SEMS)

SEMS is a prototype for monitoring energy use in a hostel room and a classroom. The Python simulator sends sample readings to a FastAPI backend, which stores them in PostgreSQL and exposes them for a Base44 frontend.

## Data flow

`simulator/simulate.py` → `POST /api/sensor-data` → PostgreSQL (`sensor_readings`) → Base44 reads `GET /api/rooms` and `GET /api/energy`.

The existing Streamlit dashboard has been removed. Base44 is the intended frontend; its project is hosted separately and is not included in this repository.

## Run locally

1. Create a virtual environment and install dependencies:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Create a PostgreSQL database, copy `.env.example` to `.env`, and enter the database settings.

3. Start the API from the project root:

   ```powershell
   python -m uvicorn backend.main:app --reload
   ```

   API docs are available at `http://127.0.0.1:8000/docs`. The API creates the `sensor_readings` table on startup.

4. In a second terminal, start the simulator:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   python -m simulator.simulate
   ```

   It posts sample readings for both rooms every two seconds. Set `SEMS_API_URL` to change the API address, or `SIMULATOR_INTERVAL_SECONDS` to change the interval.

## Base44 connection

Deploy the FastAPI service and PostgreSQL database to hosting that Base44 can reach over HTTPS. Configure `BASE44_ALLOWED_ORIGINS` on the API service as the exact Base44 app origin (comma-separated if there is more than one). Set `SEMS_API_URL` on the simulator to the deployed API base URL if the simulator runs elsewhere.

In Base44, call the API using the deployed base URL:

- `GET /api/rooms` — latest reading for each supported room; returns initial zero values until readings arrive.
- `GET /api/rooms/hostel_room` or `GET /api/rooms/classroom` — latest reading for one room.
- `GET /api/energy?limit=100` — recent historical readings (maximum 500); optional `room_id=hostel_room` or `room_id=classroom` filter.
- `POST /api/sensor-data` — submit a reading with `room_id`, `occupancy`, `people_count`, `mmwave_presence`, `light`, `fan`, `ac`, `voltage`, `current`, `power`, and `energy_kwh`.

The simulator is the current data producer. Avoid running it against production data unless sample data is intended. The API has no user authentication or appliance-control endpoint yet, so this prototype is for trusted testing rather than a public production deployment.
