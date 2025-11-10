import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from supabase import create_client
import plotly.express as px

# ==============================
# ⚙️ CONFIGURATION
# ==============================
st.set_page_config(page_title="AI-Driven Farm Intelligence System", layout="wide")

SUPABASE_URL = "https://oxzrdgzvbmmxkdkxdofr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im94enJkZ3p2Ym1teGtka3hkb2ZyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTg5NTc1MywiZXhwIjoyMDc3NDcxNzUzfQ.HP6GXxS--OapGpKJBEkEfb51nNjrxuSeET0ii8DUAPM"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

today = datetime.now().strftime("%Y-%m-%d")
today_str = datetime.now().strftime("%A, %d %B %Y")

# ==============================
# 🧭 HEADER — PROJECT TITLE
# ==============================
st.markdown(
    """
    <h1 style='text-align:center; color:#2E8B57;'>🌾 AI-Driven Farm Intelligence System</h1>
    <h4 style='text-align:center; color:gray;'>Real-time Weather & Market Advisory for farm near by DINDI</h4>
    """,
    unsafe_allow_html=True,
)
st.markdown(f"<h5 style='text-align:center; color:#777;'>📅 {today_str}</h5>", unsafe_allow_html=True)
st.markdown("---")
# ==============================
# 🌾 COMMODITY OVERVIEW — 4 CARDS
# ==============================
st.markdown("## 🏷️ Today's Market Overview")

commodities = ["Chilli", "Cotton", "Mango", "Papaya"]
market_data = supabase.table("market_prices").select("*").eq("date", today).execute().data
if not market_data:
    st.warning("No market data found for today.")
    st.stop()

market_df = pd.DataFrame(market_data)
cards = st.columns(4)

for i, crop in enumerate(commodities):
    cdata = market_df[market_df["crop_name"] == crop]
    if not cdata.empty:
        highest_modal = cdata.loc[cdata["modal_price"].idxmax()]
        cards[i].markdown(
            f"""
            <div style="background-color:#F8F9FA;padding:15px;border-radius:10px;border:1px solid #ddd;text-align:center;">
                <h4 style="color:#2E8B57;">{crop}</h4>
                <p>🏪 <b>{highest_modal['market_name']}</b></p>
                <p>💰 Modal Price: <b>{highest_modal['modal_price']}</b></p>
                <p>📈 Max Price: <b>{highest_modal['max_price']}</b></p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        cards[i].warning(f"No data for {crop}")

st.markdown("---")

# ==============================
# 🌤️ WEATHER — HORIZONTAL ROW
# ==============================
weather_data = supabase.table("weather_data").select("*").eq("date", today).execute().data
if not weather_data:
    st.error("No weather data available for today.")
    st.stop()
weather = weather_data[0]

st.markdown("### 🌦️ Today's Weather Snapshot")

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Condition", weather["condition"])
col2.metric("Temp (°C)", weather["temperature_c"])
col3.metric("Humidity (%)", weather["humidity_percent"])
col4.metric("Rainfall (mm)", weather["rainfall_mm"])
col5.metric("Wind (km/h)", weather["wind_speed_kmph"])

# Weather prediction logic
temp = weather["temperature_c"]
humidity = weather["humidity_percent"]
rain = weather["rainfall_mm"]
wind = weather["wind_speed_kmph"]

if rain > 5:
    prediction = "🌧️ Expecting rain soon — avoid irrigation and pesticide spray."
elif temp > 35:
    prediction = "🔥 High temperature expected — irrigate early morning."
elif humidity > 80:
    prediction = "☁️ High humidity — fungal infection risk, inspect crops."
elif wind > 20:
    prediction = "💨 Strong winds — avoid spraying today."
else:
    prediction = "🌤️ Stable weather — good for normal farm operations."

col6.markdown(
    f"<div style='background-color:#E6F4EA;padding:10px;border-radius:10px;text-align:center;font-size:15px;'>{prediction}</div>",
    unsafe_allow_html=True,
)

st.markdown("---")



# ==============================
# 🎯 COMMODITY INSIGHTS (RADIO)
# ==============================
st.markdown("## 📊 Crop-wise Trends & Advisory")

selected_crop = st.radio("Select Crop", commodities, horizontal=True)

crop_data = market_df[market_df["crop_name"] == selected_crop]
if crop_data.empty:
    st.warning(f"No data found for {selected_crop}.")
    st.stop()

# ==============================
# 💹 PRICE TABLE AND TREND CHART
# ==============================
trend_days = 3 if selected_crop in ["Mango", "Papaya"] else 7
dates = [datetime.now() - timedelta(days=i) for i in range(trend_days)][::-1]
trend_prices = np.random.randint(6000, 15000, size=trend_days)
trend_df = pd.DataFrame({"Date": dates, "Modal Price": trend_prices})

col7, col8 = st.columns([1.5, 1])

with col7:
    st.markdown(f"### 💰 {selected_crop} Market Prices (Today)")
    st.dataframe(crop_data[["market_name", "min_price", "modal_price", "max_price"]], use_container_width=True)

with col8:
    st.markdown(f"### 📈 {selected_crop} Price Trend ({trend_days} Days)")
    fig = px.line(trend_df, x="Date", y="Modal Price", markers=True)
    fig.update_layout(height=250, margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig, use_container_width=True)

# ==============================
# 🧠 AI-BASED SUGGESTION
# ==============================
st.markdown("### 🤖 AI Price Recommendation")

avg_price = trend_df["Modal Price"].iloc[-1]
if selected_crop in ["Mango", "Papaya"]:
    if avg_price < 4000:
        st.warning("📉 Prices dropping — sell immediately (short shelf life).")
    else:
        st.success("📈 Prices stable — sell within 1–2 days.")
else:
    if avg_price < 7000:
        st.warning("📉 Prices decreasing — avoid holding stock.")
    elif avg_price > 12000:
        st.success("📈 Prices rising — hold for better returns.")
    else:
        st.info("⚖️ Stable market — monitor next few days.")

# ==============================
# 🖋️ FOOTER
# ==============================
st.markdown("---")
st.markdown(
    "<h5 style='text-align:center; color:gray;'>Designed & Developed by <b>Kareem</b> 🌿</h5>",
    unsafe_allow_html=True,
)
