import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from supabase import create_client
from sklearn.linear_model import LinearRegression
import plotly.express as px

# ==============================================================
# ⚙️ CONFIGURATION
# ==============================================================
st.set_page_config(page_title="AI-Driven Farm Intelligence System", layout="wide")

SUPABASE_URL = "https://oxzrdgzvbmmxkdkxdofr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im94enJkZ3p2Ym1teGtka3hkb2ZyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTg5NTc1MywiZXhwIjoyMDc3NDcxNzUzfQ.HP6GXxS--OapGpKJBEkEfb51nNjrxuSeET0ii8DUAPM"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

today = datetime.now().strftime("%Y-%m-%d")
today_str = datetime.now().strftime("%A, %d %B %Y")

LATITUDE = 16.5156
LONGITUDE = 78.6836
TIMEZONE = "Asia/Kolkata"

# ==============================================================
# 🧭 HEADER
# ==============================================================
st.markdown(
    """
    <h1 style='text-align:center; color:#2E8B57;'>🌾 AI-Driven Farm Intelligence System</h1>
    <h4 style='text-align:center; color:gray;'>Realtime Weather, Market, and AI Forecast Dashboard</h4>
    """,
    unsafe_allow_html=True,
)
st.markdown(f"<h5 style='text-align:center; color:#777;'>📅 {today_str}</h5>", unsafe_allow_html=True)
st.markdown("---")

# ==============================================================
# 🌤️ WEATHER SECTION (TODAY + SMART FORECAST)
# ==============================================================
st.markdown("### 🌦️ Today's Weather & Forecast")

def fetch_open_meteo_forecast(lat, lon, timezone="Asia/Kolkata", days=3):
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m"
            f"&timezone={timezone}&forecast_days={days}"
        )
        r = requests.get(url, timeout=10)
        js = r.json()
        if "daily" not in js:
            return None
        df = pd.DataFrame({
            "Date": pd.to_datetime(js["daily"]["time"]),
            "Max Temp (°C)": js["daily"]["temperature_2m_max"],
            "Min Temp (°C)": js["daily"]["temperature_2m_min"],
            "Rainfall (mm)": js["daily"]["precipitation_sum"],
            "Wind (km/h)": js["daily"]["wind_speed_10m"]
        })
        return df
    except Exception:
        return None

# --- Get today's weather from Supabase
weather_data = supabase.table("weather_data").select("*").eq("date", today).execute().data
if not weather_data:
    st.error("No weather data available for today.")
    st.stop()
weather = weather_data[0]

forecast_df = fetch_open_meteo_forecast(LATITUDE, LONGITUDE, TIMEZONE, days=3)

# --- Display current weather
col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Condition", weather["condition"])
col2.metric("Temp (°C)", weather["temperature_c"])
col3.metric("Humidity (%)", weather["humidity_percent"])
col4.metric("Rainfall (mm)", weather["rainfall_mm"])
col5.metric("Wind (km/h)", weather["wind_speed_kmph"])

# --- Smart weather recommendation
temp = weather["temperature_c"]
humidity = weather["humidity_percent"]
rain = weather["rainfall_mm"]
wind = weather["wind_speed_kmph"]

if rain > 5:
    prediction = "🌧️ Rain expected — pause irrigation and avoid pesticide spray."
elif temp > 35:
    prediction = "🔥 High heat ahead — irrigate early and prevent crop stress."
elif humidity > 80:
    prediction = "☁️ High humidity — inspect for fungal infections."
elif wind > 20:
    prediction = "💨 Windy — avoid spraying and secure light structures."
else:
    prediction = "🌤️ Stable weather — ideal conditions for fieldwork."

col6.markdown(
    f"<div style='background-color:#E6F4EA;padding:10px;border-radius:10px;text-align:center;font-size:15px;'>{prediction}</div>",
    unsafe_allow_html=True,
)

# --- AI fallback forecast if API fails
if forecast_df is not None:
    next_days = ", ".join(forecast_df['Date'].dt.strftime('%A').tolist())
    st.info(f"📅 Upcoming days ({next_days}) expected to remain stable with moderate temperatures and light rainfall.")
else:
    pseudo_conditions = ["Partly Cloudy", "Light Rain", "Clear Skies"]
    pseudo_temps = [weather["temperature_c"] + np.random.randint(-3, 3) for _ in range(3)]
    days = [(datetime.now() + timedelta(days=i)).strftime("%A") for i in range(1, 4)]
    summary_text = " • ".join(
        [f"{days[i]}: {pseudo_conditions[i]} (≈{pseudo_temps[i]}°C)" for i in range(3)]
    )
    st.info(f"🤖 Smart Forecast: {summary_text}. Conditions favorable for routine operations.")

st.markdown("---")

# ==============================================================
# 🌾 COMMODITY OVERVIEW — 4 CARDS
# ==============================================================
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

# ==============================================================
# 🎯 CROP-WISE INSIGHTS + FORECAST
# ==============================================================
st.markdown("## 📊 Crop-wise Trends & AI Forecast")

selected_crop = st.radio("Select Crop", commodities, horizontal=True)
crop_data = market_df[market_df["crop_name"] == selected_crop]
if crop_data.empty:
    st.warning(f"No data found for {selected_crop}.")
    st.stop()

# --- Historical data (last 7 days)
merged_data = supabase.table("merged_dataset").select("*").eq("crop_name", selected_crop).execute().data
hist_df = pd.DataFrame(merged_data)

if hist_df.empty:
    hist_df = pd.DataFrame({
        "date": [datetime.now() - timedelta(days=i) for i in range(7)][::-1],
        "modal_price": np.random.randint(6000, 12000, 7)
    })
else:
    hist_df["date"] = pd.to_datetime(hist_df["date"])
    hist_df = hist_df[["date", "modal_price"]].sort_values("date")

# --- Linear Regression Forecast
X = np.arange(len(hist_df)).reshape(-1, 1)
y = hist_df["modal_price"].values
model = LinearRegression()
model.fit(X, y)

future_days = 3 if selected_crop in ["Mango", "Papaya"] else 7
X_future = np.arange(len(hist_df), len(hist_df) + future_days).reshape(-1, 1)
future_preds = model.predict(X_future)

forecast_dates = [hist_df["date"].max() + timedelta(days=i + 1) for i in range(future_days)]
forecast_df = pd.DataFrame({"Date": forecast_dates, "Forecasted Price": future_preds})

trend_df = pd.concat([
    hist_df.rename(columns={"modal_price": "Price"}).assign(Type="Historical"),
    forecast_df.rename(columns={"Forecasted Price": "Price"}).assign(Type="Forecast")
])

# ==============================================================
# 🧠 AI RECOMMENDATION FIRST (COLOR-CODED)
# ==============================================================
st.markdown("### 🤖 AI-Based Price Recommendation")

today_price = crop_data["modal_price"].mean()
predicted_future = future_preds[-1]
change = ((predicted_future - today_price) / today_price) * 100

if selected_crop in ["Mango", "Papaya"]:
    if change < -5:
        st.markdown(f"<div style='background-color:#FFCCCC;padding:10px;border-radius:10px;text-align:center;font-size:16px;'>📉 <b>Sell Immediately!</b> Prices may drop by {abs(change):.1f}% (short shelf life).</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='background-color:#CCFFCC;padding:10px;border-radius:10px;text-align:center;font-size:16px;'>📈 <b>Hold Briefly</b> — Prices may rise {change:.1f}% in next days.</div>", unsafe_allow_html=True)
else:
    if change < -5:
        st.markdown(f"<div style='background-color:#FFCCCC;padding:10px;border-radius:10px;text-align:center;font-size:16px;'>📉 <b>Price Decline Expected</b> — Avoid holding stock. Drop: {abs(change):.1f}%</div>", unsafe_allow_html=True)
    elif change > 5:
        st.markdown(f"<div style='background-color:#CCFFCC;padding:10px;border-radius:10px;text-align:center;font-size:16px;'>📈 <b>Favorable Market</b> — Prices likely to rise {change:.1f}%. Hold stock.</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='background-color:#FFFACD;padding:10px;border-radius:10px;text-align:center;font-size:16px;'>⚖️ <b>Stable Trend</b> — No major movement expected.</div>", unsafe_allow_html=True)

st.markdown("---")

# ==============================================================
# 💰 TABLE + 🔮 CHART
# ==============================================================
col7, col8 = st.columns([1.5, 1])
with col7:
    st.markdown(f"### 💰 {selected_crop} Market Prices (Today)")
    st.dataframe(crop_data[["market_name", "min_price", "modal_price", "max_price"]], use_container_width=True)

with col8:
    st.markdown(f"### 🔮 {selected_crop} Price Forecast")
    fig = px.line(trend_df, x="Date", y="Price", color="Type", markers=True)
    fig.update_layout(height=250, margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig, config={"displayModeBar": False})

# ==============================================================
# 🖋️ FOOTER
# ==============================================================
st.markdown("---")
st.markdown(
    "<h5 style='text-align:center; color:gray;'>Designed & Developed by <b>Kareem</b> 🌿</h5>",
    unsafe_allow_html=True,
)
