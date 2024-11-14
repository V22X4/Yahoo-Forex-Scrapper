from flask import Flask, jsonify, request
from utils import scrape_forex_data, update_forex_data, run_scheduler
from flask_cors import CORS
from datetime import datetime, timedelta
import sqlite3
import threading
import schedule
from werkzeug.serving import is_running_from_reloader

app = Flask(__name__)
CORS(app)

def get_db_connection():
    conn = sqlite3.connect('forex_data.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/forex-data', methods=['POST'])
def get_forex_data():
    try:
        data = request.get_json()
        from_currency = data['from']
        to_currency = data['to']
        period = data['period']
        
        # First try to get data from the database
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Calculate the date range based on the period
        end_date = datetime.now()
        if period == '1W':
            start_date = end_date - timedelta(days=7)
        elif period == '1M':
            start_date = end_date - timedelta(days=30)
        elif period == '3M':
            start_date = end_date - timedelta(days=90)
        elif period == '6M':
            start_date = end_date - timedelta(days=180)
        else:  # 1Y
            start_date = end_date - timedelta(days=365)
            
        # If no data in database, scrape it
        forex_data = scrape_forex_data(from_currency, to_currency, period)
        return jsonify(forex_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update', methods=['POST'])
def trigger_update():
    try:
        update_forex_data()
        return jsonify({'message': 'Update triggered successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# Start the scheduler in a separate thread when the app starts
def start_scheduler():
    global scheduler_thread
    if not is_running_from_reloader():
        schedule.every(24).hours.do(update_forex_data)
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()

# Ensure that the scheduler thread is joined before the app stops
def shutdown_scheduler():
    global scheduler_thread
    if scheduler_thread:
        scheduler_thread.join()

# Flask application entry point
if __name__ == '__main__':
    start_scheduler()  # Start the scheduler thread when the app starts
    try:
        app.run(debug=True)  # Run the Flask app
    finally:
        shutdown_scheduler()  # Join the scheduler thread when the app shuts down