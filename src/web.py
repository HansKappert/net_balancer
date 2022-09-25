import logging
import os 

from flask                           import Flask
from flask                           import request, render_template, url_for, redirect, jsonify
from geopy.geocoders                 import Nominatim
from datetime                        import datetime
from flask                           import Flask, request, jsonify
from common.model                    import model
from common.persistence              import persistence
from common.database_logging_handler import database_logging_handler

from service.tesla_energy_consumer   import tesla_energy_consumer


app = Flask(__name__)
app.config['SECRET_KEY'] = 'HeelLekkerbeLangrijk'

db = persistence()
data_model = model(db)
tesla = tesla_energy_consumer(db)

tesla_user = os.environ["TESLA_USER"]
try:
    tesla.initialize(email=tesla_user)
except Exception as e:
    logging.exception(e)
data_model.add_consumer(tesla)

logger = logging.getLogger(__name__)

log_handler = logging.StreamHandler()
log_handler.setLevel(logging.DEBUG)
logger.addHandler(log_handler)

log_handler = database_logging_handler(db)
log_handler.setLevel(logging.INFO)
logger.addHandler(log_handler)

###
#    Web page routings
###
@app.route('/log/get_all', methods=['GET'])
def log_get_all():
    log_lines = db.get_log_lines()
    return render_template('logging.html', 
        lines=log_lines, nice_date=nice_date
    )    
def nice_date(d):
    return d[:19]

@app.route('/', methods=['GET'])
def index():
    if (db.get_consumer_balance('Tesla') == 1):
        _balance_tesla = "checked"
    else:
        _balance_tesla = ""


    return render_template('index.html', 
        model=data_model, 
        balance_tesla=_balance_tesla
    )    


@app.route('/settings', methods=['GET','POST'])
def settings():
    if request.method == 'POST':
        data_model.log_retention = int(request.form['log_retention'])
        return redirect(url_for('index'))
    else:
        return render_template('settings.html', 
        log_retention   = data_model.log_retention
        )

@app.route('/history', methods=['GET'])
def history():
        history = db.get_history()
        surplusses = '['
        productions = '['
        tesla_consumptions = '['
        
        datetime_obj = datetime.fromtimestamp(history[0][0])
        datetime_str = datetime_obj.strftime("%Y/%m/%d %H:%M:%S")
        aantal = 0
        for i in history:
            aantal += 1
            if aantal < 1440:
                msec_since = str(i[0] )
                surplusses += '[' + msec_since + ',' + str(i[2]) + '],'
                productions += '[' + msec_since + ',' + str(i[1]) + '],'
                tesla_consumptions += '[' + msec_since + ',' + str(i[3]) + '],'
            
        surplusses = surplusses[:-1] + ']'
        productions = productions[:-1] + ']'
        tesla_consumptions = tesla_consumptions[:-1] + ']'
        return render_template('history.html', start_datetime_str=datetime_str, surplusses = surplusses, productions = productions, tesla_consumptions = tesla_consumptions)

@app.route('/consumer_tesla', methods=['GET','POST'])
def consumer_tesla():
    if request.method == 'POST':
        data_model._consumers[0].max_consumption_power = int(request.form['max_consumption_power'])
        tesla.balance_above = int(request.form['balance_above'])
        tesla.charge_until  = int(request.form['charge_until'])
        if 'set_home_location' in request.form:
            set_home_location = request.form['set_home_location']
            if set_home_location=='on':
                coords_current = db.get_tesla_current_coords()
                db.set_tesla_home_coords(coords_current[0],coords_current[1])
        return redirect(url_for('index'))
    else:
        coords_home = db.get_tesla_home_coords()
        coords_current = db.get_tesla_current_coords()
        osm = Nominatim(user_agent='TeslaPy')
        battery_level = tesla.battery_level
        if coords_home[0] == 0 and coords_home[1] == 0:
            location_home = "Nog niet ingesteld"
        else:
            coords_as_string = '%s, %s' % (coords_home[0],coords_home[1])
            location_home = osm.reverse(coords_as_string).address
        
        coords_as_string = '%s, %s' % (coords_current[0],coords_current[1])
        location_now = osm.reverse(coords_as_string).address
        return render_template('consumer_tesla.html', 
            max_consumption_power = data_model.get_consumer("Tesla").max_consumption_power,
            balance_above         = tesla.balance_above,
            charge_until          = tesla.charge_until,
            latitude_home         = coords_home[0],
            longitude_home        = coords_home[1],   
            latitude_curr         = coords_current[0],
            longitude_curr        = coords_current[1],
            location_now          = location_now,
            location_home         = location_home,
            battery_level         = battery_level,
            est_battery_range     = tesla.est_battery_range
        )




###
#    Web API routings
###

@app.route('/data/get', methods=['GET'])
def get_data():
    json_text = jsonify(
        {'surplus': data_model.surplus},
        {'current_consumption':data_model.current_consumption},
        {'current_production': data_model.current_production},
        {'charging_tesla_amp':data_model.get_consumer("Tesla").consumption_amps_now},
        {'charging_tesla_watt':data_model.get_consumer("Tesla").consumption_power_now}
        )
    return json_text

@app.route('/surplus/get', methods=['GET'])
def get_surplus():
    return jsonify({'value': data_model.surplus})

@app.route('/current_consumption/get', methods=['GET'])
def get_current_consumption():
    return jsonify({'value': data_model.current_consumption})

@app.route('/current_production/get', methods=['GET'])
def get_current_production():
    return jsonify({'value': data_model.current_production})


# 
@app.route('/balance/set/<int:value>/<string:consumer_name>', methods=['GET'])
def put_balance(value, consumer_name):
    try:
        logger.info("Setting balance to " + str(value))
        db.set_consumer_balance(consumer_name, value)
        data_model.get_consumer(consumer_name).balance_activated = value == 1
        return jsonify({'result': 'Ok'})
    except Exception as e:
        logger.exception(e)
        return jsonify({'result': 'Error: ' + e})



if __name__ == "__main__":
    app.run(host='0.0.0.0',port=8081,debug=True)
    # app.run(host='0.0.0.0',port=8081,debug=True, use_debugger=False, use_reloader=False, passthrough_errors=True)
