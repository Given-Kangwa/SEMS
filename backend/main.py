"""FastAPI endpoints for the PostgreSQL-backed SEMS prototype."""

from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import Base, engine, get_db
from backend.models import SensorReading
from backend.schemas import EnergyReading, RoomID, RoomStatus, SensorDataInput, SensorReadingResponse, SystemStatus

app = FastAPI(
    title="SEMS API",
    description="Backend API for the Smart Energy Management System prototype.",
    version="0.1.0",
)


def default_room_status(room_id: RoomID) -> RoomStatus:
    """Create the safe, empty initial status used before any sensor data arrives."""

    return RoomStatus(
        room_id=room_id,
        occupancy=False,
        people_count=0,
        mmwave_presence=False,
        light=False,
        fan=False,
        ac=False,
        voltage=0.0,
        current=0.0,
        power=0.0,
        energy_kwh=0.0,
        timestamp=datetime.now(timezone.utc),
    )


@app.on_event("startup")
def create_database_tables() -> None:
    """Create sensor_readings when the backend starts for the first time."""

    Base.metadata.create_all(bind=engine)


@app.get("/", response_model=SystemStatus)
def get_system_status() -> SystemStatus:
    """Confirm that the SEMS backend is running."""

    return SystemStatus(system_name="Smart Energy Management System (SEMS)", backend_status="online")


@app.get("/api/rooms", response_model=list[RoomStatus])
def get_all_rooms(db: Session = Depends(get_db)) -> list[RoomStatus]:
    """Return each room's newest PostgreSQL reading, or safe initial data."""

    latest_rooms: list[RoomStatus] = []
    for room_id in ("hostel_room", "classroom"):
        reading = db.scalar(
            select(SensorReading)
            .where(SensorReading.room_id == room_id)
            .order_by(SensorReading.timestamp.desc(), SensorReading.id.desc())
            .limit(1)
        )
        if reading is None:
            latest_rooms.append(default_room_status(room_id))
        else:
            latest_rooms.append(RoomStatus.model_validate(reading, from_attributes=True))
    return latest_rooms


@app.get("/api/rooms/{room_id}", response_model=RoomStatus)
def get_room(room_id: RoomID, db: Session = Depends(get_db)) -> RoomStatus:
    """Return the latest PostgreSQL reading for one supported location."""

    reading = db.scalar(
        select(SensorReading)
        .where(SensorReading.room_id == room_id)
        .order_by(SensorReading.timestamp.desc(), SensorReading.id.desc())
        .limit(1)
    )
    if reading is None:
        return default_room_status(room_id)
    return RoomStatus.model_validate(reading, from_attributes=True)


@app.post("/api/sensor-data", response_model=RoomStatus, status_code=201)
def receive_sensor_data(
    sensor_data: SensorDataInput,
    db: Session = Depends(get_db),
) -> SensorReadingResponse:
    """Save a new reading to PostgreSQL and return the newly stored row."""

    reading = SensorReading(
        **sensor_data.model_dump(),
        timestamp=datetime.now(timezone.utc),
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return SensorReadingResponse.model_validate(reading, from_attributes=True)


@app.get("/api/energy", response_model=list[EnergyReading])
def get_energy_readings(
    room_id: RoomID | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[EnergyReading]:
    """Return recent stored energy readings for a future dashboard chart."""

    query = select(SensorReading).order_by(SensorReading.timestamp.desc(), SensorReading.id.desc()).limit(limit)
    if room_id is not None:
        query = query.where(SensorReading.room_id == room_id)
    readings = db.scalars(query).all()
    return [EnergyReading.model_validate(reading, from_attributes=True) for reading in readings]
