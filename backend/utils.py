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
# conn = sqlite3.connect('forex_data.db')
conn = sqlite3.connect('forex_data.db', check_same_thread=False)
c = conn.cursor()

# Create the forex data table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS forex_data
             (date TEXT, from_currency TEXT, to_currency TEXT, exchange_rate FLOAT)''')
conn.commit()

def get_driver():
    # Set up Selenium WebDriver with headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no UI)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Automatically download and set up the correct ChromeDriver version
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def convert_date_to_timestamp(date_str):
    """Convert date string to Unix timestamp."""
    return int(datetime.strptime(date_str, "%Y-%m-%d").timestamp())

def scrape_forex_data(from_currency, to_currency, start_date, end_date):
    print(f"Scraping forex data from {start_date} to {end_date} for {from_currency}-{to_currency}...")
    """Scrape forex data from Yahoo Finance within a date range."""
    # Construct the URL with Unix timestamps for start and end dates
    url = f'https://finance.yahoo.com/quote/{from_currency}{to_currency}=X/history?period1={convert_date_to_timestamp(start_date)}&period2={convert_date_to_timestamp(end_date)}'

    try:
        
        start_time = time.time()
        driver = get_driver()

        # Open the URL
        driver.get(url)

        # Find the table containing historical prices
        table = driver.find_element(By.XPATH, "//table[@class='table yf-j5d1ld noDl']")

        # Extract the rows
        rows = table.find_elements(By.XPATH, ".//tbody/tr")

        # Parse data from rows
        data = []
        for row in rows[1:]:  # Skip the header row
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) < 5:
                continue  # Skip incomplete rows

            date = cols[0].text
            try:
                exchange_rate = float(cols[4].text.replace(',', ''))  # Parse exchange rate
                data.append({
                    'date': datetime.strptime(date, "%b %d, %Y").strftime("%Y-%m-%d"),
                    'from_currency': from_currency,
                    'to_currency': to_currency,
                    'exchange_rate': exchange_rate
                })
            except ValueError:
                print(f"Could not parse exchange rate on {date}")
                continue

        driver.quit()
        
        end_time = time.time()
        total_time = end_time - start_time
        print(f"Total time taken: {total_time:.2f} seconds")
        save_to_database(data)
        return data

    except Exception as e:
        print(f"Error scraping forex data: {e}")
        return []

def save_to_database(data):
    """Save scraped data to SQLite database."""
    for entry in data:
        c.execute('''INSERT INTO forex_data (date, from_currency, to_currency, exchange_rate)
                     VALUES (?, ?, ?, ?)''',
                  (entry['date'], entry['from_currency'], entry['to_currency'], entry['exchange_rate']))
    conn.commit()

def update_forex_data():
    """Update forex data by scraping missing dates."""
    # Get the latest date from the database
    c.execute("SELECT MAX(date) FROM forex_data")
    latest_date = c.fetchone()[0]

    # Set start and end dates for scraping
    if latest_date:
        start_date = (datetime.strptime(latest_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")

    # Scrape and save new data
    new_data = scrape_forex_data('EUR', 'USD', start_date, end_date)
    if new_data:
        save_to_database(new_data)
        print(f"Forex data updated from {start_date} to {end_date}")
    else:
        print("No new data found.")

