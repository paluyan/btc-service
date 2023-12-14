from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, cast, Date, String, extract
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from datetime import datetime
import pytz
from flask_httpauth import HTTPBasicAuth
import os

app = Flask(__name__)
auth = HTTPBasicAuth()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bitcoin_prices.db'
# disable track modifications for performance
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# init SQLAlchemy with the flask app
db = SQLAlchemy(app)

prague_tz = pytz.timezone('Europe/Prague')


@auth.verify_password
def verify_password(username, password):
    return username == os.environ.get('USERNAME_BTC') and password == os.environ.get('PSWD_BTC')

# define a db model for the btc prices
class BitcoinPrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(prague_tz))
    price_eur = db.Column(db.Float)
    price_czk = db.Column(db.Float)

# create the database tables
with app.app_context():
	db.create_all()

# fetch btc prices and store them in the db
def fetch_bitcoin_prices():
    with app.app_context():  
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=eur,czk")
        if response.status_code == 200:
            data = response.json()['bitcoin']
            new_price = BitcoinPrice(price_eur=data['eur'], price_czk=data['czk'])
            db.session.add(new_price)
            db.session.commit()
        else: print(f"Error, {response.status_code}")

# init a scheduler
scheduler = BackgroundScheduler()
# run func every 5 minute
scheduler.add_job(fetch_bitcoin_prices, 'interval', minutes=5)
scheduler.start()

# query the latest BitcoinPrice entry
def get_bitcoin_data():
    latest_price = BitcoinPrice.query.order_by(BitcoinPrice.timestamp.desc()).first()
    if latest_price:
	    return {'price_eur': latest_price.price_eur, 
	    		'price_czk': latest_price.price_czk, 
	    		'server_timestamp': latest_price.timestamp.isoformat()
	    		}
    else:
        return jsonify({'error': 'Data is not collected yet'}), 404

@app.route('/current_price')
@auth.login_required
def current_price():
	client_request_time = datetime.now(prague_tz).isoformat()

	try:
		bitcoin_data = get_bitcoin_data()
	except Exception as e:
		print("Get data error", e)
	bitcoin_data["client_request_time"] = client_request_time
	return jsonify(bitcoin_data)


@app.route('/average_daily')
@auth.login_required
def average_daily():
	avg_prices = db.session.query(
	    func.date(BitcoinPrice.timestamp).label('date'),
	    func.avg(BitcoinPrice.price_eur).label('avg_price_eur'),
	    func.avg(BitcoinPrice.price_czk).label('avg_price_czk')
	).group_by(func.date(BitcoinPrice.timestamp)).all()

	return jsonify([{
	    'date': price.date,  
	    'avg_price_eur': round(price.avg_price_eur, 2),  
	    'avg_price_czk': round(price.avg_price_czk, 2)
	} for price in avg_prices])

@app.route('/monthly_averages')
def monthly_averages():
    monthly_avg_prices = db.session.query(
        extract('year', BitcoinPrice.timestamp).label('year'),
        extract('month', BitcoinPrice.timestamp).label('month'),
        func.avg(BitcoinPrice.price_eur).label('avg_price_eur'),
        func.avg(BitcoinPrice.price_czk).label('avg_price_czk')
    ).group_by('year', 'month').all()

    monthly_data = []
    for year, month, avg_eur, avg_czk in monthly_avg_prices:
        monthly_data.append({
            'year': int(year),
            'month': int(month),
            'avg_price_eur': float(avg_eur),
            'avg_price_czk': float(avg_czk)
        })

    return jsonify(monthly_data)

# delete recors older than 12 month
def delete_old_records():
    twelve_months_ago = datetime.now(prague_tz)  - timedelta(days=365)
    # TODO write function for db backup before cleaning
    BitcoinPrice.query.filter(BitcoinPrice.timestamp < twelve_months_ago).delete()
    db.session.commit()

scheduler = BackgroundScheduler()
scheduler.add_job(delete_old_records, 'cron', month='1-12', day=1, hour=0)
scheduler.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
