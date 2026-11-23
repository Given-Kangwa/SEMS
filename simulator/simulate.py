"""Stateful software simulator for the future ESP32-based SEMS prototype."""

import random
import os
import time
from dataclasses import dataclass, field

import requests


API_BASE_URL = os.getenv("SEMS_API_URL", "http://127.0.0.1:8000").rstrip("/")
API_URL = f"{API_BASE_URL}/api/sensor-data"
SEND_INTERVAL_SECONDS = max(1, int(os.getenv("SIMULATOR_INTERVAL_SECONDS", "2")))


@dataclass
class RoomSimulator:
    """Keep one room's scenario, appliance states, and accumulated energy."""

    room_id: str
    display_name: str
    energy_kwh: float = 0.0
    occupancy: bool = False
    people_count: int = 0
    light: bool = False
    fan: bool = False
    ac: bool = False
    base_power_w: float = 0.0
    readings_left_in_scenario: int = 0
    _last_power_w: float = field(default=0.0, init=False)

    def choose_new_scenario(self) -> None:
        """Choose a realistic state that remains active for several readings."""

        if self.room_id == "hostel_room":
            # Hostel use is commonly one resident, with occasional two-person visits.
            scenario = random.choices(
                ["vacant", "one_person", "two_people"], weights=[35, 55, 10], k=1
            )[0]
            self.people_count = {"vacant": 0, "one_person": 1, "two_people": 2}[scenario]
        else:
            # Classrooms are empty most of the time but have occasional sessions.
            scenario = random.choices(["vacant", "class_in_use"], weights=[70, 30], k=1)[0]
            self.people_count = 0 if scenario == "vacant" else random.randint(1, 10)

        self.occupancy = self.people_count > 0
        if not self.occupancy:
            self.light = self.fan = self.ac = False
            # Small standby consumption represents devices such as indicator lights.
            self.base_power_w = random.uniform(1.0, 5.0)
        else:
            # Appliances are selected once for the scenario, not independently each cycle.
            self.light = random.random() < 0.92
            self.fan = random.random() < 0.88
            self.ac = random.random() < (0.35 if self.room_id == "hostel_room" else 0.25)
            self.base_power_w = self.appliance_power()

        # A scenario lasts 30 to 90 seconds (six to eighteen 5-second readings).
        self.readings_left_in_scenario = random.randint(6, 18)

    def appliance_power(self) -> float:
        """Calculate nominal power from appliance states using prototype ratings."""

        light_power = random.uniform(40.0, 100.0) if self.light else 0.0
        fan_power = random.uniform(50.0, 100.0) if self.fan else 0.0
        ac_power = random.uniform(800.0, 1500.0) if self.ac else 0.0
        return light_power + fan_power + ac_power

    def create_payload(self, elapsed_seconds: float) -> dict:
        """Create one realistic sensor reading and update accumulated energy."""

        if self.readings_left_in_scenario <= 0:
            self.choose_new_scenario()

        # Meter values vary slightly, but remain based on the selected appliances.
        power_w = max(0.0, self.base_power_w * random.uniform(0.96, 1.04))
        voltage_v = random.uniform(220.0, 240.0)
        current_a = power_w / voltage_v

        # kWh = watts multiplied by elapsed seconds, divided by 3,600,000.
        self.energy_kwh += power_w * elapsed_seconds / 3_600_000
        self._last_power_w = power_w
        self.readings_left_in_scenario -= 1

        return {
            "room_id": self.room_id,
            "occupancy": self.occupancy,
            "people_count": self.people_count,
            "mmwave_presence": self.occupancy,
            "light": self.light,
            "fan": self.fan,
            "ac": self.ac,
            "voltage": round(voltage_v, 2),
            "current": round(current_a, 3),
            "power": round(power_w, 2),
            "energy_kwh": round(self.energy_kwh, 6),
        }

    def log_message(self, payload: dict) -> str:
        """Format one clear console line after a successful API submission."""

        occupancy = "OCCUPIED" if payload["occupancy"] else "VACANT"
        presence = "YES" if payload["mmwave_presence"] else "NO"
        people_word = "person" if payload["people_count"] == 1 else "people"
        return (
            f"{self.display_name} | {occupancy} | {payload['people_count']} {people_word} | "
            f"mmWave: {presence} | Light: {'ON' if payload['light'] else 'OFF'} | "
            f"Fan: {'ON' if payload['fan'] else 'OFF'} | AC: {'ON' if payload['ac'] else 'OFF'} | "
            f"Power: {payload['power']:.0f} W | Energy: {payload['energy_kwh']:.3f} kWh"
        )


def submit_reading(room: RoomSimulator, payload: dict) -> None:
    """Send one reading to FastAPI and keep running if the backend is offline."""

    try:
        response = requests.post(API_URL, json=payload, timeout=3)
        response.raise_for_status()
        print(room.log_message(payload))
    except requests.RequestException as error:
        print(f"{room.display_name} | Backend unavailable ({error}). Retrying in 5 seconds...")


def main() -> None:
    """Send two stateful room readings every five seconds until Ctrl+C is pressed."""

    rooms = [
        RoomSimulator("hostel_room", "HOSTEL"),
        RoomSimulator("classroom", "CLASSROOM"),
    ]
    previous_time = time.monotonic()
    print("SEMS sensor simulator started. Press Ctrl+C to stop.")

    try:
        while True:
            current_time = time.monotonic()
            elapsed_seconds = current_time - previous_time
            previous_time = current_time

            for room in rooms:
                payload = room.create_payload(elapsed_seconds)
                submit_reading(room, payload)

            time.sleep(SEND_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\nSEMS sensor simulator stopped cleanly.")


if __name__ == "__main__":
    main()
