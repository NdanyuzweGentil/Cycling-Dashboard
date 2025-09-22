# Cycling Performance Dashboard (Streamlit)

## Setup
1. Create a virtual environment (recommended).
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run:
   ```
   streamlit run app.py
   ```

## Using your own data
- Upload a CSV or Excel file via the sidebar.
- If your column names differ, use the "Column Mapping" section to map them.
- Required logical fields (you can map your names to these):
  - timestamp (datetime)
  - rider_name (string)
  - team_name (string, optional)
  - distance_km (numeric, optional)
  - duration_sec (numeric, optional)
  - power_watts (numeric, optional)
  - heart_rate_bpm (numeric, optional)
  - elevation_gain_m (numeric, optional)

## Time resolutions supported
Hourly, Daily, Weekly, Monthly, Quarterly, Yearly.

## Sample data
A small `data/sample_cycling.csv` is included for quick start. Replace with your file or upload in the app.
