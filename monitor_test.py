
import sqlite3
from datetime import datetime

import pandas as pd
import psutil
import streamlit as st
from streamlit_autorefresh import st_autorefresh


# Page Configuration
st.set_page_config(
    page_title="Cloud Management Dashboard",
    page_icon="☁️",
    layout="wide"
)

st.title("☁️ Cloud Management Dashboard")
st.caption("Real-Time Server Resource Monitoring")


# Auto Refresh Every 5 Seconds
st_autorefresh(interval=5000, key="server_refresh")


# Get Local Computer Metrics
cpu_usage = psutil.cpu_percent(interval=0.5)
ram_usage = psutil.virtual_memory().percent
disk_usage = psutil.disk_usage("C:\\").percent


# Display Current Metrics
st.subheader("📊 Live Resource Usage")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("CPU Usage", f"{cpu_usage:.1f}%")

with col2:
    st.metric("RAM Usage", f"{ram_usage:.1f}%")

with col3:
    st.metric("Disk Usage (C:)", f"{disk_usage:.1f}%")


# Resource Usage Alerts
st.subheader("🚨 System Health Alerts")

if cpu_usage >= 80:
    st.error("High CPU usage detected!")
else:
    st.success("CPU usage is normal.")

if ram_usage >= 90:
    st.error("High RAM usage detected!")
else:
    st.success("RAM usage is normal.")

if disk_usage >= 90:
    st.error("Disk usage is high!")
else:
    st.success("Disk usage is normal.")


# Create Monitoring History Database
conn = sqlite3.connect("monitor_history.db")

conn.execute("""
    CREATE TABLE IF NOT EXISTS monitoring (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recorded_at TEXT,
        cpu REAL,
        ram REAL,
        disk REAL
    )
""")

# Save Current Metrics
conn.execute(
    """
    INSERT INTO monitoring (recorded_at, cpu, ram, disk)
    VALUES (?, ?, ?, ?)
    """,
    (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        cpu_usage,
        ram_usage,
        disk_usage
    )
)

conn.commit()


# Display Recent Monitoring History
st.subheader("📋 Recent Monitoring History")

history = pd.read_sql_query(
    """
    SELECT recorded_at, cpu, ram, disk
    FROM monitoring
    ORDER BY id DESC
    LIMIT 20
    """,
    conn
)

st.dataframe(history, use_container_width=True)


# Historical Performance Chart
st.subheader("📈 Resource Usage History")

chart_data = pd.read_sql_query(
    """
    SELECT recorded_at, cpu, ram, disk
    FROM monitoring
    ORDER BY id DESC
    LIMIT 100
    """,
    conn
)

conn.close()

if not chart_data.empty:
    chart_data = chart_data.sort_values("recorded_at")
    chart_data = chart_data.set_index("recorded_at")
    st.line_chart(chart_data)
else:
    st.info("Monitoring history is not available yet.")


# Project Information
st.divider()
st.caption(
    "Note: These metrics monitor your local Windows computer, "
    "not actual AWS cloud servers."
)
