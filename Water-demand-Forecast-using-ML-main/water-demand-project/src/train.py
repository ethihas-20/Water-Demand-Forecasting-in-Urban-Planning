import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import LabelEncoder
import joblib
import os

# Load dataset
df = pd.read_csv('data/processed/FINAL_SCIENTIFIC_CITY_ZONE_WATER_DEMAND_DATASET.csv')

# Validate columns
expected_columns = ['date', 'city', 'zone', 'population', 'temperature', 'rainfall', 'water_demand_mld']
assert list(df.columns) == expected_columns, f"Columns mismatch: {df.columns}"

# Convert date to datetime
df['date'] = pd.to_datetime(df['date'])

# Sort by date
df = df.sort_values('date').reset_index(drop=True)

# Handle missing values safely
df = df.dropna()

# Feature engineering
df['month'] = df['date'].dt.month
df['week'] = df['date'].dt.isocalendar().week
df['day'] = df['date'].dt.day

# Encode city and zone
le_city = LabelEncoder()
le_zone = LabelEncoder()
df['city_encoded'] = le_city.fit_transform(df['city'])
df['zone_encoded'] = le_zone.fit_transform(df['zone'])

# Data split: time-based, no shuffle
X = df[['month', 'week', 'day', 'city_encoded', 'zone_encoded', 'temperature', 'rainfall', 'population']]
y = df['water_demand_mld']
train_size = int(0.8 * len(df))
X_train, X_test = X[:train_size], X[train_size:]
y_train, y_test = y[:train_size], y[train_size:]

# Train model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
mape = (np.abs((y_test - y_pred) / y_test).mean()) * 100
residuals = y_test - y_pred
std_residual = np.std(residuals)

print(f"MAE: {mae}")
print(f"RMSE: {rmse}")
print(f"MAPE: {mape}%")
print(f"Std Residual: {std_residual}")

# Save model and encoders
os.makedirs('results', exist_ok=True)
joblib.dump(model, 'results/model.pkl')
joblib.dump(le_city, 'results/label_encoder_city.pkl')
joblib.dump(le_zone, 'results/label_encoder_zone.pkl')
joblib.dump(std_residual, 'results/std_residual.pkl')

# Save metrics
metrics_df = pd.DataFrame({'MAE': [mae], 'RMSE': [rmse], 'MAPE': [mape]})
metrics_df.to_csv('results/metrics.csv', index=False)