from flask import Flask, render_template, request, jsonify, send_from_directory
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from utils.data_loader import load_data, add_time_granularities, aggregate_by_period

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Global variable to store current data
current_data = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/results')
def results():
    return render_template('results.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    global current_data
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Read the uploaded file
        if file.filename.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            df = pd.read_csv(file)
        
        # Process the data using existing utilities
        current_data = df
        current_data = add_time_granularities(current_data)
        
        # Generate summary statistics
        stats = generate_summary_stats(current_data)
        
        # Generate rider summaries
        riders = generate_rider_summaries(current_data)
        
        return jsonify({
            'success': True,
            'stats': stats,
            'riders': riders,
            'message': f'Successfully uploaded {len(current_data)} records'
        })
        
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 400

@app.route('/api/data/<period>')
def get_performance_data(period):
    if current_data is None:
        # Load sample data if no data is uploaded
        current_data = load_data("data/sample_cycling.csv")
        current_data = add_time_granularities(current_data)
    
    try:
        # Generate time series data for the specified period
        data = generate_time_series_data(current_data, period)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': f'Error generating data: {str(e)}'}), 500

@app.route('/api/stats')
def get_stats():
    if current_data is None:
        # Load sample data if no data is uploaded
        current_data = load_data("data/sample_cycling.csv")
        current_data = add_time_granularities(current_data)
    
    stats = generate_summary_stats(current_data)
    return jsonify(stats)

@app.route('/api/riders')
def get_riders():
    if current_data is None:
        # Load sample data if no data is uploaded
        current_data = load_data("data/sample_cycling.csv")
        current_data = add_time_granularities(current_data)
    
    riders = generate_rider_summaries(current_data)
    return jsonify(riders)

@app.route('/api/team-comparison')
def get_team_comparison():
    if current_data is None:
        # Load sample data if no data is uploaded
        current_data = load_data("data/sample_cycling.csv")
        current_data = add_time_granularities(current_data)
    
    team_data = generate_team_comparison_data(current_data)
    return jsonify(team_data)

def generate_summary_stats(df):
    """Generate summary statistics from the dataframe"""
    stats = {}
    
    if 'distance_km' in df.columns:
        stats['totalDistance'] = float(df['distance_km'].sum())
    else:
        stats['totalDistance'] = 0.0
    
    if 'duration_sec' in df.columns:
        stats['totalDuration'] = float(df['duration_sec'].sum() / 3600)  # Convert to hours
    else:
        stats['totalDuration'] = 0.0
    
    if 'power_watts' in df.columns:
        stats['avgPower'] = float(df['power_watts'].mean()) if not df['power_watts'].isna().all() else 0
    else:
        stats['avgPower'] = 0
    
    if 'heart_rate_bpm' in df.columns:
        stats['avgHeartRate'] = float(df['heart_rate_bpm'].mean()) if not df['heart_rate_bpm'].isna().all() else 0
    else:
        stats['avgHeartRate'] = 0
    
    if 'elevation_gain_m' in df.columns:
        stats['totalElevation'] = float(df['elevation_gain_m'].sum())
    else:
        stats['totalElevation'] = 0.0
    
    return stats

def generate_rider_summaries(df):
    """Generate individual rider performance summaries"""
    if 'rider_name' not in df.columns:
        return []
    
    rider_stats = []
    
    for rider in df['rider_name'].unique():
        rider_data = df[df['rider_name'] == rider]
        
        stats = {
            'name': rider,
            'team': rider_data['team_name'].iloc[0] if 'team_name' in rider_data.columns else 'Unknown',
            'distance': float(rider_data['distance_km'].sum()) if 'distance_km' in rider_data.columns else 0,
            'duration': float(rider_data['duration_sec'].sum() / 3600) if 'duration_sec' in rider_data.columns else 0,
            'power': float(rider_data['power_watts'].mean()) if 'power_watts' in rider_data.columns and not rider_data['power_watts'].isna().all() else 0,
            'hr': float(rider_data['heart_rate_bpm'].mean()) if 'heart_rate_bpm' in rider_data.columns and not rider_data['heart_rate_bpm'].isna().all() else 0,
            'elevation': float(rider_data['elevation_gain_m'].sum()) if 'elevation_gain_m' in rider_data.columns else 0
        }
        rider_stats.append(stats)
    
    return rider_stats

def generate_time_series_data(df, period):
    """Generate time series data for charts"""
    if period not in ['hour', 'day', 'week', 'month', 'quarter', 'year']:
        period = 'month'
    
    # Generate labels based on period
    if period == 'hour':
        labels = [f"{i:02d}:00" for i in range(24)]
    elif period == 'day':
        labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    elif period == 'week':
        labels = [f"Week {i}" for i in range(1, 13)]
    elif period == 'month':
        labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    elif period == 'quarter':
        labels = ['Q1', 'Q2', 'Q3', 'Q4']
    else:  # year
        labels = [str(year) for year in range(2020, 2026)]
    
    # Generate sample data (in a real app, this would be actual aggregated data)
    np.random.seed(42)  # For consistent sample data
    distance_data = np.random.normal(50, 15, len(labels)).clip(10, 100)
    power_data = np.random.normal(200, 30, len(labels)).clip(150, 300)
    
    # Team data
    teams = df['team_name'].unique() if 'team_name' in df.columns else ['Team A', 'Team B']
    team_power = np.random.normal(200, 20, len(teams)).clip(180, 250)
    
    return {
        'labels': labels,
        'distance': distance_data.tolist(),
        'power': power_data.tolist(),
        'teams': teams.tolist(),
        'teamPower': team_power.tolist()
    }

def generate_team_comparison_data(df):
    """Generate team comparison data"""
    if 'team_name' not in df.columns:
        return {'teams': [], 'metrics': {}}
    
    teams = df['team_name'].unique()
    metrics = {}
    
    for team in teams:
        team_data = df[df['team_name'] == team]
        
        metrics[team] = {
            'totalDistance': float(team_data['distance_km'].sum()) if 'distance_km' in team_data.columns else 0,
            'avgPower': float(team_data['power_watts'].mean()) if 'power_watts' in team_data.columns and not team_data['power_watts'].isna().all() else 0,
            'avgHeartRate': float(team_data['heart_rate_bpm'].mean()) if 'heart_rate_bpm' in team_data.columns and not team_data['heart_rate_bpm'].isna().all() else 0,
            'totalElevation': float(team_data['elevation_gain_m'].sum()) if 'elevation_gain_m' in team_data.columns else 0,
            'riderCount': len(team_data['rider_name'].unique()) if 'rider_name' in team_data.columns else 0
        }
    
    return {
        'teams': teams.tolist(),
        'metrics': metrics
    }

@app.route('/api/leaderboard/<period>')
def get_leaderboard(period):
    if current_data is None:
        # Load sample data if no data is uploaded
        current_data = load_data("data/sample_cycling.csv")
        current_data = add_time_granularities(current_data)
    
    try:
        # Generate leaderboard data
        leaderboard_data = generate_leaderboard_data(current_data, period)
        return jsonify(leaderboard_data)
    except Exception as e:
        return jsonify({'error': f'Error generating leaderboard: {str(e)}'}), 500

def generate_leaderboard_data(df, period):
    """Generate leaderboard data for riders and teams"""
    if period not in ['hour', 'day', 'week', 'month', 'quarter', 'year']:
        period = 'month'
    
    # Rider leaderboard
    rider_leaderboard = []
    if 'rider_name' in df.columns:
        for rider in df['rider_name'].unique():
            rider_data = df[df['rider_name'] == rider]
            total_distance = rider_data['distance_km'].sum() if 'distance_km' in rider_data.columns else 0
            avg_power = rider_data['power_watts'].mean() if 'power_watts' in rider_data.columns and not rider_data['power_watts'].isna().all() else 0
            
            rider_leaderboard.append({
                'name': rider,
                'team': rider_data['team_name'].iloc[0] if 'team_name' in rider_data.columns else 'Unknown',
                'distance': float(total_distance),
                'power': float(avg_power),
                'rides': len(rider_data)
            })
    
    # Sort by distance
    rider_leaderboard.sort(key=lambda x: x['distance'], reverse=True)
    
    # Team leaderboard
    team_leaderboard = []
    if 'team_name' in df.columns:
        for team in df['team_name'].unique():
            team_data = df[df['team_name'] == team]
            total_distance = team_data['distance_km'].sum() if 'distance_km' in team_data.columns else 0
            avg_power = team_data['power_watts'].mean() if 'power_watts' in team_data.columns and not team_data['power_watts'].isna().all() else 0
            rider_count = len(team_data['rider_name'].unique()) if 'rider_name' in team_data.columns else 0
            
            team_leaderboard.append({
                'name': team,
                'distance': float(total_distance),
                'power': float(avg_power),
                'riderCount': rider_count,
                'rides': len(team_data)
            })
    
    # Sort by distance
    team_leaderboard.sort(key=lambda x: x['distance'], reverse=True)
    
    return {
        'riders': rider_leaderboard[:10],  # Top 10 riders
        'teams': team_leaderboard[:5]      # Top 5 teams
    }

@app.route('/api/news')
def get_news():
    """Get latest news and updates"""
    news = [
        {
            'id': 1,
            'title': 'Team Victory at Regional Championship',
            'date': '2025-03-15',
            'excerpt': 'Our team secured first place in the regional cycling championship with outstanding performances from all riders.',
            'category': 'Achievement'
        },
        {
            'id': 2,
            'title': 'New Training Program Launched',
            'date': '2025-03-10',
            'excerpt': 'We\'ve introduced a new high-intensity training program to improve our riders\' performance metrics.',
            'category': 'Training'
        },
        {
            'id': 3,
            'title': 'New Rider Joins Team',
            'date': '2025-03-05',
            'excerpt': 'We\'re excited to welcome our newest team member who brings fresh energy and talent to our cycling squad.',
            'category': 'Team'
        },
        {
            'id': 4,
            'title': 'Performance Analytics Update',
            'date': '2025-02-28',
            'excerpt': 'Our new dashboard provides real-time insights into rider performance across all training sessions.',
            'category': 'Technology'
        }
    ]
    
    return jsonify(news)

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Initialize with sample data
    try:
        current_data = load_data("data/sample_cycling.csv")
        current_data = add_time_granularities(current_data)
        print("Loaded sample data successfully")
    except Exception as e:
        print(f"Warning: Could not load sample data: {e}")
        current_data = None
    
    app.run(debug=True, host='0.0.0.0', port=5000)
