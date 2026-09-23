"""Pydantic schemas used to validate API input and format API responses."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# Limiting this type keeps both API requests and path parameters to SEMS rooms.
RoomID = Literal["hostel_room", "classroom"]


class SensorDataInput(BaseModel):
    """Validated sensor data sent by a future ESP32 device."""

    room_id: RoomID
    occupancy: bool
    people_count: int = Field(ge=0)
    mmwave_presence: bool
    light: bool
    fan: bool
    ac: bool
    voltage: float = Field(ge=0)
    current: float = Field(ge=0)
    power: float = Field(ge=0)
    energy_kwh: float = Field(ge=0)


class RoomStatus(SensorDataInput):
    """The latest reading for a room, including its server timestamp."""

    timestamp: datetime


class SensorReadingResponse(RoomStatus):
    """A stored reading, including its PostgreSQL primary key."""

    model_config = ConfigDict(from_attributes=True)

    id: int


class EnergyReading(BaseModel):
    """Compact reading format intended for future dashboard charts."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    room_id: RoomID
    timestamp: datetime
    power: float
    energy_kwh: float


class SystemStatus(BaseModel):
    """Basic response returned by the root endpoint."""

    system_name: str
    backend_status: str
