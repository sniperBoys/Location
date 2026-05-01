import streamlit as st
import json
import os
from datetime import datetime, timedelta
import random
import time

# Map libraries - try import
try:
    import folium
    from streamlit_folium import st_folium
    MAP_OK = True
except:
    MAP_OK = False

# Page config
st.set_page_config(page_title="Security Tracker", page_icon="🛡️", layout="wide")

# File names
LOCATION_FILE = "locations.json"
OTP_FILE = "otp_store.json"

# Session state
if 'admin_login' not in st.session_state:
    st.session_state.admin_login = False
if 'show_otp' not in st.session_state:
    st.session_state.show_otp = None
if 'device_for_otp' not in st.session_state:
    st.session_state.device_for_otp = None

# ============ HELPER FUNCTIONS ============

def generate_otp():
    """Generate 6 digit OTP"""
    return str(random.randint(100000, 999999))

def save_otp_to_file(device_id, otp, hours=24):
    """Save OTP with expiry"""
    try:
        data = {}
        if os.path.exists(OTP_FILE):
            with open(OTP_FILE, 'r') as f:
                data = json.load(f)
        
        data[device_id] = {
            "otp": otp,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "expires": (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S"),
            "active": True
        }
        
        with open(OTP_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def check_otp(device_id, otp_entered):
    """Verify OTP - Reusable"""
    try:
        if not os.path.exists(OTP_FILE):
            return False, "No OTP generated yet"
        
        with open(OTP_FILE, 'r') as f:
            data = json.load(f)
        
        if device_id not in data:
            return False, "No OTP for this device"
        
        otp_info = data[device_id]
        
        # Check expiry
        expire_time = datetime.strptime(otp_info['expires'], "%Y-%m-%d %H:%M:%S")
        if datetime.now() > expire_time:
            return False, "OTP expired"
        
        # Check otp
        if otp_info['otp'] == otp_entered:
            return True, "Valid"
        else:
            return False, "Wrong OTP"
    
    except Exception as e:
        return False, f"Error: {e}"

def save_location_data(device_id, lat, lon):
    """Save location coordinates"""
    try:
        data = {}
        if os.path.exists(LOCATION_FILE):
            with open(LOCATION_FILE, 'r') as f:
                data = json.load(f)
        
        if device_id not in data:
            data[device_id] = []
        
        data[device_id].append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "lat": float(lat),
            "lon": float(lon)
        })
        
        # Keep last 500 records
        if len(data[device_id]) > 500:
            data[device_id] = data[device_id][-500:]
        
        with open(LOCATION_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except:
        return False

def get_all_locations():
    """Load all saved locations"""
    if os.path.exists(LOCATION_FILE):
        with open(LOCATION_FILE, 'r') as f:
            return json.load(f)
    return {}

# ============ MAIN APP ============

st.title("🛡️ Security Location Tracking System")
st.markdown("---")

# Get URL parameters
url_params = st.query_params

# ============ CREATE TABS ============
tab1, tab2 = st.tabs(["📱 Boss View", "🔐 Admin Panel"])

# ============ TAB 1: BOSS VIEW ============
with tab1:
    st.header("📍 Location Sharing")
    
    # Check if OTP and device in URL
    has_device = 'device' in url_params
    has_otp = 'otp' in url_params
    has_location = 'lat' in url_params and 'lon' in url_params
    
    if has_device and has_otp:
        device = url_params['device']
        otp = url_params['otp']
        
        # Verify OTP
        valid, message = check_otp(device, otp)
        
        if valid:
            # Save location if coordinates present
            if has_location:
                save_location_data(device, url_params['lat'], url_params['lon'])
            
            # Success message
            st.success("✅ OTP Verified - Tracking Active")
            st.balloons()
            
            # Status display
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #11998e, #38ef7d); 
                        padding: 20px; border-radius: 10px; color: white; text-align: center;">
                <h2>🟢 LIVE TRACKING</h2>
                <p><b>Device:</b> {device}</p>
                <p><b>OTP:</b> {otp}</p>
                <p>📍 Location auto-sending every 30 seconds</p>
            </div>
            """, unsafe_allow_html=True)
            
            # JavaScript for auto location
            st.components.v1.html(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{ font-family: Arial; text-align: center; padding: 10px; }}
                    .dot {{ height: 20px; width: 20px; background-color: #00ff00; 
                            border-radius: 50%; display: inline-block; animation: blink 1s infinite; }}
                    @keyframes blink {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0; }} 100% {{ opacity: 1; }} }}
                </style>
            </head>
            <body>
                <span class="dot"></span> <b>GPS Active</b>
                <p style="font-size: 12px; color: gray;">Keep this page open</p>
                <script>
                var deviceName = "{device}";
                var otpCode = "{otp}";
                var appUrl = window.location.href.split('?')[0];
                
                function sendGPS() {{
                    if (navigator.geolocation) {{
                        navigator.geolocation.getCurrentPosition(
                            function(pos) {{
                                var lat = pos.coords.latitude;
                                var lon = pos.coords.longitude;
                                var newUrl = appUrl + '?device=' + deviceName + 
                                           '&otp=' + otpCode + 
                                           '&lat=' + lat + '&lon=' + lon;
                                fetch(newUrl);
                                console.log('📍 Sent: ' + lat + ', ' + lon);
                            }},
                            function(err) {{
                                console.log('⏳ Waiting for GPS...');
                            }},
                            {{ enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }}
                        );
                    }}
                }}
                
                sendGPS();
                setInterval(sendGPS, 30000);
                </script>
            </body>
            </html>
            """, height=150)
            
            # Show last known location
            if has_location:
                st.info(f"📍 Current: {url_params['lat']}, {url_params['lon']}")
        
        else:
            st.error(f"❌ {message}")
    
    # OTP entry form
    st.markdown("---")
    st.subheader("🔢 Enter OTP to Start Tracking")
    
    with st.form("boss_form"):
        col1, col2 = st.columns(2)
        with col1:
            device_input = st.text_input("Your Name:", value="Sarah", key="boss_device")
        with col2:
            otp_input = st.text_input("OTP Code:", max_chars=6, key="boss_otp")
        
        submit_btn = st.form_submit_button("✅ Start Tracking", use_container_width=True)
        
        if submit_btn:
            if device_input and otp_input:
                valid, msg = check_otp(device_input, otp_input)
                if valid:
                    st.success("✅ Verified! Starting tracking...")
                    st.markdown(f"""
                    <meta http-equiv="refresh" content="1;url=?device={device_input}&otp={otp_input}">
                    """, unsafe_allow_html=True)
                else:
                    st.error(f"❌ {msg}")
            else:
                st.warning("Please fill both fields")

# ============ TAB 2: ADMIN PANEL ============
with tab2:
    st.header("🔐 Admin Panel")
    
    # Admin login
    if not st.session_state.admin_login:
        st.subheader("Admin Login")
        password = st.text_input("Password:", type="password", key="admin_pass")
        
        if st.button("🔑 Login", use_container_width=True):
            if password == "Secure@2024":
                st.session_state.admin_login = True
                st.rerun()
            else:
                st.error("❌ Wrong password!")
    
    else:
        st.success("✅ Admin Access Granted")
        
        # OTP Generation Section
        st.markdown("---")
        st.subheader("🎫 Generate OTP")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            new_device = st.text_input("Device Name:", value="Sarah", key="admin_device")
        with col2:
            validity_hours = st.selectbox("Valid For:", [1, 6, 12, 24, 48, 72, 168], 
                                         format_func=lambda x: f"{x} Hours")
        with col3:
            st.write("")  # Spacer
            st.write("")
            gen_btn = st.button("🔢 Generate OTP", use_container_width=True, type="primary")
        
        if gen_btn:
            new_otp = generate_otp()
            if save_otp_to_file(new_device, new_otp, validity_hours):
                st.session_state.show_otp = new_otp
                st.session_state.device_for_otp = new_device
        
        # Show generated OTP
        if st.session_state.show_otp:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea, #764ba2); 
                        padding: 25px; border-radius: 15px; color: white; text-align: center;">
                <h1 style="font-size: 60px; letter-spacing: 10px;">{st.session_state.show_otp}</h1>
                <p><b>Device:</b> {st.session_state.device_for_otp}</p>
                <p><b>Valid:</b> {validity_hours} Hours</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.info("""
            📱 **Boss Ko Bhejne Ka Message:**
            
            App link kholen → Apna naam likhen → OTP enter karen → Done!
            """)
        
        # Live locations
        st.markdown("---")
        st.subheader("📍 Live Locations")
        
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
        
        all_locations = get_all_locations()
        
        if all_locations:
            for device, locs in all_locations.items():
                if locs:
                    latest = locs[-1]
                    
                    # Calculate timing
                    last_update = datetime.strptime(f"{latest['date']} {latest['time']}", 
                                                   "%Y-%m-%d %H:%M:%S")
                    seconds_ago = (datetime.now() - last_update).seconds
                    
                    if seconds_ago < 60:
                        status = "🟢 LIVE"
                        color = "#00cc00"
                    elif seconds_ago < 300:
                        status = f"🟡 {seconds_ago//60} min ago"
                        color = "#ff9900"
                    else:
                        status = f"🔴 {seconds_ago//60} min ago"
                        color = "#ff0000"
                    
                    # Display card
                    st.markdown(f"""
                    <div style="border-left: 5px solid {color}; padding: 10px; 
                              margin: 10px 0; background: #f9f9f9; border-radius: 5px;">
                        <h3>{status} | 📱 {device}</h3>
                        <p>📍 <b>{latest['lat']:.6f}, {latest['lon']:.6f}</b></p>
                        <p>🕐 {latest['date']} at {latest['time']}</p>
                        <p>📊 Updates: {len(locs)}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Map
            if MAP_OK:
                st.subheader("🗺️ Live Map")
                try:
                    # Get center
                    centers_lat = []
                    centers_lon = []
                    for locs in all_locations.values():
                        if locs:
                            l = locs[-1]
                            centers_lat.append(l['lat'])
                            centers_lon.append(l['lon'])
                    
                    if centers_lat:
                        map_center = [sum(centers_lat)/len(centers_lat), 
                                    sum(centers_lon)/len(centers_lon)]
                        m = folium.Map(location=map_center, zoom_start=15)
                        
                        for device, locs in all_locations.items():
                            if locs:
                                latest = locs[-1]
                                folium.Marker(
                                    [latest['lat'], latest['lon']],
                                    popup=f"<b>{device}</b><br>{latest['time']}",
                                    icon=folium.Icon(color='red', icon='user')
                                ).add_to(m)
                        
                        st_folium(m, width=800, height=500)
                except:
                    st.warning("Map unavailable")
        else:
            st.info("📡 Waiting for location data...")
        
        # Auto refresh
        time.sleep(15)
        st.rerun()

# Footer
st.markdown("---")
st.markdown("<p style='text-align:center;color:gray;'>🛡️ OTP-Based Auto Tracking | Perfect Working System</p>", 
           unsafe_allow_html=True)
