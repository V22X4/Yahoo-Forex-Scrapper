# Yahoo Forex Scrapper

This project is a full-stack application that allows users to visualize historic exchange rate data.

## Backend (Python)

The backend is built using Flask and provides the following endpoints:

1. `POST /api/forex-data`: This endpoint takes the `from` currency, `to` currency, and `period` as request parameters and returns the corresponding historic exchange rate data.
2. `GET /update-forex-data`: This endpoint triggers the periodic update of the forex data in the SQLite database.

The `utils.py` file contains the functions for scraping the data from Yahoo Finance and updating the database.

## Frontend (HTML, CSS, JavaScript)

The frontend is a simple web application built using HTML, CSS, and JavaScript. It allows the user to select the `from` currency, `to` currency, and `period`, and then fetches the data from the backend API and renders a line chart using Chart.js.

## Setup

1. Install the required Python dependencies by running `pip install -r requirements.txt` in the `backend` directory.
2. Run the Flask app using `python app.py`.
3. Open the `index.html` file in a web browser to access the frontend.
