
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Server Management",
    page_icon="☁️",
    layout="wide"
)

st.title("☁️ Cloud Server Management")
st.write("Demo server management dashboard")

# Demo server details
if "servers" not in st.session_state:
    st.session_state.servers = [
        {"Server ID": "SRV001", "Name": "Web Server", "Status": "Running"},
        {"Server ID": "SRV002", "Name": "Database Server", "Status": "Stopped"},
        {"Server ID": "SRV003", "Name": "Application Server", "Status": "Running"},
    ]

st.subheader("🖥️ Server List")

st.dataframe(
    pd.DataFrame(st.session_state.servers),
    use_container_width=True
)

st.subheader("⚙️ Server Controls")

server_names = [s["Name"] for s in st.session_state.servers]

selected_server = st.selectbox(
    "Select a server",
    server_names
)

server = next(
    s for s in st.session_state.servers
    if s["Name"] == selected_server
)

st.write("Current status:", server["Status"])

col1, col2 = st.columns(2)

with col1:
    if st.button("▶️ Start Server"):
        server["Status"] = "Running"
        st.success(f"{selected_server} is now Running")
        st.rerun()

with col2:
    if st.button("⏹️ Stop Server"):
        server["Status"] = "Stopped"
        st.warning(f"{selected_server} is now Stopped")
        st.rerun()

st.caption(
    "Demo only: These buttons change simulated server status. "
    "They do not start or stop actual cloud servers."
)
