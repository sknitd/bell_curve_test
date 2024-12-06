import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
import streamlit as st
import time

# Google Sheets CSV export link
sheet_url = "https://docs.google.com/spreadsheets/d/124iF_dVpT5HMMHRRq5s3-66lc2EpMPw8cekL2JiTR7s/gviz/tq?tqx=out:csv"

# Function to dynamically calculate bins
def calculate_bins(data):
    n = len(data)
    return int(np.ceil(np.log2(n) + 1))  # Sturges' Rule

# Function to calculate percentiles based on the actual dataset
def calculate_percentile(value, data):
    rank = data[data <= value].count()
    percentile = (rank / len(data)) * 100
    return percentile

# Function to find the nearest value in the dataset and its corresponding date
def find_nearest_value_and_date(percentile_value, data):
    nearest_value = data.iloc[(data["NetMargin"] - percentile_value).abs().idxmin()]
    return nearest_value["NetMargin"], nearest_value["Date"]

# Streamlit app
def main():
    st.title("Dynamic Bell Curve with Date-Filtered Sample and Real-Time Updates")

    # Add auto-refresh interval
    refresh_interval = st.sidebar.slider("Refresh Interval (seconds)", 1, 60, 10)

    # Fetch data from Google Sheets
    st.write("Fetching data from Google Sheets...")
    try:
        data = pd.read_csv(sheet_url)
        st.success("Successfully fetched data!")
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        return

    # Ensure the required columns are present
    if "NetMargin" not in data.columns or "Date" not in data.columns:
        st.error("The Google Sheet must contain 'NetMargin' and 'Date' columns.")
        return

    # Extract and preprocess data
    data["NetMargin"] = data["NetMargin"].astype(float)
    data["Date"] = pd.to_datetime(data["Date"])
    data = data.sort_values(by="Date")
    net_margin = data["NetMargin"]
    dates = data["Date"]

    # Combine Date and NetMargin into a single column for the dropdown
    combined_data = pd.DataFrame({"Date": dates, "NetMargin": net_margin})
    combined_data["Dropdown"] = combined_data["Date"].dt.strftime("%Y-%m-%d") + " | " + combined_data["NetMargin"].round(2).astype(str)

    # Dropdown for selecting a date and NetMargin value
    st.markdown("### Select a Date and Value")
    selected_row = st.selectbox("Choose a Date and NetMargin value:", combined_data["Dropdown"])
    selected_value = float(selected_row.split("|")[1].strip())  # Extract the NetMargin value
    selected_date = pd.to_datetime(selected_row.split("|")[0].strip())  # Extract the Date

    # Filter data up to the selected date
    filtered_data = combined_data[combined_data["Date"] <= selected_date]
    filtered_net_margin = filtered_data["NetMargin"]

    # Calculate bins dynamically
    bins = calculate_bins(filtered_net_margin)

    # Calculate percentile for the selected value in the filtered data
    percentile = calculate_percentile(selected_value, filtered_net_margin)

    # Calculate specific percentiles in the filtered data
    percentiles = [50, 80, 90, 95, 99]
    percentile_values = {p: np.percentile(filtered_net_margin, p) for p in percentiles}

    # Find the nearest values and dates for each percentile in the filtered data
    nearest_values_and_dates = {}
    for p, val in percentile_values.items():
        nearest_value, nearest_date = find_nearest_value_and_date(val, filtered_data)
        nearest_values_and_dates[p] = (nearest_value, nearest_date)

    # Display calculated percentiles and corresponding dates
    st.markdown("### Percentile Summary (Filtered Data)")
    for p, (val, date) in nearest_values_and_dates.items():
        st.write(f"{p}th Percentile: {val:.2f} (Date: {date.strftime('%Y-%m-%d')})")

    # Create histogram and bell curve for the filtered data
    fig, ax = plt.subplots(figsize=(10, 6))
    counts, bins, _ = ax.hist(filtered_net_margin, bins=bins, density=True, alpha=0.6, color="blue", label="NetMargin Histogram (Filtered)")
    mean, std_dev = filtered_net_margin.mean(), filtered_net_margin.std()
    x = np.linspace(bins[0], bins[-1], 1000)
    y = 1 / (std_dev * np.sqrt(2 * np.pi)) * np.exp(-0.5 * ((x - mean) / std_dev) ** 2)
    ax.plot(x, y, "k-", linewidth=2, label="Fitted Bell Curve (Filtered)")

    # Highlight the selected value on the bell curve
    ax.axvline(x=selected_value, color="red", linestyle="--", label=f"Selected Value: {selected_value}")
    ax.text(selected_value, max(y) / 2, f"Percentile: {percentile:.2f}%", color="red", rotation=90)

    # Highlight specific percentiles on the bell curve
    for p, (val, date) in nearest_values_and_dates.items():
        ax.axvline(x=val, color="green", linestyle="--", label=f"{p}th Percentile: {val:.2f}")

    ax.set_title("Distribution of NetMargin (Filtered by Date)")
    ax.set_xlabel("NetMargin")
    ax.set_ylabel("Density")
    ax.legend()

    # Display the updated plot
    st.pyplot(fig)

    # Show selected date, value, and percentile
    st.write(f"**Selected Date:** {selected_date.strftime('%Y-%m-%d')}")
    st.write(f"**Selected Value:** {selected_value}")
    st.write(f"**Percentile:** {percentile:.2f}%")

    # Automatically refresh the page after the interval
    st.write(f"Auto-refreshing every {refresh_interval} seconds...")
    time.sleep(refresh_interval)
    st.experimental_rerun()

if __name__ == "__main__":
    main()
