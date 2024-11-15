import time
import sqlite3
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException
import logging
from contextlib import contextmanager


def init_database():
    """Initialize database and create necessary tables"""
    with sqlite3.connect('forex_data.db') as conn:
        try:
            cursor = conn.cursor()
            
            # Create forex_data table with proper constraints
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS forex_data (
                    date TEXT,
                    from_currency TEXT,
                    to_currency TEXT,
                    exchange_rate FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, from_currency, to_currency)
                )
            ''')
            
            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_forex_data_lookup 
                ON forex_data(from_currency, to_currency, date)
            ''')
            
            conn.commit()
            
        except sqlite3.Error as e:
            logging.error(f"Database initialization error: {e}")
            raise

# Database connection context manager
@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = sqlite3.connect('forex_data.db', timeout=20)
        conn.row_factory = sqlite3.Row
        yield conn
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_driver():
    """Configure and return a Chrome WebDriver with optimal settings"""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-logging")  # Disable Selenium logging
    chrome_options.add_argument("--log-level=3")     # Set Chrome log level to FATAL
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        logging.error(f"Failed to create WebDriver: {str(e)}")
        raise

def period_to_days(period):
    """Convert period string to number of days"""
    period_mapping = {'1W': 7, '1M': 30, '3M': 90, '6M': 180, '1Y': 365}
    return period_mapping.get(period, 7)  # Default to 7 days if invalid period

def convert_date_to_timestamp(date_str):
    """Convert date string to Unix timestamp"""
    try:
        return int(datetime.strptime(date_str, "%Y-%m-%d").timestamp())
    except ValueError as e:
        logging.error(f"Date conversion error: {e}")
        raise

def scrape_forex_data(from_currency, to_currency, period, logger=None):
    """Scrape forex data from Yahoo Finance with improved error handling"""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=period_to_days(period))).strftime("%Y-%m-%d")
    
    logger.info(f"Scraping forex data from {start_date} to {end_date} for {from_currency}-{to_currency}...")
    
    url = f'https://finance.yahoo.com/quote/{from_currency}{to_currency}=X/history?period1={convert_date_to_timestamp(start_date)}&period2={convert_date_to_timestamp(end_date)}'
    
    driver = None
    retry_count = 0
    max_retries = 3
    
    while retry_count < max_retries:
        try:
            driver = get_driver()
            driver.get(url)
            
            # Wait for table with timeout
            wait = WebDriverWait(driver, 20)
            table = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//table[@class='table yf-j5d1ld noDl']")
            ))
            
            rows = table.find_elements(By.XPATH, ".//tbody/tr")
            data = []
            
            for row in rows[1:]:
                try:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) >= 5:
                        date = cols[0].text
                        exchange_rate = float(cols[4].text.replace(',', ''))
                        data_point = {
                            'date': datetime.strptime(date, "%b %d, %Y").strftime("%Y-%m-%d"),
                            'from_currency': from_currency,
                            'to_currency': to_currency,
                            'exchange_rate': exchange_rate
                        }
                        data.append(data_point)
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing row: {e}")
                    continue
            
            if data:  # Only save if we got data
                save_to_database(data, logger)
                return data
            else:
                raise ValueError("No data was scraped")
            
        except TimeoutException:
            retry_count += 1
            logger.warning(f"Timeout occurred, attempt {retry_count} of {max_retries}")
            if retry_count == max_retries:
                raise
            time.sleep(5)  # Wait before retrying
            
        except Exception as e:
            logger.error(f"Error scraping forex data: {e}")
            raise
            
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    logger.error(f"Error closing driver: {e}")
                    
    return []

def save_to_database(entries, logger=None):
    """Save entries to database with improved error handling"""
    if logger is None:
        logger = logging.getLogger(__name__)
        
    if isinstance(entries, dict):
        entries = [entries]

    with get_db_connection() as conn:
        try:
            cursor = conn.cursor()
            
            # Create table if it doesn't exist
            cursor.execute('''CREATE TABLE IF NOT EXISTS forex_data
                            (date TEXT, 
                             from_currency TEXT, 
                             to_currency TEXT, 
                             exchange_rate FLOAT,
                             UNIQUE(date, from_currency, to_currency))''')
            
            for entry in entries:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO forex_data 
                        (date, from_currency, to_currency, exchange_rate)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        entry['date'],
                        entry['from_currency'],
                        entry['to_currency'],
                        entry['exchange_rate']
                    ))
                except sqlite3.Error as e:
                    logger.error(f"Error inserting entry {entry}: {e}")
                    continue
                    
            conn.commit()
            
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            conn.rollback()
            raise

def update_forex_data(logger=None):
    """Update forex data for all currency pairs and periods with improved error handling"""
    if logger is None:
        logger = logging.getLogger(__name__)
        
    currency_pairs = [('GBP', 'INR'), ('AED', 'INR'), ('EUR', 'USD')]
    periods = ['1W', '1M', '3M', '6M', '1Y']
    
    for from_currency, to_currency in currency_pairs:
        for period in periods:
            try:
                logger.info(f"Processing {from_currency}-{to_currency} for {period}...")
                scrape_forex_data(from_currency, to_currency, period, logger)
                time.sleep(2)  # Avoid too many rapid requests
            except Exception as e:
                logger.error(f"Error processing {from_currency}-{to_currency}: {e}")
                continue  # Continue with next pair even if one fails