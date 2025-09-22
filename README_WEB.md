# Team Velocity - Cycling Performance Dashboard

A professional cycling team dashboard website inspired by the UCI Kigali 2025 design, built with Flask and modern web technologies.

## Features

### 🏆 Professional Website Design

- Modern, responsive design inspired by UCI Kigali 2025
- Mobile-friendly interface
- Beautiful animations and transitions
- Professional cycling theme

### 📊 Interactive Dashboard

- Real-time performance metrics
- Time-based analysis (hourly, daily, weekly, monthly, quarterly, yearly)
- Interactive charts using Chart.js
- Team and individual performance comparison

### 🚴‍♂️ Team Management

- Team roster with individual rider profiles
- Performance statistics for each rider
- Team comparison metrics

### 🏁 Race Results

- Podium finishes display
- Complete race results table
- Upcoming races calendar
- Season statistics

### 📈 Data Analysis

- CSV/Excel file upload support
- Automatic data processing and visualization
- Multiple time granularities for analysis
- Export capabilities

### 📰 News & Updates

- Team announcements
- Race updates
- Performance highlights

## Installation

1. **Clone or download the project files**

2. **Install Python dependencies:**

   ```bash
   pip install -r requirements_web.txt
   ```

3. **Run the Flask application:**

   ```bash
   python app_web.py
   ```

4. **Open your browser and navigate to:**
   ```
   http://localhost:5000
   ```

## Usage

### Uploading Data

1. Click on the "Upload CSV or Excel File" section on the homepage
2. Select your cycling data file (CSV or Excel format)
3. The system will automatically process and visualize your data

### Expected Data Format

Your CSV/Excel file should contain columns with cycling performance data. The system automatically detects common column names:

**Required Columns:**

- `timestamp` or `date` - Date and time of the activity
- `rider_name` or `rider` - Name of the cyclist
- `team_name` or `team` - Team name

**Performance Columns:**

- `distance_km` or `distance` - Distance in kilometers
- `duration_sec` or `duration` - Duration in seconds
- `power_watts` or `power` - Power output in watts
- `heart_rate_bpm` or `hr` - Heart rate in beats per minute
- `elevation_gain_m` or `elevation` - Elevation gain in meters

### Sample Data Format

```csv
timestamp,rider_name,team_name,distance_km,duration_sec,power_watts,heart_rate_bpm,elevation_gain_m
2025-01-02 07:15:00,Alex Rider,Team A,32.4,3600,210,145,320
2025-01-03 18:05:00,Jamie Lee,Team B,28.1,3300,195,152,280
2025-02-14 06:45:00,Alex Rider,Team A,45.2,5400,225,148,540
```

### Dashboard Features

1. **Time Period Analysis:**

   - Select different time periods (hourly, daily, weekly, monthly, quarterly, yearly)
   - View performance trends over time
   - Compare team and individual metrics

2. **Performance Metrics:**

   - Total distance covered
   - Average power output
   - Heart rate analysis
   - Elevation gain statistics
   - Speed calculations

3. **Team Comparison:**
   - Side-by-side team performance
   - Individual rider rankings
   - Team statistics summary

## File Structure

```
cycling-dashboard/
├── app_web.py              # Flask web application
├── templates/
│   ├── index.html         # Main dashboard page
│   └── results.html       # Race results page
├── utils/
│   └── data_loader.py     # Data processing utilities
├── data/
│   └── sample_cycling.csv # Sample data file
├── requirements_web.txt   # Python dependencies
└── README_WEB.md         # This file
```

## API Endpoints

The application provides several API endpoints for data access:

- `GET /` - Main dashboard page
- `GET /results` - Race results page
- `POST /upload` - Upload CSV/Excel data
- `GET /api/data/<period>` - Get performance data by time period
- `GET /api/stats` - Get summary statistics
- `GET /api/riders` - Get rider information
- `GET /api/team-comparison` - Get team comparison data
- `GET /api/leaderboard/<period>` - Get leaderboard data
- `GET /api/news` - Get latest news

## Customization

### Adding New Charts

To add new visualizations, modify the JavaScript in `templates/index.html`:

1. Create new chart containers in the HTML
2. Add Chart.js initialization code
3. Connect to Flask API endpoints for data

### Modifying the Design

The CSS is embedded in the HTML templates. Key design elements:

- Color scheme: Blue (#3498db) and purple (#9b59b6) gradients
- Typography: Inter font family
- Layout: CSS Grid and Flexbox
- Animations: CSS transitions and transforms

### Adding New Pages

1. Create new HTML template in `templates/` folder
2. Add route in `app_web.py`
3. Update navigation links in existing templates

## Sample Data

The application includes sample cycling data in `data/sample_cycling.csv` that demonstrates the expected format and provides initial data for testing.

## Browser Compatibility

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## Performance

- Optimized for datasets up to 10,000 records
- Lazy loading for large datasets
- Responsive design for all screen sizes
- Fast chart rendering with Chart.js

## Support

For issues or questions:

1. Check the sample data format
2. Ensure all required dependencies are installed
3. Verify your data file format matches the expected structure

## License

This project is open source and available under the MIT License.
