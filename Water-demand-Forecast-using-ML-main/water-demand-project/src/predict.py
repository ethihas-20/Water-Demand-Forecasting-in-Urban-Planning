import pandas as pd
import joblib
import os
import matplotlib.pyplot as plt
import numpy as np

# Load model and encoders
model = joblib.load('results/model.pkl')
le_city = joblib.load('results/label_encoder_city.pkl')
le_zone = joblib.load('results/label_encoder_zone.pkl')
std_residual = joblib.load('results/std_residual.pkl')

def predict_demand(city, zone, date_str):
    """
    Predict water demand for a specific city, zone and date.
    Uses historical data before the selected date.
    """
    df = pd.read_csv('data/processed/FINAL_SCIENTIFIC_CITY_ZONE_WATER_DEMAND_DATASET.csv')
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    selected_date = pd.to_datetime(date_str)
    city_zone_df = df[(df['city'] == city) & (df['zone'] == zone)]
    if city_zone_df.empty:
        raise ValueError(f"No data for city {city}, zone {zone}")
    # Get data before selected_date
    past_df = city_zone_df[city_zone_df['date'] < selected_date]
    if past_df.empty:
        # Use the earliest data
        last_row = city_zone_df.iloc[0]
    else:
        last_row = past_df.iloc[-1]
    # Features
    row = {
        'month': selected_date.month,
        'week': selected_date.isocalendar().week,
        'day': selected_date.day,
        'city_encoded': le_city.transform([city])[0],
        'zone_encoded': le_zone.transform([zone])[0],
        'temperature': last_row['temperature'],
        'rainfall': last_row['rainfall'],
        'population': last_row['population']
    }
    pred = model.predict(pd.DataFrame([row]))[0]

    # Uncertainty-Aware Forecasting
    lower = pred - 1.96 * std_residual
    upper = pred + 1.96 * std_residual
    expected = pred

    # External Shock Detection Module
    shock_detected = False
    adjustment_factor = 1.0
    if last_row['temperature'] > 35:
        adjustment_factor *= 1.1  # increase by 10%
        shock_detected = True
    if last_row['rainfall'] < 1:
        adjustment_factor *= 1.1
        shock_detected = True
    if not past_df.empty and len(past_df) >= 7:
        recent_avg = past_df['water_demand_mld'].tail(7).mean()
        if abs(pred - recent_avg) / recent_avg > 0.2:
            adjustment_factor *= 1.2  # increase by 20%
            shock_detected = True
    shock_adjusted = expected * adjustment_factor

    # Threshold & Alert Logic
    zone_mean = city_zone_df['water_demand_mld'].mean()
    zone_std = city_zone_df['water_demand_mld'].std()
    low_threshold = zone_mean - 1.5 * zone_std
    high_threshold = zone_mean + 1.5 * zone_std
    alert_message = None
    if shock_adjusted < low_threshold:
        alert_message = "Water demand critically LOW"
    elif shock_adjusted > high_threshold:
        alert_message = "Water demand critically HIGH"

    return {
        'expected': expected,
        'lower': lower,
        'upper': upper,
        'shock_adjusted': shock_adjusted,
        'shock_detected': shock_detected,
        'alert_message': alert_message,
        'low_threshold': low_threshold,
        'high_threshold': high_threshold
    }

# Load dataset to get last values
df = pd.read_csv('data/processed/FINAL_SCIENTIFIC_CITY_ZONE_WATER_DEMAND_DATASET.csv')
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date')

# Get last row per city and zone
last_df = df.groupby(['city', 'zone']).tail(1).set_index(['city', 'zone'])

# Forecast next 30 days for each city and zone
future_periods = 30
forecasts = []

for (city, zone) in last_df.index:
    last_row = last_df.loc[(city, zone)]
    last_date = last_row['date']
    future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=future_periods)

    for date in future_dates:
        row = {
            'month': date.month,
            'week': date.isocalendar().week,
            'day': date.day,
            'city_encoded': le_city.transform([city])[0],
            'zone_encoded': le_zone.transform([zone])[0],
            'temperature': last_row['temperature'],
            'rainfall': last_row['rainfall'],
            'population': last_row['population']
        }
        pred = model.predict(pd.DataFrame([row]))[0]
        forecasts.append({
            'date': date,
            'city': city,
            'zone': zone,
            'predicted_water_demand': pred
        })

forecast_df = pd.DataFrame(forecasts)

# Save forecast
os.makedirs('results/predictions', exist_ok=True)
forecast_df.to_csv('results/predictions/forecast.csv', index=False)

# Plot and save
for city in df['city'].unique():
    for zone in df[df['city'] == city]['zone'].unique():
        city_zone_data = df[(df['city'] == city) & (df['zone'] == zone)]
        city_zone_forecast = forecast_df[(forecast_df['city'] == city) & (forecast_df['zone'] == zone)]

        plt.figure()
        plt.plot(city_zone_data['date'], city_zone_data['water_demand_mld'], label='Historical')
        plt.plot(city_zone_forecast['date'], city_zone_forecast['predicted_water_demand'], label='Forecast')
        plt.title(f'Water Demand Forecast for {city} - {zone}')
        plt.xlabel('Date')
        plt.ylabel('Water Demand')
        plt.legend()
        plt.savefig(f'img/forecast_{city}_{zone}.png')
        plt.close()