# ============================================================
# 🌦️🌾 AGRI INTELLIGENCE FULL PIPELINE
# (Weather Fetch + Market Generation + Data Merge)
# ============================================================

import random
import statistics
import requests
import pandas as pd
from datetime import datetime, date
from supabase import create_client, Client

# --- 1️⃣ CONFIGURATION ---
SUPABASE_URL = "https://oxzrdgzvbmmxkdkxdofr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im94enJkZ3p2Ym1teGtka3hkb2ZyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTg5NTc1MywiZXhwIjoyMDc3NDcxNzUzfQ.HP6GXxS--OapGpKJBEkEfb51nNjrxuSeET0ii8DUAPM"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
LATITUDE, LONGITUDE = 16.5156, 78.6836
TIMEZONE = "Asia/Kolkata"
today = datetime.now().strftime("%Y-%m-%d")

print(f"\n🌾 Running Agri Intelligence Full Pipeline for {today}\n")

# ============================================================
# PART A — WEATHER DATA FETCH
# ============================================================
try:
    print("⛅ Fetching weather data...")
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={LATITUDE}&longitude={LONGITUDE}"
        f"&hourly=temperature_2m,relative_humidity_2m,rain,wind_speed_10m"
        f"&timezone={TIMEZONE}"
    )

    data = requests.get(url).json()
    hourly_temp = data["hourly"]["temperature_2m"]
    hourly_humidity = data["hourly"]["relative_humidity_2m"]
    hourly_rain = data["hourly"]["rain"]
    hourly_wind = data["hourly"]["wind_speed_10m"]

    daily_temp = round(statistics.mean(hourly_temp), 2)
    daily_humidity = round(statistics.mean(hourly_humidity), 2)
    daily_rainfall = round(sum(hourly_rain), 2)
    daily_wind = round(statistics.mean(hourly_wind), 2)

    if daily_rainfall > 5:
        condition = "Rainy"
    elif daily_humidity > 80 and daily_temp < 25:
        condition = "Cloudy"
    elif daily_temp > 35:
        condition = "Hot"
    elif daily_wind > 20:
        condition = "Windy"
    else:
        condition = "Clear"

    weather_record = {
        "date": today,
        "location": "Farm Location",
        "temperature_c": daily_temp,
        "humidity_percent": daily_humidity,
        "rainfall_mm": daily_rainfall,
        "wind_speed_kmph": daily_wind,
        "condition": condition,
    }

    existing_weather = supabase.table("weather_data").select("id").eq("date", today).execute()
    if not existing_weather.data:
        supabase.table("weather_data").insert(weather_record).execute()
        print("✅ Weather data uploaded.")
    else:
        print("⚠️ Weather data already exists — skipped.")

except Exception as e:
    print(f"❌ Weather fetch failed: {e}")

# ============================================================
# PART B — MARKET DATA GENERATION
# ============================================================
try:
    print("\n📊 Generating synthetic market data...")

    market_map = {
        "Gudimalkapur APMC": ["Cotton", "Mango", "Papaya"],
        "Hyderabad": ["Mango", "Papaya"],
        "Kothapet Fruit Market": ["Mango", "Papaya"],
        "Malakpet Mandi": ["Cotton", "Chilli"],
        "Nalgonda": ["Cotton", "Chilli"],
        "Nalgonda APMC": ["Cotton", "Chilli"],
        "Suryapet": ["Cotton", "Chilli"],
        "Suryapet APMC": ["Cotton", "Chilli"],
    }

    price_ranges = {
        "Chilli": {"min": (8000, 12000), "modal": (12000, 15000), "max": (15000, 20000)},
        "Cotton": {"min": (5000, 7500), "modal": (6000, 8000), "max": (7500, 9000)},
        "Mango": {"min": (4000, 6000), "modal": (5000, 8500), "max": (9000, 12000)},
        "Papaya": {"min": (1000, 1500), "modal": (2500, 3500), "max": (3500, 4000)},
    }

    records = []
    for market, crops in market_map.items():
        for crop in crops:
            rng = price_ranges[crop]
            min_p = random.randint(*rng["min"])
            modal_p = random.randint(*rng["modal"])
            max_p = random.randint(*rng["max"])
            modal_p = min(max(modal_p, min_p + 500), max_p - 500)
            records.append({
                "date": today,
                "crop_name": crop,
                "market_name": market,
                "min_price": float(min_p),
                "modal_price": float(modal_p),
                "max_price": float(max_p)
            })

    existing_market = supabase.table("market_prices").select("id").eq("date", today).execute()
    if not existing_market.data:
        supabase.table("market_prices").insert(records).execute()
        print(f"✅ Inserted {len(records)} market records.")
    else:
        print("⚠️ Market data already exists — skipped.")

except Exception as e:
    print(f"❌ Market data error: {e}")

# ============================================================
# PART C — MERGE WEATHER + MARKET DATA
# ============================================================
try:
    print("\n🔗 Merging weather and market data...")

    weather = supabase.table("weather_data").select("*").eq("date", today).execute().data
    if not weather:
        raise ValueError("No weather data found.")
    weather = weather[0]

    market = supabase.table("market_prices").select("*").eq("date", today).execute().data
    if not market:
        raise ValueError("No market data found.")

    market_df = pd.DataFrame(market)
    merged_records = [
        {
            "date": today,
            "market_name": row["market_name"],
            "crop_name": row["crop_name"],
            "min_price": row["min_price"],
            "max_price": row["max_price"],
            "modal_price": row["modal_price"],
            "temperature_c": weather["temperature_c"],
            "humidity_percent": weather["humidity_percent"],
            "rainfall_mm": weather["rainfall_mm"],
            "wind_speed_kmph": weather["wind_speed_kmph"],
            "condition": weather["condition"]
        }
        for _, row in market_df.iterrows()
    ]

    existing_merge = supabase.table("merged_dataset").select("id").eq("date", today).execute()
    if not existing_merge.data:
        supabase.table("merged_dataset").insert(merged_records).execute()
        print(f"✅ Merged {len(merged_records)} records successfully.")
    else:
        print("⚠️ Merge data already exists — skipped.")

except Exception as e:
    print(f"❌ Merge process failed: {e}")

# ============================================================
# ✅ PIPELINE COMPLETE
# ============================================================
print("\n🎯 Agri Intelligence Daily Pipeline Completed Successfully!")
