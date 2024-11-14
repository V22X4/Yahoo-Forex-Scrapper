from flask import Flask, jsonify, request
from utils import scrape_forex_data, update_forex_data
from flask_cors import CORS
from flask_cors import cross_origin
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)


periodToDays = {'1W': 7, '1M': 30, '3M': 90, '6M': 180, '1Y': 365}


@app.route('/api/forex-data', methods=['POST'])
@cross_origin()
def get_forex_data():
    data = request.get_json()
    from_currency = data['from']
    to_currency = data['to']
    period = data['period']
    
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=periodToDays[period])).strftime("%Y-%m-%d")
    
    forex_data = scrape_forex_data(from_currency, to_currency, start_date, end_date)
    return jsonify(forex_data)

@app.route('/update-forex-data', methods=['GET'])
@cross_origin()
def update_data():
    update_forex_data()
    return jsonify({'message': 'Forex data updated successfully'})

if __name__ == '__main__':
    app.run(debug=True)