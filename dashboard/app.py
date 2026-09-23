"""Live Streamlit dashboard for the Smart Energy Management System prototype."""

from datetime import datetime, timezone

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st


API_BASE_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT_SECONDS = 3

st.set_page_config(page_title="SEMS | IIT Madras Zanzibar", page_icon="S", layout="wide")

# These styles keep the dashboard compact and easy to scan on a laptop screen.
st.markdown(
    """
    <style>
        .stApp { background: #f6f8fb; }
        .block-container { max-width: 1320px; padding-top: 2rem; padding-bottom: 2rem; }
        .sems-brand { color: #0b6b4f; font-size: 2.35rem; font-weight: 800; letter-spacing: .08em; margin: 0; }
        .sems-title { color: #14213d; font-size: 1.55rem; font-weight: 700; margin: .15rem 0; }
        .sems-location { color: #64748b; font-size: .98rem; margin: 0; }
        .online-badge { background: #dcfce7; border: 1px solid #86efac; border-radius: 999px; color: #166534; display: inline-block; font-size: .9rem; font-weight: 700; padding: .5rem .9rem; }
        .section-label { color: #0f172a; font-size: 1.25rem; font-weight: 750; margin: 1.4rem 0 .7rem; }
        .room-heading { color: #0f172a; font-size: 1.25rem; font-weight: 750; margin-bottom: .2rem; }
        .room-subtitle { color: #64748b; font-size: .88rem; margin-bottom: .8rem; }
        [data-testid="stMetric"] { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: .75rem .85rem; }
        [data-testid="stMetricLabel"] { white-space: normal; overflow: visible; }
        [data-testid="stMetricValue"] { font-size: 1.3rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_rooms() -> tuple[list[dict] | None, str | None]:
    """Fetch current room status without crashing if FastAPI is unavailable."""

    try:
        response = requests.get(f"{API_BASE_URL}/api/rooms", timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            return None, "The /api/rooms response was not a list."
        return data, None
    except requests.RequestException as error:
        return None, str(error)


def get_energy_data() -> tuple[list[dict] | None, str | None]:
    """Fetch recent PostgreSQL-backed readings through the FastAPI API."""

    try:
        response = requests.get(
            f"{API_BASE_URL}/api/energy",
            params={"limit": 500},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            return None, "The /api/energy response was not a list."
        return data, None
    except requests.RequestException as error:
        return None, str(error)


def process_latest_readings(rooms: list[dict]) -> pd.DataFrame:
    """Convert current API readings to a clean DataFrame for live summaries."""

    room_data = pd.DataFrame(rooms)
    if not room_data.empty and "timestamp" in room_data:
        room_data["timestamp"] = pd.to_datetime(room_data["timestamp"], utc=True)
    return room_data


def room_title(room_id: str) -> str:
    """Convert backend room IDs to reader-friendly dashboard labels."""

    return "Hostel Room" if room_id == "hostel_room" else "Classroom"


def on_off(value: bool) -> str:
    """Display a Boolean appliance state as a clear label."""

    return "ON" if value else "OFF"


def format_timestamp(timestamp: object) -> str:
    """Format an ISO timestamp from FastAPI for display in a room card."""

    converted = pd.to_datetime(timestamp, utc=True, errors="coerce")
    if pd.isna(converted):
        return "Not available"
    return converted.strftime("%Y-%m-%d %H:%M:%S UTC")


def render_room_card(room: dict) -> None:
    """Render all current sensor and appliance values for one monitored room."""

    occupancy = "Occupied" if room["occupancy"] else "Unoccupied"
    mmwave = "Detected" if room["mmwave_presence"] else "Not detected"

    with st.container(border=True):
        st.markdown(f'<div class="room-heading">{room_title(room["room_id"])}</div>', unsafe_allow_html=True)
        st.markdown('<div class="room-subtitle">Latest sensor reading from SEMS API</div>', unsafe_allow_html=True)

        status_columns = st.columns(3)
        status_columns[0].metric("Occupancy", occupancy)
        status_columns[1].metric("People Count", int(room["people_count"]))
        status_columns[2].metric("mmWave Presence", mmwave)

        appliance_columns = st.columns(3)
        appliance_columns[0].metric("Light", on_off(room["light"]))
        appliance_columns[1].metric("Fan", on_off(room["fan"]))
        appliance_columns[2].metric("AC", on_off(room["ac"]))

        electrical_columns = st.columns(4)
        electrical_columns[0].metric("Voltage", f"{float(room['voltage']):.1f} V")
        electrical_columns[1].metric("Current", f"{float(room['current']):.2f} A")
        electrical_columns[2].metric("Power", f"{float(room['power']):.1f} W")
        electrical_columns[3].metric("Energy", f"{float(room['energy_kwh']):.3f} kWh")
        st.caption(f"Last reading: {format_timestamp(room['timestamp'])}")


def render_energy_charts(energy_data: list[dict]) -> None:
    """Render real power and accumulated-energy charts returned by /api/energy."""

    energy_frame = pd.DataFrame(energy_data)
    if energy_frame.empty:
        st.info("No stored energy readings yet. Start the simulator to populate the charts.")
        return

    # Sort each room's history so Plotly draws lines in timestamp order.
    energy_frame["timestamp"] = pd.to_datetime(energy_frame["timestamp"], utc=True)
    energy_frame = energy_frame.sort_values(["room_id", "timestamp", "id"])
    colors = {"hostel_room": "#0b6b4f", "classroom": "#2563eb"}
    power_figure = go.Figure()
    consumption_figure = go.Figure()

    for room_id in ("hostel_room", "classroom"):
        room_history = energy_frame[energy_frame["room_id"] == room_id]
        if room_history.empty:
            continue
        label = room_title(room_id)
        trace_settings = {"color": colors[room_id], "width": 3}
        power_figure.add_trace(
            go.Scatter(x=room_history["timestamp"], y=room_history["power"], mode="lines+markers", name=label, line=trace_settings)
        )
        consumption_figure.add_trace(
            go.Scatter(x=room_history["timestamp"], y=room_history["energy_kwh"], mode="lines+markers", name=label, line=trace_settings)
        )

    chart_layout = {
        "height": 340,
        "margin": {"l": 10, "r": 10, "t": 20, "b": 10},
        "paper_bgcolor": "white",
        "plot_bgcolor": "white",
        "hovermode": "x unified",
        "legend_title": "Location",
    }
    power_figure.update_layout(**chart_layout, yaxis_title="Power (W)", xaxis_title="Time")
    consumption_figure.update_layout(**chart_layout, yaxis_title="Energy (kWh)", xaxis_title="Time")
    for figure in (power_figure, consumption_figure):
        figure.update_xaxes(gridcolor="#e2e8f0")
        figure.update_yaxes(gridcolor="#e2e8f0")

    st.markdown('<div class="section-label">Live Energy Monitoring</div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.plotly_chart(power_figure, use_container_width=True)
    st.markdown('<div class="section-label">Energy Consumption Over Time</div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.plotly_chart(consumption_figure, use_container_width=True)


def render_dashboard() -> None:
    """Fetch live API data and render one dashboard refresh."""

    rooms, rooms_error = get_rooms()
    energy_data, energy_error = get_energy_data()

    header_left, header_right = st.columns([5, 1])
    with header_left:
        st.markdown('<p class="sems-brand">SEMS</p>', unsafe_allow_html=True)
        st.markdown('<p class="sems-title">Smart Energy Management System</p>', unsafe_allow_html=True)
        st.markdown('<p class="sems-location">IIT Madras Zanzibar</p>', unsafe_allow_html=True)
    with header_right:
        if rooms_error:
            st.error("API Offline")
        else:
            st.markdown('<div class="online-badge">System Online</div>', unsafe_allow_html=True)

    st.divider()
    if rooms_error:
        st.warning("SEMS API is currently unavailable.")
        st.caption(f"Connection detail: {rooms_error}")
        return

    latest_readings = process_latest_readings(rooms)
    last_update = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    st.markdown('<div class="section-label">System Status</div>', unsafe_allow_html=True)
    status_columns = st.columns(3)
    status_columns[0].metric("API Connection", "Online")
    status_columns[1].metric("Last Successful Update", last_update)
    status_columns[2].metric("Readings Retrieved", len(energy_data) if energy_data is not None else 0)
    if energy_error:
        st.warning("Room status is available, but recent energy history could not be loaded.")
        st.caption(f"Energy API detail: {energy_error}")

    st.markdown('<div class="section-label">Overview</div>', unsafe_allow_html=True)
    overview_columns = st.columns(3)
    overview_columns[0].metric("Total Power", f"{latest_readings['power'].sum():.1f} W")
    overview_columns[1].metric("Total Energy", f"{latest_readings['energy_kwh'].sum():.3f} kWh")
    overview_columns[2].metric("Occupied Spaces", f"{int(latest_readings['occupancy'].sum())} / 2")

    st.markdown('<div class="section-label">Room Monitoring</div>', unsafe_allow_html=True)
    rooms_by_id = {room["room_id"]: room for room in rooms}
    room_columns = st.columns(2, gap="large")
    for column, room_id in zip(room_columns, ("hostel_room", "classroom")):
        with column:
            room = rooms_by_id.get(room_id)
            if room is None:
                st.warning(f"No current reading is available for {room_title(room_id)}.")
            else:
                render_room_card(room)

    # Only real readings returned by the FastAPI API are charted here.
    if energy_data is not None:
        render_energy_charts(energy_data)


# Streamlit reruns this fragment about every five seconds to request fresh data.
@st.fragment(run_every=5)
def live_dashboard() -> None:
    """Refresh the live API dashboard at a five-second interval."""

    render_dashboard()


live_dashboard()
