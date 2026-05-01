import streamlit as st
import json
import os
from datetime import datetime, timedelta
import random
import time

try:
    import folium
    from streamlit_folium import st_folium
    MAP_AVAILABLE = True
except:
    MAP_AVAILABLE = False

st.set_page_config(page_title="Security Tracker", page_icon="🛡️", layout="wide")

# Files
DATA_FILE = "locations.json"
OTP_FILE = "otp_store.json"

# Session
if 'current_otp' not in st.session_state:
    st.session_state.current_otp = None
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

# ============ FUNCTIONS ============
def generate_otp():
    return ''.join(random.choices('0123456789', k=6))

def save_otp(device_id, otp):
    try:
        otp_data = {}
        if os.path.exists(OTP_FILE):
            with open(OTP_FILE, 'r') as f:
                otp_data = json.load(f)
        
        otp_data[device_id] = {
            "otp": otp,
            "created": datetime.now().isoformat(),
            "expires": (datetime.now() + timedelta(hours=12)).isoformat(),
            "used": False
        }
        
        with open(OTP_FILE, 'w') as f:
            json.dump(otp_data, f)
        return True
    except:
        return False

def verify_otp(device_id, entered_otp):
    try:
        if not os.path.exists(OTP_FILE):
            return False, "No OTP generated"
        
        with open(OTP_FILE, 'r') as f:
            otp_data = json.load(f)
        
        if device_id not in otp_data:
            return False, "Invalid device"
        
        otp_info = otp_data[device_id]
        expiry = datetime.fromisoformat(otp_info['expires'])
        
        if datetime.now() > expiry:
            return False, "OTP expired"
        if otp_info['used']:
            return False, "OTP already used"
        if otp_info['otp'] == entered_otp:
            otp_data[device_id]['used'] = True
            with open(OTP_FILE, 'w') as f:
                json.dump(otp_data, f)
            return True, "Verified!"
        
        return False, "Invalid OTP"
    except:
        return False, "Error"

def save_location(device_id, lat, lon):
    try:
        data = {}
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
        
        if device_id not in data:
            data[device_id] = []
        
        data[device_id].append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "lat": float(lat),
            "lon": float(lon)
        })
        
        if len(data[device_id]) > 1000:
            data[device_id] = data[device_id][-1000:]
        
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f)
        return True
    except:
        return False

def load_locations():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

# ============ UI ============
st.title("🛡️ Security Location Tracker")
st.markdown("### 🔐 Automatic OTP Tracking System")

params = st.query_params

# ============ BOSS VIEW ============
boss_tab, admin_tab = st.tabs(["📱 Boss View", "🔐 Admin Panel"])

with boss_tab:
    st.header("📍 Automatic Location Sharing")
    
    # Auto-detect if OTP in URL
    if 'device' in params and 'otp' in params:
        device = params['device']
        otp = params['otp']
        
        valid, msg = verify_otp(device, otp)
        
        if valid:
            # Check if location coordinates in URL (from JavaScript)
            if 'lat' in params and 'lon' in params:
                lat = params['lat']
                lon = params['lon']
                save_location(device, lat, lon)
                st.success(f"📍 Location Auto-Sent: {lat}, {lon}")
            
            st.success(f"✅ Tracking Active!")
            st.markdown(f"""
            ### 🟢 Live Tracking ON
            **Device:** {device}  
            **Status:** Location auto-sending every 30 seconds
            """)
            
            # JavaScript for automatic location capture
            st.components.v1.html(f"""
                <html>
                <head>
                    <style>
                        body {{
                            font-family: Arial;
                            text-align: center;
                            padding: 20px;
                            background: #f0f8f0;
                        }}
                        .status {{
                            color: green;
                            font-size: 24px;
                            font-weight: bold;
                        }}
                        .pulse {{
                            animation: pulse 2s infinite;
                        }}
                        @keyframes pulse {{
                            0% {{ opacity: 1; }}
                            50% {{ opacity: 0.5; }}
                            100% {{ opacity: 1; }}
                        }}
                    </style>
                </head>
                <body>
                    <div class="status pulse">🟢 TRACKING ACTIVE</div>
                    <p>📍 Location auto-sending...</p>
                    <p style="color:gray;font-size:12px;">Keep this page open</p>
                    
                    <script>
                    var device = '{device}';
                    var otp = '{otp}';
                    var baseUrl = window.location.href.split('?')[0];
                    
                    function sendLocation() {{
                        if (navigator.geolocation) {{
                            navigator.geolocation.getCurrentPosition(
                                function(position) {{
                                    var lat = position.coords.latitude;
                                    var lon = position.coords.longitude;
                                    
                                    // Send to server
                                    var url = baseUrl + '?device=' + device + 
                                              '&otp=' + otp + 
                                              '&lat=' + lat + 
                                              '&lon=' + lon;
                                    
                                    fetch(url, {{mode: 'no-cors'}});
                                    
                                    console.log('Location sent: ' + lat + ', ' + lon);
                                }},
                                function(error) {{
                                    console.log('GPS waiting...');
                                }},
                                {{
                                    enableHighAccuracy: true,
                                    timeout: 10000,
                                    maximumAge: 0
                                }}
                            );
                        }}
                    }}
                    
                    // Send location immediately and then every 30 seconds
                    sendLocation();
                    setInterval(sendLocation, 30000);
                    </script>
                </body>
                </html>
            """, height=250)
            
            st.info("📱 **Boss:** Bas page open rakhein, location automatic update hoti rahegi")
            
        else:
            st.error(f"❌ {msg}")
    
    # Manual OTP Form
    with st.form("otp_form"):
        st.subheader("🔢 Enter OTP to Start")
        st.markdown("OTP enter karte hi location automatic share hona start ho jayegi")
        
        device_id = st.text_input("Your Name/ID:", "Sarah")
        otp_input = st.text_input("6-Digit OTP:", max_chars=6)
        
        if st.form_submit_button("✅ Start Auto Tracking"):
            valid, msg = verify_otp(device_id, otp_input)
            if valid:
                st.success("✅ Verified! Redirecting...")
                # Redirect with OTP
                st.markdown(f"""
                <meta http-equiv="refresh" content="1;url=?device={device_id}&otp={otp_input}">
                """, unsafe_allow_html=True)
            else:
                st.error(msg)

# ============ ADMIN PANEL ============
with admin_tab:
    st.header("🔐 Admin Controls")
    
    if not st.session_state.admin_logged_in:
        admin_pass = st.text_input("Admin Password:", type="password")
        if st.button("🔑 Login"):
            if admin_pass == "Security@2024":
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Wrong password")
    else:
        st.success("✅ Admin Access")
        
        # OTP Generator
        st.subheader("🎫 Generate OTP for Boss")
        
        col1, col2 = st.columns(2)
        with col1:
            device_name = st.text_input("Boss Name:", "Sarah")
        with col2:
            validity = st.selectbox("OTP Validity:", ["12 Hours", "24 Hours", "7 Days"])
        
        validity_hours = {"12 Hours": 12, "24 Hours": 24, "7 Days": 168}
        
        if st.button("🔢 Generate OTP", type="primary", use_container_width=True):
            otp = generate_otp()
            
            # Custom validity
            otp_data = {}
            if os.path.exists(OTP_FILE):
                with open(OTP_FILE, 'r') as f:
                    otp_data = json.load(f)
            
            otp_data[device_name] = {
                "otp": otp,
                "created": datetime.now().isoformat(),
                "expires": (datetime.now() + timedelta(hours=validity_hours[validity])).isoformat(),
                "used": False
            }
            
            with open(OTP_FILE, 'w') as f:
                json.dump(otp_data, f)
            
            st.session_state.current_otp = otp
            
            # Display OTP
            st.success("✅ OTP Generated Successfully!")
            st.markdown(f"""
            ---
            ## 🔢 OTP: **{otp}**
            
            📱 **Device:** {device_name}  
            ⏰ **Valid:** {validity}  
            🔗 **App Link:** YOUR_STREAMLIT_URL
            
            ---
            ### 📋 Boss Ko Yeh Bhejein:
            
            ```
            👋 Salam Sir,
            
            Location tracking ke liye:
            
            1. Yeh link open karein:
               YOUR_STREAMLIT_URL
            
            2. Apna naam: {device_name}
            
            3. OTP enter karein: {otp}
            
            4. Done! Page open rakhein.
            
            Kuch aur nahi karna 🙏
            ```
            """)
        
        st.divider()
        
        # Live Tracking View
        st.subheader("📍 Live Location Monitor")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        with col2:
            auto_refresh = st.checkbox("Auto Refresh", value=True)
        
        locations = load_locations()
        
        if locations:
            # Status cards
            for device, locs in locations.items():
                if locs:
                    latest = locs[-1]
                    
                    # Calculate time difference
                    time_str = f"{latest['date']} {latest['time']}"
                    last_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                    diff = (datetime.now() - last_time).seconds
                    
                    if diff < 60:
                        status_icon = "🟢"
                        status_text = "LIVE NOW"
                        status_color = "green"
                    elif diff < 300:
                        status_icon = "🟡"
                        status_text = f"{diff//60} min ago"
                        status_color = "orange"
                    else:
                        status_icon = "🔴"
                        status_text = f"{diff//60} min ago"
                        status_color = "red"
                    
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 15px;
                        border-radius: 10px;
                        margin: 10px 0;
                        color: white;
                    ">
                        <h3>{status_icon} {device}</h3>
                        <p>📍 {latest['lat']:.4f}, {latest['lon']:.4f}</p>
                        <p>🕐 {latest['time']} | <span style="color: {status_color};">{status_text}</span></p>
                        <p>📊 Total Updates: {len(locs)}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Map
            if MAP_AVAILABLE:
                st.subheader("🗺️ Map View")
                try:
                    latest_lats = []
                    latest_lons = []
                    for locs in locations.values():
                        if locs:
                            latest = locs[-1]
                            latest_lats.append(latest['lat'])
                            latest_lons.append(latest['lon'])
                    
                    if latest_lats:
                        center_lat = sum(latest_lats) / len(latest_lats)
                        center_lon = sum(latest_lons) / len(latest_lons)
                        
                        m = folium.Map(location=[center_lat, center_lon], zoom_start=15)
                        
                        colors = ['red', 'blue', 'green', 'purple', 'orange']
                        for idx, (device, locs) in enumerate(locations.items()):
                            if locs:
                                color = colors[idx % len(colors)]
                                
                                # Path trail
                                points = [[l['lat'], l['lon']] for l in locs[-20:]]
                                if len(points) > 1:
                                    folium.PolyLine(points, color=color, weight=3, opacity=0.5).add_to(m)
                                
                                # Latest position
                                latest = locs[-1]
                                folium.Marker(
                                    [latest['lat'], latest['lon']],
                                    popup=f"<b>{device}</b><br>🕐 {latest['time']}",
                                    icon=folium.Icon(color=color, icon='user', prefix='fa')
                                ).add_to(m)
                                
                                folium.Circle(
                                    [latest['lat'], latest['lon']],
                                    radius=20,
                                    color=color,
                                    fill=True,
                                    opacity=0.3
                                ).add_to(m)
                        
                        st_folium(m, width=800, height=500)
                except:
                    st.warning("Map loading...")
            
            # History table
            with st.expander("📊 View History"):
                for device, locs in locations.items():
                    if locs:
                        st.write(f"**{device}** - Last 20 updates:")
                        st.dataframe(locs[-20:], use_container_width=True)
        else:
            st.info("📍 Waiting for location data... Generate OTP and share with boss")
        
        # Auto refresh
        if auto_refresh:
            time.sleep(10)
            st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align:center; color:gray;'>
    <h4>🛡️ Automatic Security System</h4>
    <p>✅ OTP-Based | ✅ Auto Location | ✅ No Manual Input | ✅ Boss-Friendly</p>
</div>
""", unsafe_allow_html=True)
