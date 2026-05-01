import streamlit as st
import json
import os
from datetime import datetime, timedelta
import random
import time

st.set_page_config(page_title="Security Tracker", page_icon="🛡️", layout="wide")

LOCATION_FILE = "locations.json"
OTP_FILE = "otp_store.json"

if 'admin_login' not in st.session_state:
    st.session_state.admin_login = False
if 'show_otp' not in st.session_state:
    st.session_state.show_otp = None
if 'device_for_otp' not in st.session_state:
    st.session_state.device_for_otp = None

def generate_otp():
    return str(random.randint(100000, 999999))

def save_otp_to_file(device_id, otp, hours=24):
    try:
        data = {}
        if os.path.exists(OTP_FILE):
            with open(OTP_FILE, 'r') as f:
                data = json.load(f)
        data[device_id] = {
            "otp": otp,
            "expires": (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(OTP_FILE, 'w') as f:
            json.dump(data, f)
        return True
    except:
        return False

def check_otp(device_id, otp_entered):
    try:
        if not os.path.exists(OTP_FILE):
            return False
        with open(OTP_FILE, 'r') as f:
            data = json.load(f)
        if device_id in data and data[device_id]['otp'] == otp_entered:
            return True
        return False
    except:
        return False

def save_location_data(device_id, lat, lon):
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
        if len(data[device_id]) > 500:
            data[device_id] = data[device_id][-500:]
        with open(LOCATION_FILE, 'w') as f:
            json.dump(data, f)
        return True
    except:
        return False

def get_all_locations():
    if os.path.exists(LOCATION_FILE):
        with open(LOCATION_FILE, 'r') as f:
            return json.load(f)
    return {}

# ============ MAIN ============
st.title("🛡️ Security Location Tracker")
st.markdown("---")

url_params = st.query_params

tab1, tab2 = st.tabs(["📱 Boss View", "🔐 Admin Panel"])

# ============ BOSS TAB ============
with tab1:
    st.header("📍 Share Your Location")
    
    if 'device' in url_params and 'otp' in url_params:
        device = url_params['device']
        otp = url_params['otp']
        
        if check_otp(device, otp):
            
            if 'lat' in url_params and 'lon' in url_params:
                save_location_data(device, url_params['lat'], url_params['lon'])
                st.success(f"✅ Location Saved!")
                st.metric("Latitude", url_params['lat'])
                st.metric("Longitude", url_params['lon'])
            
            st.success(f"✅ Connected - {device}")
            
            st.markdown("---")
            st.subheader("📤 SEND LOCATION (One Click)")
            
            # SIMPLE BUTTON - No complex JavaScript
            if st.button("📍 SEND MY LOCATION NOW", type="primary", use_container_width=True):
                st.html("""
                <script>
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(function(pos) {
                        var lat = pos.coords.latitude;
                        var lon = pos.coords.longitude;
                        var base = window.location.href.split('?')[0];
                        var params = new URLSearchParams(window.location.search);
                        var device = params.get('device');
                        var otp = params.get('otp');
                        window.location.href = base + '?device=' + device + '&otp=' + otp + '&lat=' + lat + '&lon=' + lon;
                    });
                } else {
                    alert('GPS not available');
                }
                </script>
                """)
                st.info("🔄 Getting GPS location...")
            
            st.markdown("---")
            st.subheader("📋 Manual Entry (Backup)")
            
            col1, col2 = st.columns(2)
            with col1:
                manual_lat = st.text_input("Latitude:", key="lat_input")
            with col2:
                manual_lon = st.text_input("Longitude:", key="lon_input")
            
            if st.button("📤 Send Manual", use_container_width=True):
                if manual_lat and manual_lon:
                    save_location_data(device, manual_lat, manual_lon)
                    st.success("✅ Sent!")
                    st.rerun()
            
        else:
            st.error("❌ Invalid OTP")
    
    # OTP Form
    st.markdown("---")
    with st.form("boss_form"):
        st.subheader("🔢 Enter OTP")
        device_input = st.text_input("Your Name:", "Sarah")
        otp_input = st.text_input("OTP:", max_chars=6)
        
        if st.form_submit_button("✅ Start", use_container_width=True):
            if check_otp(device_input, otp_input):
                st.query_params['device'] = device_input
                st.query_params['otp'] = otp_input
                st.rerun()
            else:
                st.error("Wrong OTP!")

# ============ ADMIN TAB ============
with tab2:
    st.header("🔐 Admin Panel")
    
    if not st.session_state.admin_login:
        password = st.text_input("Password:", type="password")
        if st.button("🔑 Login", use_container_width=True):
            if password == "Secure@2024":
                st.session_state.admin_login = True
                st.rerun()
            else:
                st.error("Wrong!")
    else:
        st.success("✅ Admin Access")
        
        st.subheader("🎫 Generate OTP")
        
        col1, col2 = st.columns(2)
        with col1:
            device_name = st.text_input("Device:", "Sarah")
        with col2:
            validity = st.selectbox("Valid:", [6, 12, 24, 48], format_func=lambda x: f"{x}hrs")
        
        if st.button("🔢 Generate OTP", type="primary", use_container_width=True):
            otp = generate_otp()
            save_otp_to_file(device_name, otp, validity)
            st.session_state.show_otp = otp
            st.session_state.device_for_otp = device_name
        
        if st.session_state.show_otp:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea, #764ba2); 
                        padding: 20px; border-radius: 10px; color: white; text-align: center;">
                <h1 style="font-size: 50px; letter-spacing: 10px;">{st.session_state.show_otp}</h1>
                <p><b>Device:</b> {st.session_state.device_for_otp}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("📍 Live Locations")
        
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
        
        locations = get_all_locations()
        
        if locations:
            for device, locs in locations.items():
                if locs:
                    latest = locs[-1]
                    st.markdown(f"""
                    <div style="border: 2px solid #4CAF50; padding: 15px; border-radius: 10px; margin: 10px 0;">
                        <h3>📱 {device}</h3>
                        <p><b>📍 {latest['lat']}, {latest['lon']}</b></p>
                        <p>🕐 {latest['date']} {latest['time']}</p>
                        <p>📊 Updates: {len(locs)}</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Waiting for location...")
        
        time.sleep(10)
        st.rerun()

st.markdown("---")
st.markdown("<p style='text-align:center;'>🛡️ Security Tracking System</p>", unsafe_allow_html=True)
