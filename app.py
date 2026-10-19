
import streamlit as st
import psutil
import sqlite3
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ==================== PAGE CONFIGURATION ====================

st.set_page_config(
    page_title="Cloud Management Dashboard",
    page_icon="☁️",
    layout="wide"
)

st_autorefresh(interval=5000, key="dashboard_refresh")

DB_NAME = "monitor_history.db"


# ==================== DATABASE SETUP ====================

def get_connection():
    return sqlite3.connect(DB_NAME)


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS servers (
                server_id TEXT PRIMARY KEY,
                server_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Inactive',
                cpu_usage REAL DEFAULT 0,
                ram_usage REAL DEFAULT 0,
                created_at TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS monitoring (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recorded_at TEXT,
                cpu REAL,
                ram REAL,
                disk REAL
            )
        """)

        count = conn.execute(
            "SELECT COUNT(*) FROM servers"
        ).fetchone()[0]

        if count == 0:
            demo_servers = [
                ("SRV-001", "Web Server", "Active", 45, 60,
                 datetime.now().isoformat(timespec="seconds")),
                ("SRV-002", "Database Server", "Active", 72, 85,
                 datetime.now().isoformat(timespec="seconds")),
                ("SRV-003", "Application Server", "Inactive", 0, 0,
                 datetime.now().isoformat(timespec="seconds")),
                ("SRV-004", "Backup Server", "Active", 38, 42,
                 datetime.now().isoformat(timespec="seconds"))
            ]

            conn.executemany("""
                INSERT INTO servers
                (server_id, server_name, status, cpu_usage,
                 ram_usage, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, demo_servers)


initialize_database()


# ==================== DATABASE OPERATIONS ====================

def get_servers():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT server_id, server_name, status,
                   cpu_usage, ram_usage, created_at
            FROM servers
            ORDER BY server_id
        """).fetchall()

    return [
        {
            "Server ID": row[0],
            "Server Name": row[1],
            "Status": row[2],
            "CPU Usage (%)": row[3],
            "RAM Usage (%)": row[4],
            "Created At": row[5]
        }
        for row in rows
    ]


def save_server(server_id, server_name):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO servers
            (server_id, server_name, status, cpu_usage,
             ram_usage, created_at)
            VALUES (?, ?, 'Inactive', 0, 0, ?)
        """, (
            server_id,
            server_name,
            datetime.now().isoformat(timespec="seconds")
        ))


def update_server_status(server_id, status):
    with get_connection() as conn:
        conn.execute("""
            UPDATE servers
            SET status = ?
            WHERE server_id = ?
        """, (status, server_id))


def delete_server(server_id):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM servers WHERE server_id = ?",
            (server_id,)
        )


# ==================== HEADER ====================

st.title("☁️ Cloud Management Dashboard")
st.caption("Server Management, Resource Monitoring and Usage History")

st.sidebar.title("⚙️ Dashboard Settings")
st.sidebar.info("Cloud Management System")

page = st.sidebar.radio(
    "Navigate",
    [
        "Dashboard",
        "Server Management",
        "Monitoring History",
        "About Project"
    ]
)


# ==================== RESOURCE MONITORING ====================

try:
    cpu = psutil.cpu_percent(interval=0.3)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage("C:\\").percent
except Exception as error:
    st.error(f"Unable to read system metrics: {error}")
    cpu, ram, disk = 0, 0, 0

with get_connection() as conn:
    conn.execute("""
        INSERT INTO monitoring (recorded_at, cpu, ram, disk)
        VALUES (?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        cpu,
        ram,
        disk
    ))


# ==================== DASHBOARD ====================

if page == "Dashboard":

    st.subheader("Welcome to your Cloud Monitoring System")
    st.success("Dashboard is running successfully!")

    servers = get_servers()
    total_count = len(servers)
    active_count = sum(
        server["Status"] == "Active" for server in servers
    )
    inactive_count = total_count - active_count

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("☁️ Total Servers", total_count)
    col2.metric("✅ Active Servers", active_count)
    col3.metric("⏸️ Inactive Servers", inactive_count)
    col4.metric("💰 Estimated Daily Cost", "$25.50")

    st.caption(
        "Server records and cost are demonstration data. "
        "Cost is not connected to cloud billing."
    )

    st.divider()
    st.subheader("🖥️ Local Computer Resource Monitoring")

    col1, col2, col3 = st.columns(3)
    col1.metric("CPU Usage", f"{cpu:.1f}%")
    col2.metric("RAM Usage", f"{ram:.1f}%")
    col3.metric("Disk Usage (C:)", f"{disk:.1f}%")

    st.caption(
        "These metrics represent this Windows computer, "
        "not actual AWS cloud servers."
    )

    st.subheader("🚨 System Health Alerts")

    if cpu >= 80:
        st.error("High CPU usage detected!")
    else:
        st.success("CPU usage is normal.")

    if ram >= 90:
        st.error("High RAM usage detected!")
    else:
        st.success("RAM usage is normal.")

    if disk >= 90:
        st.error("Disk usage is high!")
    else:
        st.success("Disk usage is normal.")

    st.divider()
    st.subheader("📊 Server Status Overview")

    status_data = pd.DataFrame({
        "Status": ["Active", "Inactive"],
        "Servers": [active_count, inactive_count]
    })

    st.bar_chart(status_data, x="Status", y="Servers")

    st.subheader("🗄️ Server Details")

    if servers:
        st.dataframe(
            pd.DataFrame(servers).drop(columns=["Created At"]),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No servers available. Add a server in Server Management.")

    st.subheader("📈 Resource Usage History")

    with get_connection() as conn:
        chart_data = pd.read_sql_query("""
            SELECT recorded_at, cpu, ram, disk
            FROM monitoring
            ORDER BY id DESC
            LIMIT 100
        """, conn)

    if not chart_data.empty:
        chart_data = chart_data.sort_values("recorded_at")
        st.line_chart(chart_data.set_index("recorded_at"))
    else:
        st.info("Monitoring history is not available yet.")


# ==================== SERVER MANAGEMENT ====================

elif page == "Server Management":

    st.header("🖥️ Server Management")
    st.write("Add, view, start, stop and delete demo server records.")

    servers = get_servers()

    st.subheader("➕ Add New Server")

    with st.form("add_server_form", clear_on_submit=True):
        new_server_id = st.text_input(
            "Server ID",
            placeholder="Example: SRV-005"
        )
        new_server_name = st.text_input(
            "Server Name",
            placeholder="Example: Web Server"
        )

        submitted = st.form_submit_button("Add Server")

        if submitted:
            server_id = new_server_id.strip()
            server_name = new_server_name.strip()

            if not server_id or not server_name:
                st.warning("Please enter both Server ID and Server Name.")
            elif any(
                server["Server ID"].lower() == server_id.lower()
                for server in servers
            ):
                st.error("This Server ID already exists.")
            elif any(
                server["Server Name"].lower() == server_name.lower()
                for server in servers
            ):
                st.error("This Server Name already exists.")
            else:
                try:
                    save_server(server_id, server_name)
                    st.success("Server saved to the database!")
                    st.rerun()
                except sqlite3.Error as error:
                    st.error(f"Could not save server: {error}")

    st.divider()
    st.subheader("📋 Manage Existing Servers")

    servers = get_servers()

    if not servers:
        st.info("No servers found. Add a server above.")
    else:
        filter_status = st.selectbox(
            "Filter by Status",
            ["All", "Active", "Inactive"],
            key="management_filter"
        )

        visible_servers = (
            servers if filter_status == "All"
            else [
                server for server in servers
                if server["Status"] == filter_status
            ]
        )

        st.dataframe(
            pd.DataFrame(visible_servers).drop(
                columns=["Created At"]
            ),
            use_container_width=True,
            hide_index=True
        )

        st.subheader("⚙️ Server Controls")

        selected_id = st.selectbox(
            "Select Server",
            [server["Server ID"] for server in servers],
            format_func=lambda sid: next(
                f"{server['Server Name']} ({sid})"
                for server in servers
                if server["Server ID"] == sid
            ),
            key="control_server"
        )

        selected = next(
            server for server in servers
            if server["Server ID"] == selected_id
        )

        st.write(f"Current status: **{selected['Status']}**")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("▶️ Start Demo Server", use_container_width=True):
                update_server_status(selected_id, "Active")
                st.success("Demo server status updated to Active.")
                st.rerun()

        with col2:
            if st.button("⏹️ Stop Demo Server", use_container_width=True):
                update_server_status(selected_id, "Inactive")
                st.success("Demo server status updated to Inactive.")
                st.rerun()

        st.divider()
        st.subheader("🗑️ Delete Server")

        delete_id = st.selectbox(
            "Select Server to Delete",
            [server["Server ID"] for server in servers],
            format_func=lambda sid: next(
                f"{server['Server Name']} ({sid})"
                for server in servers
                if server["Server ID"] == sid
            ),
            key="delete_server_select"
        )

        confirm_delete = st.checkbox(
            "I confirm that I want to delete this server."
        )

        if st.button(
            "Delete Selected Server",
            disabled=not confirm_delete,
            type="primary"
        ):
            delete_server(delete_id)
            st.success("Server deleted from the database.")
            st.rerun()

    st.caption(
        "These controls manage simulated records only. "
        "They do not create, start or stop real cloud infrastructure."
    )


# ==================== MONITORING HISTORY ====================

elif page == "Monitoring History":

    st.header("📈 Monitoring History")
    st.write("Historical resource measurements from this computer.")

    with get_connection() as conn:
        history = pd.read_sql_query("""
            SELECT id, recorded_at, cpu, ram, disk
            FROM monitoring
            ORDER BY id DESC
            LIMIT 500
        """, conn)

    if history.empty:
        st.info("No monitoring records available.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Recorded Samples", len(history))
        col2.metric("Latest CPU", f"{history.iloc[0]['cpu']:.1f}%")
        col3.metric("Latest RAM", f"{history.iloc[0]['ram']:.1f}%")

        st.subheader("📊 Historical Resource Chart")
        chart = history.sort_values("id").set_index("recorded_at")
        st.line_chart(chart[["cpu", "ram", "disk"]])

        st.subheader("📋 Measurement Records")
        st.dataframe(
            history,
            use_container_width=True,
            hide_index=True
        )

        csv_data = history.to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇️ Download History as CSV",
            data=csv_data,
            file_name="monitoring_history.csv",
            mime="text/csv"
        )


# ==================== ABOUT PROJECT ====================

elif page == "About Project":

    st.header("ℹ️ About Cloud Management Dashboard")

    st.markdown("""
    ### Project Overview
    This project demonstrates a cloud-management-style dashboard
    built using Python, Streamlit, SQLite and psutil.

    ### Features
    - Live local computer CPU, RAM and disk monitoring
    - Resource threshold alerts
    - Demo server status overview and filtering
    - Add and delete server records
    - Persist server details and status in SQLite
    - Monitoring history and performance charts
    - CSV export of monitoring records

    ### Technology Stack
    - Python
    - Streamlit
    - SQLite
    - Pandas
    - psutil

    ### Important Limitation
    Local system metrics come from the computer running this app.
    The server management functions operate on simulated records.
    Real AWS EC2 monitoring and control are not configured.
    """)

    st.info(
        "This is a demonstration project, not yet connected "
        "to a real cloud provider."
    )


# ==================== FOOTER ====================

st.divider()
st.caption(
    "Cloud Management Dashboard | Python + Streamlit + SQLite"
)
