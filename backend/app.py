from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
import sqlite3
import threading
import schedule
import signal
import sys
import time
import logging
import os
from werkzeug.serving import is_running_from_reloader
from contextlib import contextmanager
from utils import scrape_forex_data, update_forex_data, init_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global variables for thread management
scheduler_thread = None
should_run_scheduler = threading.Event()

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        conn = sqlite3.connect('forex_data.db', timeout=20)
        conn.row_factory = sqlite3.Row
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Shutdown signal received. Cleaning up...")
    should_run_scheduler.clear()
    if scheduler_thread:
        scheduler_thread.join(timeout=5)
    sys.exit(0)

def run_scheduler():
    """Run the scheduler loop with proper shutdown handling"""
    logger.info("Scheduler thread started")
    while should_run_scheduler.is_set():
        try:
            schedule.run_pending()
            should_run_scheduler.wait(timeout=1)
        except Exception as e:
            logger.error(f"Error in scheduler: {e}")
            time.sleep(1)  # Prevent rapid error loops
    logger.info("Scheduler thread stopping")

@app.route('/api/forex-data', methods=['POST'])
def get_forex_data():
    try:
        data = request.get_json()
        if not data or not all(key in data for key in ['from', 'to', 'period']):
            return jsonify({'error': 'Missing required parameters'}), 400

        from_currency = data['from']
        to_currency = data['to']
        period = data['period']

        # Validate period
        valid_periods = ['1W', '1M', '3M', '6M', '1Y']
        if period not in valid_periods:
            return jsonify({'error': 'Invalid period'}), 400

        # Calculate date range
        end_date = datetime.now()
        period_days = {
            '1W': 7, '1M': 30, '3M': 90,
            '6M': 180, '1Y': 365
        }
        start_date = end_date - timedelta(days=period_days[period])

        try:
            
            # scrape it
            forex_data = scrape_forex_data(from_currency, to_currency, period)
            return jsonify(forex_data)


        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return jsonify({'error': 'Database error occurred'}), 500

    except Exception as e:
        logger.error(f"Error in get_forex_data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/update', methods=['POST'])
def trigger_update():
    try:
        update_thread = threading.Thread(
            target=update_forex_data,
            daemon=True,
            kwargs={'logger': logger}
        )
        update_thread.start()
        return jsonify({'message': 'Update triggered successfully'})
    except Exception as e:
        logger.error(f"Error triggering update: {e}")
        return jsonify({'error': str(e)}), 500

def start_scheduler():
    """Start the scheduler thread with proper initialization"""
    global scheduler_thread
    if not is_running_from_reloader():
        should_run_scheduler.set()
        schedule.every(24).hours.do(lambda: update_forex_data(logger=logger))
        scheduler_thread = threading.Thread(
            target=run_scheduler,
            daemon=True
        )
        scheduler_thread.start()
        logger.info("Scheduler started successfully")
        
def initialize_app():
    """Initialize application dependencies"""
    try:
        init_database()  # Initialize database and create tables
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)

if __name__ == '__main__':
    
    initialize_app()
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start scheduler
    start_scheduler()
    
    try:
        # Run Flask app
        port = int(os.getenv("PORT", 3000))  # Default to 5000 if not defined
        app.run(debug=True, use_reloader=True, host='0.0.0.0', port=port)

    except Exception as e:
        logger.error(f"Error starting Flask app: {e}")
    finally:
        # Cleanup
        should_run_scheduler.clear()
        if scheduler_thread:
            scheduler_thread.join(timeout=5)
        logger.info("Application shutdown complete")