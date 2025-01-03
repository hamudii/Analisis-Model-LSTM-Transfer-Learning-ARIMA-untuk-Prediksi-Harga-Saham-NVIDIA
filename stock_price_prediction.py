# -*- coding: utf-8 -*-
"""Stock_price_prediction.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1W3g2mV6TuvdTbFKI3HEAeifMbl9RCyLb
"""

import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
import math
import joblib

# Title
st.title("NVIDIA Stock Price Prediction")
st.markdown("""
This app demonstrates three models for stock price forecasting:
1. ARIMA (AutoRegressive Integrated Moving Average)
2. Long Short-Term Memory (LSTM)
3. Transfer Learning with Pretrained Models
""")

# Sidebar title
# st.sidebar.title("Model Settings")

# Menetapkan model secara otomatis tanpa memungkinkan pengguna memilih
selected_model = ["LSTM", "ARIMA", "Transfer Learning"]

# Menetapkan ticker dan tanggal otomatis tanpa input dari pengguna
ticker = "NVDA"
start_date = pd.to_datetime("2020-01-01")
end_date = pd.to_datetime("2024-10-30")

# # Tampilkan informasi model yang dipilih
# st.sidebar.write(f"Selected Models: {', '.join(selected_model)}")
# st.sidebar.write(f"Stock Ticker: {ticker}")
# st.sidebar.write(f"Start Date: {start_date.date()}")
# st.sidebar.write(f"End Date: {end_date.date()}")

# Load dataset
@st.cache_data
def load_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data

# Panggil fungsi untuk memuat data
data = load_data(ticker, start_date, end_date)
st.write(f"### Data for {ticker} from {start_date.date()} to {end_date.date()}")
st.dataframe(data.tail())

# Load data
data = load_data(ticker, start_date, end_date)
st.write("## Historical Stock Data")
st.line_chart(data['Close'])

# Shared preprocessing
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(data[['Close']])
look_back = 60

df = data
df.replace("null", np.nan, inplace = True)
missing_data = df.isnull()

for column in missing_data.columns.values.tolist():
    print(column)
    print (missing_data[column].value_counts())
    print(" ")

# Flatten multi-level columns
df.columns = ['_'.join(col).strip() for col in df.columns.values]

# Reset index if 'Date' is already the index
df.reset_index(inplace=True)

# Check the DataFrame after modifications

df.set_index('Date', inplace=True)


df_10 = pd.DataFrame()
df_10['Close_NVDA'] = df['Close_NVDA'].rolling(window=10).mean()
df_20 = pd.DataFrame()
df_20['Close_NVDA'] = df['Close_NVDA'].rolling(window=20).mean()
df_30 = pd.DataFrame()
df_30['Close_NVDA'] = df['Close_NVDA'].rolling(window=30).mean()
df_40 = pd.DataFrame()
df_40['Close_NVDA'] = df['Close_NVDA'].rolling(window=40).mean()

if "ARIMA" in selected_model:
    st.write("## ARIMA Model")

    # Load pre-trained ARIMA model
    arima_model = joblib.load('arima_nvda_model.pkl')


    # Melakukan log-transformasi jika data tidak stasioner
    data_log = np.log(df['Close_NVDA'])

    # Jika p-value > 0.05, kita lakukan differencing
    data_diff = data_log.diff().dropna()


    # ADF Test
    st.write("### Augmented Dickey-Fuller (ADF) Test for Stationarity")
    adf_result = adfuller(data_diff)
    st.write(f"ADF Statistic: {adf_result[0]}")
    st.write(f"p-value: {adf_result[1]}")

    # Forecast for test data
    test_size = int(len(data) * 0.1)
    forecast = arima_model.forecast(steps=test_size)
    test = df['Close_NVDA'][-test_size:]
    train = df['Close_NVDA'][:-test_size]

    # Evaluate
    mae = mean_absolute_error(test, forecast)
    rmse = math.sqrt(mean_squared_error(test, forecast))

    st.write(f"Mean Absolute Error: {mae}")
    st.write(f"Root Mean Squared Error: {rmse}")

    # Generate future dates for prediction visualization
    future_dates = pd.date_range(start=test.index[-1], periods=test_size + 1, freq='B')[1:]  # Skip the first date to avoid overlap

    # Plot
    st.write("### ARIMA Model Forecast")
    plt.figure(figsize=(14, 7))
    plt.plot(data.index, df['Close_NVDA'], label='Historical Data', color='blue')
    plt.plot(test.index, forecast, label='Test Forecast', color='red')
    plt.legend()
    st.pyplot(plt)

    # Forecast for 1 year ahead (252 business days)
    one_year_forecast = arima_model.forecast(steps=252)
    future_dates_1yr = pd.date_range(start=test.index[-1], periods=253, freq='B')[1:]  # Skip the first date

    st.write("### 1-Year Forecast with Historical Data")
    # Forecast untuk 1 tahun ke depan (252 hari perdagangan)
    future_steps = 252
    future_forecast = arima_model.forecast(steps=future_steps)

    # Tambahkan pola sinusoidal dan noise
    amplitude = 0.05  # Amplitudo fluktuasi
    period = 50  # Periode fluktuasi sinusoidal
    noise_scale = 0.02  # Skala noise acak

    # Pola sinusoidal
    sinusoidal_variation = amplitude * np.sin(2 * np.pi * np.arange(len(future_forecast)) / period)

    # Noise acak
    random_noise = np.random.normal(loc=0, scale=noise_scale, size=future_forecast.shape)

    # Gabungkan prediksi dengan fluktuasi
    future_forecast_with_fluctuation = future_forecast + sinusoidal_variation + random_noise

    # Generate tanggal untuk 1 tahun ke depan
    future_dates = pd.date_range(start=train.index[-1] + pd.Timedelta(days=1), periods=future_steps, freq='B')

    plt.figure(figsize=(14, 7))

    # Plot data historis
    plt.plot(data.index, df['Close_NVDA'], label='Historical Data', color='blue')

    # Plot forecast dengan fluktuasi
    plt.plot(future_dates, future_forecast_with_fluctuation, label='1-Year Forecast', color='red')

    # Tambahkan judul dan label
    plt.title('1-Year Forecast of NVDA Stock Price')
    plt.xlabel('Date')
    plt.ylabel('Stock Price')
    plt.legend()

    # Tampilkan plot menggunakan Streamlit
    st.pyplot(plt)

    # Display prediction details for 1 year ahead
    future_predictions_1yr_df = pd.DataFrame({
        "Date": future_dates_1yr,
        "Predicted Price": one_year_forecast.values  # Convert Series to array
    })
    st.write("### Predicted Stock Prices for Next Year with ARIMA")
    st.dataframe(future_predictions_1yr_df)

    # Downloadable CSV for 1 year forecast
    csv_1yr = future_predictions_1yr_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download 1 Year Predictions as CSV",
        data=csv_1yr,
        file_name="nvidia_1yr_predictions_ARIMA.csv",
        mime="text/csv"
    )

# Model: LSTM
if "LSTM" in selected_model:
    st.write("## LSTM Model")
    look_back = 60
    x_train, y_train = [], []
    for i in range(look_back, len(scaled_data)):
        x_train.append(scaled_data[i-look_back:i, 0])
        y_train.append(scaled_data[i, 0])

    x_train, y_train = np.array(x_train), np.array(y_train)
    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))

    # Load pre-trained LSTM model and training history
    lstm_model = load_model('lstm_model.h5')
    import json
    with open('lstm_training_history.json', 'r') as f:
        lstm_training_history = json.load(f)

    # Predictions
    predicted_train_prices = lstm_model.predict(x_train)
    predicted_train_prices = scaler.inverse_transform(predicted_train_prices)
    actual_train_prices = scaler.inverse_transform(y_train.reshape(-1, 1))

    rmse_lstm = math.sqrt(mean_squared_error(actual_train_prices, predicted_train_prices))
    mae_lstm = mean_absolute_error(actual_train_prices, predicted_train_prices)

    st.write(f"RMSE (LSTM): {rmse_lstm}")
    st.write(f"MAE (LSTM): {mae_lstm}")
    st.line_chart({"Actual": actual_train_prices.flatten(), "Predicted": predicted_train_prices.flatten()})

    # Visualize training loss
    st.write("### Training Loss (LSTM)")
    plt.figure(figsize=(18, 9))
    plt.plot(lstm_training_history['loss'], label='Loss LSTM')
    plt.xlabel('Epoch')
    plt.ylabel('Loss LSTM')
    plt.title('LSTM Training Loss')
    plt.legend()
    st.pyplot(plt)

    look_back = 60
    future_steps = 252  # Approximate trading days in 1 year
    frequency = 30  # Periodic wave frequency (in days)
    seasonality_amplitude = 0.04  # Increased amplitude for noticeable seasonality
    trend_factor = 0.0001  # Small constant upward trend per step

    # Initialize last sequence for future prediction
    last_sequence = scaled_data[-look_back:]
    future_predictions = []

    # Generate predictions with trend and seasonality
    for step in range(future_steps):
        pred = lstm_model.predict(last_sequence.reshape(1, -1, 1))

        # Add effects: noise, fluctuation, seasonality, and trend
        base_noise = np.random.normal(0, 0.007 + step * 0.00001, pred.shape)
        fluctuation = np.random.normal(0, 0.09) if np.random.rand() > 0.9 else 0
        seasonality = seasonality_amplitude * math.sin(3 * math.pi * (step % frequency) / frequency)
        trend = trend_factor * step

        # Combine predictions and effects
        pred_with_effects = pred + base_noise + fluctuation + seasonality + trend

        future_predictions.append(pred_with_effects[0, 0])
        last_sequence = np.append(last_sequence[1:], pred_with_effects)

    # Transform predictions back to original scale
    future_predictions = scaler.inverse_transform(np.array(future_predictions).reshape(-1, 1))

    # Generate future dates for visualization
    future_dates = pd.date_range(df.index[-1], periods=future_steps + 1, freq='B')[1:]  # Skip the first date to avoid overlap

    # Display historical data plot
    st.write("### Historical Data and Future Predictions")
    plt.figure(figsize=(18, 9))
    plt.plot(df.index, df['Close_NVDA'], label='Historical Data', color='blue')

    # Plot future predictions
    plt.plot(future_dates, future_predictions, label='Enhanced Future Predictions with Trend and Seasonality', color='red')

    # Labels and title
    plt.xlabel('Date')
    plt.ylabel('Close Price USD ($)')
    plt.title('NVIDIA Stock Price Forecast with Trend and Seasonality')
    plt.legend(loc='upper left')

    # Show plot
    st.pyplot(plt)

    # Display prediction details in a table
    future_predictions_df = pd.DataFrame({
        "Date": future_dates,
        "Predicted Price": future_predictions.flatten()
    })
    st.write("### Predicted Stock Prices for Next Year with LSTM")
    st.dataframe(future_predictions_df)

    # Downloadable CSV
    csv = future_predictions_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Predicted Prices as CSV",
        data=csv,
        file_name="nvidia_future_predictions_LSTM.csv",
        mime="text/csv"
    )

# Model: Transfer Learning
if "Transfer Learning" in selected_model:
    st.write("## Transfer Learning")

    # Load pre-trained Transfer Learning model and training history
    transfer_learning_model = load_model('transfer_learning_model.h5')
    import json
    with open('lstm_training_history.json', 'r') as f:
        transfer_training_history = json.load(f)

    predicted_train_prices_tl =  transfer_learning_model.predict(x_train)
    predicted_train_prices_tl = scaler.inverse_transform(predicted_train_prices_tl)
    actual_train_prices = scaler.inverse_transform(y_train.reshape(-1, 1))

    rmse_transfer = math.sqrt(mean_squared_error(actual_train_prices, predicted_train_prices_tl))
    mae_transfer = mean_absolute_error(actual_train_prices, predicted_train_prices_tl)

    st.write(f"RMSE (Transfer Learning): {rmse_transfer}")
    st.write(f"MAE (Transfer Learning): {mae_transfer}")
    st.line_chart({"Actual": actual_train_prices.flatten(), "Predicted": predicted_train_prices_tl.flatten()})

    # Visualize training loss
    st.write("### Training Loss (Transfer Learning)")
    plt.figure(figsize=(18, 9))
    plt.plot(transfer_training_history['loss'], label='Loss Transfer Learning')
    plt.xlabel('Epoch')
    plt.ylabel('Loss Transfer Learning')
    plt.title('Transfer Learning Training Loss')
    plt.legend()
    st.pyplot(plt)

    look_back = 60
    future_steps = 252  # Approximate trading days in 1 year
    frequency = 30  # Periodic wave frequency (in days)
    seasonality_amplitude = 0.04  # Increased amplitude for noticeable seasonality
    trend_factor = 0.0001  # Small constant upward trend per step

    # Initialize last sequence for future prediction
    last_sequence = scaled_data[-look_back:]
    future_predictions = []

    # Generate predictions with trend and seasonality
    for step in range(future_steps):
        pred = transfer_learning_model.predict(last_sequence.reshape(1, -1, 1))

        # Add effects: noise, fluctuation, seasonality, and trend
        base_noise = np.random.normal(0, 0.007 + step * 0.00001, pred.shape)
        fluctuation = np.random.normal(0, 0.09) if np.random.rand() > 0.9 else 0
        seasonality = seasonality_amplitude * math.sin(3 * math.pi * (step % frequency) / frequency)
        trend = trend_factor * step

        # Combine predictions and effects
        pred_with_effects = pred + base_noise + fluctuation + seasonality + trend

        future_predictions.append(pred_with_effects[0, 0])
        last_sequence = np.append(last_sequence[1:], pred_with_effects)

    # Transform predictions back to original scale
    future_predictions = scaler.inverse_transform(np.array(future_predictions).reshape(-1, 1))

    # Generate future dates for visualization
    future_dates = pd.date_range(df.index[-1], periods=future_steps + 1, freq='B')[1:]  # Skip the first date to avoid overlap

    # Display historical data plot
    st.write("### Historical Data and Future Predictions")
    plt.figure(figsize=(18, 9))
    plt.plot(df.index, df['Close_NVDA'], label='Historical Data', color='blue')

    # Plot future predictions
    plt.plot(future_dates, future_predictions, label='Enhanced Future Predictions with Trend and Seasonality', color='red')

    # Labels and title
    plt.xlabel('Date')
    plt.ylabel('Close Price USD ($)')
    plt.title('NVIDIA Stock Price Forecast with Trend and Seasonality')
    plt.legend(loc='upper left')

    # Show plot
    st.pyplot(plt)

    # Display prediction details in a table
    future_predictions_df = pd.DataFrame({
        "Date": future_dates,
        "Predicted Price": future_predictions.flatten()
    })
    st.write("### Predicted Stock Prices for Next Year with Transfer Learning")
    st.dataframe(future_predictions_df)

    # Downloadable CSV
    csv = future_predictions_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Predicted Prices as CSV",
        data=csv,
        file_name="nvidia_future_predictions_Transfer Learning.csv",
        mime="text/csv"
    )

st.write("### Thank you for using the app!")