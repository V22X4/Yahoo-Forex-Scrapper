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
import schedule


# SQLite Database setup
conn = sqlite3.connect('forex_data.db', check_same_thread=False)
c = conn.cursor()

# Create the forex data table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS forex_data
             (date TEXT, from_currency TEXT, to_currency TEXT, exchange_rate FLOAT)''')
conn.commit()

def get_driver():
    """Configure and return a Chrome WebDriver with optimal settings"""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        return driver
    except Exception as e:
        print(f"Failed to create WebDriver: {str(e)}")
        raise

def period_to_days(period):
    period_to_days = {'1W': 7, '1M': 30, '3M': 90, '6M': 180, '1Y': 365}
    return period_to_days[period]

def convert_date_to_timestamp(date_str):
    """Convert date string to Unix timestamp"""
    return int(datetime.strptime(date_str, "%Y-%m-%d").timestamp())

def scrape_forex_data(from_currency, to_currency, period):
   
    """Scrape forex data from Yahoo Finance"""
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=period_to_days(period))).strftime("%Y-%m-%d")
    
    print(f"Scraping forex data from {start_date} to {end_date} for {from_currency}-{to_currency}...")
    
    url = f'https://finance.yahoo.com/quote/{from_currency}{to_currency}=X/history?period1={convert_date_to_timestamp(start_date)}&period2={convert_date_to_timestamp(end_date)}'
    
    driver = None
    try:
        driver = get_driver()
        driver.get(url)
        
        # Wait for table to be present
        wait = WebDriverWait(driver, 10)
        table = wait.until(EC.presence_of_element_located((By.XPATH, "//table[@class='table yf-j5d1ld noDl']")))
        
        rows = table.find_elements(By.XPATH, ".//tbody/tr")
        data = []
        
        for row in rows[1:]:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 5:
                try:
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
                    print(f"Error parsing row: {e}")
                    continue
        
        save_to_database(data)
        return data
        
    except Exception as e:
        print(f"Error scraping forex data: {e}")
        return []
    
    finally:
        if driver:
            driver.quit()

def save_to_database(entries):
    """Save entries to database ensuring no duplicate (date, from_currency, to_currency)."""
    if isinstance(entries, dict):  # Check if it's a single entry (dict)
        entries = [entries]  # Convert to a list of one entry for uniform handling

    try:
        for entry in entries:
            # Check if the (date, from_currency, to_currency) already exists in the database
            c.execute('''SELECT COUNT(*) FROM forex_data WHERE date = ? AND from_currency = ? AND to_currency = ?''',
                      (entry['date'], entry['from_currency'], entry['to_currency']))
            count = c.fetchone()[0]

            if count == 0:  # If no entry exists, insert it
                c.execute('''INSERT INTO forex_data 
                             (date, from_currency, to_currency, exchange_rate)
                             VALUES (?, ?, ?, ?)''',
                          (entry['date'], entry['from_currency'], 
                           entry['to_currency'], entry['exchange_rate']))
                conn.commit()
                # print(f"Inserted new entry for {entry['from_currency']}-{entry['to_currency']} on {entry['date']}")
            # else:
                # print(f"Entry for {entry['from_currency']}-{entry['to_currency']} on {entry['date']} already exists.")

    except Exception as e:
        print(f"Error saving to database: {e}")
        conn.rollback()


def update_forex_data():
    """Update forex data for all currency pairs and periods"""
    currency_pairs = [('GBP', 'INR'), ('AED', 'INR'), ('EUR', 'USD')]
    periods = ['1W', '1M', '3M', '6M', '1Y']
    
    for from_currency, to_currency in currency_pairs:
        for period in periods:
            try:
                print(f"Processing {from_currency}-{to_currency} for {period}...")
                scrape_forex_data(from_currency, to_currency, period)
                time.sleep(2)  # Avoid too many rapid requests
            except Exception as e:
                print(f"Error processing {from_currency}-{to_currency}: {e}")

def run_scheduler():
    """Run the scheduler loop"""
    while True:
        schedule.run_pending()
        time.sleep(1)

