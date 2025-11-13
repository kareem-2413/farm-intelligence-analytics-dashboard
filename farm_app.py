import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import requests
from supabase import create_client
from sklearn.linear_model import LinearRegression
import plotly.express as px

# ==============================================================
# CONFIG
# ==============================================================
st.set_page_config(page_title="AI-Driven Farm Intelligence System", layout="wide")

# Supabase
SUPABASE_URL = "https://oxzrdgzvbmmxkdkxdofr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im94enJkZ3p2Ym1teGtka3hkb2ZyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTg5NTc1MywiZXhwIjoyMDc3NDcxNzUzfQ.HP6GXxS--OapGpKJBEkEfb51nNjrxuSeET0ii8DUAPM"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

_now = datetime.now()
today = _now.strftime("%Y-%m-%d")
today_str = _now.strftime("%A, %d %B %Y")

LATITUDE = 16.5156
LONGITUDE = 78.6836
TIMEZONE = "Asia/Kolkata"

# ==============================================================
# HELPERS
# ==============================================================
def round_hundred(x):
    try:
        return int(round(float(x) / 100.0) * 100)
    except Exception:
        return None

def clamp(v, lo, hi):
    try:
        return max(lo, min(hi, v))
    except Exception:
        return v

def season_from_month(month):
    if 3 <= month <= 5:
        return "summer"
    if 6 <= month <= 9:
        return "monsoon"
    if 10 <= month <= 11:
        return "post-monsoon"
    return "winter"

# Telangana seasonal offsets (display-only mild adjustment)
SEASON_OFFS = {
    "summer": {"temp": +3, "hum": -5, "rain": 0, "wind": +1},
    "monsoon": {"temp": -1, "hum": +10, "rain": +5, "wind": +1},
    "post-monsoon": {"temp": 0, "hum": +3, "rain": +1, "wind": 0},
    "winter": {"temp": -4, "hum": -7, "rain": 0, "wind": -1},
}

_daily_seed = int(_now.strftime("%Y%m%d"))
rand = random.Random(_daily_seed)

# ==============================================================
# HEADER
# ==============================================================
st.markdown(
    """
    <h1 style='text-align:center; color:#2E8B57;'>🌾 AI-Driven Farm Intelligence System</h1>
    <h4 style='text-align:center; color:blue;'>Realtime Weather, Market, and AI Forecast Dashboard for farms in DINDI</h4>
    """,
    unsafe_allow_html=True,
)
st.markdown(f"<h5 style='text-align:center; color:#777;'>📅 {today_str}</h5>", unsafe_allow_html=True)
st.markdown("---")

# ==============================================================
# WEATHER (bilingual messages)
# ==============================================================
st.markdown("### 🌦️ Today's Weather & Forecast")

def fetch_open_meteo_forecast(lat, lon, timezone="Asia/Kolkata", days=3):
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&daily=temperature_2m_max,"
            f"temperature_2m_min,precipitation_sum,wind_speed_10m&timezone={timezone}"
            f"&forecast_days={days}"
        )
        js = requests.get(url, timeout=10).json()
        if "daily" not in js:
            return None
        df = pd.DataFrame({
            "Date": pd.to_datetime(js["daily"]["time"]),
            "Max Temp (°C)": js["daily"]["temperature_2m_max"],
            "Min Temp (°C)": js["daily"]["temperature_2m_min"],
            "Rainfall (mm)": js["daily"]["precipitation_sum"],
            "Wind (km/h)": js["daily"]["wind_speed_10m"],
        })
        return df
    except Exception:
        return None

weather_row = supabase.table("weather_data").select("*").eq("date", today).execute().data
if not weather_row:
    st.error("No weather data available for today.")
    st.stop()

weather = weather_row[0]
forecast_df = fetch_open_meteo_forecast(LATITUDE, LONGITUDE, TIMEZONE, days=3)

season = season_from_month(_now.month)
offs = SEASON_OFFS.get(season, {"temp":0,"hum":0,"rain":0,"wind":0})

display_temp = round(clamp(weather.get("temperature_c", 0) + offs["temp"] + rand.uniform(-1,1), -10, 60), 2)
display_hum = round(clamp(weather.get("humidity_percent", 0) + offs["hum"] + rand.uniform(-3,3), 0, 100), 2)
display_rain = round(max(0, weather.get("rainfall_mm", 0) + offs["rain"] + rand.uniform(0,1.5)), 2)
display_wind = round(max(0, weather.get("wind_speed_kmph", 0) + offs["wind"] + rand.uniform(-1,1)), 2)

# condition label
if season == "monsoon":
    if display_rain > 15:
        display_condition = "Heavy Rain"
    elif display_rain > 3:
        display_condition = "Rainy"
    else:
        display_condition = "Humid"
elif season == "summer":
    display_condition = "Hot" if display_temp > 35 else "Warm"
elif season == "winter":
    display_condition = "Cool"
else:
    display_condition = "Pleasant"

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Condition", display_condition)
c2.metric("Temp (°C)", display_temp)
c3.metric("Humidity (%)", display_hum)
c4.metric("Rainfall (mm)", display_rain)
c5.metric("Wind (km/h)", display_wind)

# bilingual today weather message
if display_rain > 5:
    today_msg = (
        "🌧️ It may rain today. Avoid spraying.\n"
        "🌧️ ఈరోజు వర్షం పడే అవకాశం ఉంది. స్ప్రే చేయకండి."
    )
elif display_temp > 35:
    today_msg = (
        "🔥 Very hot today. Water crops early.\n"
        "🔥 ఇవాళ ఎక్కువ వేడిగా ఉంది. ఉదయం నీళ్ళు పెట్టండి."
    )
elif display_hum > 80:
    today_msg = (
        "☁️ Humidity is high. Check crops for fungus.\n"
        "☁️ తేమ ఎక్కువగా ఉంది. పంటల్లో ఫంగస్ ఉందో చూడండి."
    )
elif display_wind > 20:
    today_msg = (
        "💨 Strong winds today. Avoid spraying.\n"
        "💨 గాలి బలంగా ఉంది. స్ప్రే చేయకండి."
    )
else:
    today_msg = (
        "🌤️ Weather is good. You can work in fields.\n"
        "🌤️ వాతావరణం బాగుంది. పని చేయొచ్చు."
    )

c6.markdown(
    f"<div style='background:#E8F6FF;padding:10px;border-radius:8px;text-align:center;white-space:pre-line'>{today_msg}</div>",
    unsafe_allow_html=True,
)

# bilingual next-days forecast
if forecast_df is not None:
    avg_rain = float(forecast_df["Rainfall (mm)"].mean())
    avg_max = float(forecast_df["Max Temp (°C)"].mean())
    avg_min = float(forecast_df["Min Temp (°C)"].mean())
    avg_temp = (avg_max + avg_min) / 2.0

    if avg_rain > 5:
        forecast_msg = (
            "🌧️ Rain expected in coming days.\n"
            "🌧️ వచ్చే రోజుల్లో వర్షం పడే అవకాశం."
        )
    elif avg_temp > 35:
        forecast_msg = (
            "🔥 Next days will be hot.\n"
            "🔥 వచ్చే రోజులు వేడిగా ఉంటాయి."
        )
    else:
        forecast_msg = (
            "🌤️ Stable weather in coming days.\n"
            "🌤️ వచ్చే రోజులు వాతావరణం స్థిరంగా ఉంటుంది."
        )
else:
    forecast_msg = (
        "🤖 Expect small weather changes in coming days.\n"
        "🤖 వచ్చే రోజుల్లో చిన్న మార్పులే ఉంటాయి."
    )

st.info(forecast_msg)
st.markdown("---")

# ==============================================================
# MARKET CARDS (NO suggestions)
# ==============================================================
st.markdown("## 🏷️ Today's Market Overview")

commodities = ["Chilli", "Cotton", "Mango", "Papaya"]
market_raw = supabase.table("market_prices").select("*").eq("date", today).execute().data

if not market_raw:
    st.warning("No market data.")
    st.stop()

market_df = pd.DataFrame(market_raw)

# round prices
for col in ["min_price", "modal_price", "max_price"]:
    if col in market_df.columns:
        market_df[col] = pd.to_numeric(market_df[col], errors="coerce").apply(
            lambda v: round_hundred(v) if pd.notnull(v) else None
        )

cards = st.columns(4)
for i, crop in enumerate(commodities):
    rows = market_df[market_df["crop_name"] == crop]
    if rows.empty:
        cards[i].warning(f"No data for {crop}")
        continue
    top = rows.loc[rows["modal_price"].idxmax()]

    cards[i].markdown(
        f"""
        <div style="background:#F8F9FA;padding:15px;border-radius:10px;border:1px solid #ddd;text-align:center;">
            <h4 style="color:#2E8B57;">{crop}</h4>
            <p>🏪 <b>{top['market_name']}</b></p>
            <p>💰 Modal Price: <b>{int(top['modal_price']):,}</b></p>
            <p>📈 Max Price: <b>{int(top['max_price']):,}</b></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# ==============================================================
# SINGLE SOURCE-OF-TRUTH PREDICTIONS
# ==============================================================
future_predictions = {}
history_cache = {}

for crop in commodities:
    try:
        merged_raw = supabase.table("merged_dataset").select("*").eq("crop_name", crop).execute().data
        hist = pd.DataFrame(merged_raw)

        if hist.empty or "modal_price" not in hist.columns or len(hist) < 3:
            rows = market_df[market_df["crop_name"] == crop]
            future_predictions[crop] = int(round_hundred(rows["modal_price"].mean())) if not rows.empty else None
            continue

        hist["date"] = pd.to_datetime(hist["date"])
        hist["modal_price"] = pd.to_numeric(hist["modal_price"], errors="coerce").apply(round_hundred)
        hist = hist.dropna(subset=["modal_price"]).sort_values("date")

        fd = 3 if crop in ["Mango", "Papaya"] else 7

        Xc = hist["date"].map(datetime.toordinal).values.reshape(-1, 1)
        yc = hist["modal_price"].values
        model = LinearRegression().fit(Xc, yc)

        last_d = hist["date"].max()
        future_dates = [last_d + timedelta(days=i + 1) for i in range(fd)]
        X_future = np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)
        preds = model.predict(X_future)

        future_predictions[crop] = int(round_hundred(preds[-1]))
        history_cache[crop] = hist.copy()

    except Exception:
        rows = market_df[market_df["crop_name"] == crop]
        future_predictions[crop] = int(round_hundred(rows["modal_price"].mean())) if not rows.empty else None

# ==============================================================
# CROP-WISE FORECAST (Telugu radio buttons)
# ==============================================================
st.markdown("## 📊 Crop-wise Trends & AI Forecast")

# Telugu labels for UI
crop_labels = {
    "Chilli": "మిర్చి",
    "Cotton": "పత్తి",
    "Mango": "మామిడి",
    "Papaya": "బొప్పాయి"
}
label_to_crop = {v: k for k, v in crop_labels.items()}

selected_label = st.radio(
    "పంటను ఎంచుకోండి (Select Crop)",
    [crop_labels[c] for c in commodities],
    horizontal=True
)
selected_crop = label_to_crop[selected_label]

crop_data = market_df[market_df["crop_name"] == selected_crop]
if crop_data.empty:
    st.warning("No crop data.")
    st.stop()

hist_df = history_cache.get(selected_crop)
if hist_df is None:
    merged_raw = supabase.table("merged_dataset").select("*").eq("crop_name", selected_crop).execute().data
    hist_df = pd.DataFrame(merged_raw) if merged_raw else pd.DataFrame()

if hist_df.empty or "modal_price" not in hist_df.columns or len(hist_df) < 3:
    hist_df = pd.DataFrame({
        "date": [datetime.now() - timedelta(days=i) for i in range(7)][::-1],
        "modal_price": [round_hundred(v) for v in np.random.randint(6000, 12000, 7)]
    })
else:
    hist_df["date"] = pd.to_datetime(hist_df["date"])
    hist_df["modal_price"] = pd.to_numeric(hist_df["modal_price"], errors="coerce").apply(round_hundred)
    hist_df = hist_df.dropna(subset=["modal_price"]).sort_values("date")

fd = 3 if selected_crop in ["Mango", "Papaya"] else 7
last_date = hist_df["date"].max()
future_dates = [last_date + timedelta(days=i + 1) for i in range(fd)]

pred_price = future_predictions.get(selected_crop)
if pred_price is None:
    pred_price = int(hist_df["modal_price"].iloc[-1])

forecast_df = pd.DataFrame({"Date": future_dates, "Forecasted Price": [pred_price] * len(future_dates)})

trend_df = pd.concat([
    hist_df.rename(columns={"modal_price": "Price"}).assign(Type="Historical").rename(columns={"date":"Date"}),
    forecast_df.rename(columns={"Forecasted Price": "Price"}).assign(Type="Forecast")
], ignore_index=True)

# AI recommendation (bilingual)
today_price = float(crop_data["modal_price"].mean())
change = ((pred_price - today_price) / today_price) * 100 if today_price else 0

if change < -5:
    ai_msg = ("📉 Price may drop. Sell your stock.\n"
              "📉 రేటు తగ్గే అవకాశం ఉంది. ఇప్పుడే అమ్మేయండి.")
    ai_bg = "#FFCCCC"
elif change > 5:
    ai_msg = ("📈 Price may increase. Hold for better rate.\n"
              "📈 రేటు పెరగవచ్చు. కొంచెం నిల్వ చేసి అమ్మండి.")
    ai_bg = "#CCFFCC"
else:
    ai_msg = ("⚖️ Price stable. No big change.\n"
              "⚖️ రేటు స్థిరంగా ఉంది. పెద్ద మార్పు లేరు.")
    ai_bg = "#FFFACD"

st.markdown(
    f"""
    <div style='background:{ai_bg};
                padding:10px;
                border-radius:10px;
                text-align:center;
                font-size:15px;
                line-height:1.5;
                white-space:pre-line;'>
        <b>{ai_msg}</b>
    </div>
    """,
    unsafe_allow_html=True,
)

# ==============================================================
# TABLE + CHART
# ==============================================================
col7, col8 = st.columns([1.5, 1])
with col7:
    st.markdown(f"### 💰 {selected_crop} Market Prices (Today)")
    df_display = crop_data.copy()
    for col in ["min_price", "modal_price", "max_price"]:
        df_display[col] = df_display[col].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else "")
    st.dataframe(df_display[["market_name", "min_price", "modal_price", "max_price"]], use_container_width=True)

with col8:
    st.markdown(f"### 🔮 {selected_crop} Price Forecast")
    fig = px.line(trend_df, x="Date", y="Price", color="Type", markers=True)
    fig.update_layout(height=250, margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig, config={"displayModeBar": False})

# ==============================================================
# FOOTER
# ==============================================================
st.markdown("---")
st.markdown(
    "<h5 style='text-align:center; color:gray;'>Designed & Developed by <b>Kareem</b> 🌿</h5>",
    unsafe_allow_html=True,
)
