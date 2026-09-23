"""SQLAlchemy ORM models that map Python objects to PostgreSQL tables."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Float, Integer, String

from backend.database import Base


class SensorReading(Base):
    """One time-stamped sensor reading received for a SEMS location."""

    __tablename__ = "sensor_readings"
    __table_args__ = (
        CheckConstraint(
            "room_id IN ('hostel_room', 'classroom')",
            name="valid_sensor_reading_room_id",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    occupancy = Column(Boolean, nullable=False)
    people_count = Column(Integer, nullable=False)
    mmwave_presence = Column(Boolean, nullable=False)
    light = Column(Boolean, nullable=False)
    fan = Column(Boolean, nullable=False)
    ac = Column(Boolean, nullable=False)
    voltage = Column(Float, nullable=False)
    current = Column(Float, nullable=False)
    power = Column(Float, nullable=False)
    energy_kwh = Column(Float, nullable=False)
