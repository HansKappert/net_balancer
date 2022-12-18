import logging
import os
import time
import tempfile
from flask                           import Flask, request, jsonify, render_template, send_file, url_for, redirect
from flask.logging                   import default_handler
from geopy.geocoders                 import Nominatim
from datetime                        import datetime,timedelta

from common.model                    import model
from common.persistence              import persistence
from common.database_logging_handler import database_logging_handler
from service.tesla_energy_consumer   import tesla_energy_consumer


# See reference webite for Flots: https://humblesoftware.com/flotr2/documentation
# and the project itself on https://github.com/HumbleSoftware/Flotr2

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

mylogger = logging.getLogger(__name__)

app.logger.removeHandler(default_handler)

streamlog_handler = logging.StreamHandler()
streamlog_handler.setLevel(logging.DEBUG)
# app.logger.addHandler(streamlog_handler)

dblog_handler = database_logging_handler(db)
dblog_handler.setLevel(logging.INFO)
# app.logger.addHandler(dblog_handler)

for logger in (    app.logger,    mylogger):
    logger.addHandler(streamlog_handler)
    logger.addHandler(dblog_handler)


mylogger.info("Web app ready to receive requests")
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
        data_model.stats_retention = int(request.form['stats_retention'])
        return redirect(url_for('index'))
    else:
        return render_template('settings.html', 
        log_retention   = data_model.log_retention, 
        stats_retention = data_model.stats_retention
        )

@app.route('/download_db_file')
def download_db_file():
    file_name = os.path.join(os.path.dirname(os.path.abspath(__file__)),"energy_mediator.db")
    if os.path.isfile(file_name):
        return send_file(file_name, as_attachment=True)
    else:
        app.logger.error(f"Cannot find database file at {file_name}")


@app.route('/download_csv_file')
def download_csv_file():
    tmp_path = tempfile.gettempdir()
    file_name = os.path.join(tmp_path, "stats.csv")
    app.logger.info(f"Writing csv file to: {file_name}")
    stats_retention_days = db.get_stats_retention()
    data = db.get_history(stats_retention_days * 24 * 60)
    with  open(file_name, "w") as f: 
        app.logger.info(f"Writing data to temporary file {file_name}")
        f.write("timestamp;production;consumption;tesla_consumption;cost_price;profit_price;cost;profit;tesla_cost;gas_reading\n")
        for row in data:
            dt = datetime.fromtimestamp(int(row[0])).strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{dt};{row[1]};{row[2]};{row[3]};{row[4]};{row[5]};{row[6]};{row[7]};{row[8]};{row[9]}\n")
        f.close()
    if os.path.isfile(file_name):
        return send_file(file_name, as_attachment=True)
    else:
        app.logger.error(f"Cannot find the file ({file_name}) I just created!")


@app.route('/download_cum_csv_file')
def download_cum_csv_file():
    tmp_path = tempfile.gettempdir()
    file_name = os.path.join(tmp_path, "cum_stats.csv")
    app.logger.info(f"Writing csv file to: {file_name}")
    data = db.get_cum_stats()
    with  open(file_name, "w") as f: 
        app.logger.info(f"Writing data to temporary file {file_name}")
        f.write("year;month;day;hour;current_production;current_consumption;tesla_consumption;cost_price;profit_price;cost;profit;tesla_cost;gas_consumption\n")
        for row in data:
            f.write(f"{row[0]};{row[1]};{row[2]};{row[3]};{row[4]};{row[5]};{row[6]};{row[7]};{row[8]};{row[9]};{row[10]};{row[11]};{row[12]}\n")
        f.close()
    if os.path.isfile(file_name):
        return send_file(file_name, as_attachment=True)
    else:
        app.logger.error(f"Cannot find the file ({file_name}) I just created!")



@app.route('/kwh_history', methods=['GET','POST'])
def kwh_history():
    if request.method == 'POST':
        minutes = int(request.form["minutes"])
    else:
        minutes = 60

    history = db.get_history(minutes)
    app.logger.info(f"Got {len(history)} records from the database.")
    productions        = '['
    consumptions       = '['
    tesla_consumptions = '['
    datetime_str = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    
    if len(history) > 0:
        datetime_obj = datetime.fromtimestamp(history[0][0])
        datetime_str = datetime_obj.strftime("%Y/%m/%d %H:%M:%S")

        for i in history:
            msec_since = str(i[0] )
            productions        += '[' + msec_since + ',' + str(i[1]) + '],'
            consumptions       += '[' + msec_since + ',' + str(i[2]) + '],'
            tesla_consumptions += '[' + msec_since + ',' + str(i[3]) + '],'
        
    consumptions       =       consumptions.strip(',') + ']'
    productions        =        productions.strip(',') + ']'
    tesla_consumptions = tesla_consumptions.strip(',') + ']'
    
    return render_template('kwh_history.html', 
                            start_datetime_str = datetime_str, 
                            consumptions       = consumptions, 
                            productions        = productions, 
                            tesla_consumptions = tesla_consumptions,
                            minutes            = minutes)


@app.route('/euro_history', methods=['GET','POST'])
def euro_history():
    today = datetime.strptime(datetime.today().strftime("%Y-%m-%d"),"%Y-%m-%d")
    if request.method == 'POST':
        datum = datetime.strptime(request.form["datum"],"%Y-%m-%d")
        if "go" in request.form:
            if request.form["go"] == "eerder":
                datum = datum + timedelta(days=-1)
            if request.form["go"] == "later":
                datum = datum + timedelta(days=1)
    else:
        datum = today

    hour = 0
    profits     = '['
    costs       = '['
    tesla_costs = '['
    gas_usages  = '['

    total_costs   = 0.0
    total_profits = 0.0
    total_tesla   = 0.0
    total_gas     = 0.0
    
    while hour <= 23:
        c = 0.0
        p = 0.0
        t = 0.0
        g = 0.0
        has_data_this_hour = False

        if datum < today:
            date_hour = datum + timedelta(hours=hour)
            summarized_data = db.get_cum_stats_for_date_hour(date_hour)
            if len(summarized_data) == 1:
                for row in summarized_data: # typically 1 row.
                        c = row[9]  if row[9] else 0.0
                        p = row[10] if row[10] else 0.0
                        t = row[11] if row[11] else 0.0
                        g = row[12] if row[12] else 0.0
                app.logger.debug(f"hour {hour} : costs {str(c)}, profits {str(p)}, tesla_costs {str(t)}, gas {str(g)}")
                has_data_this_hour = True
        else:
            if datetime.now().hour >= hour:
                from_dt  = datetime(datum.year,datum.month,datum.day,hour,0,0)
                until_dt = datetime(datum.year,datum.month,datum.day,hour,59,59)
                summarized_data  = db.get_summarized_euro_history_from_to(from_dt,until_dt)
            
                if len(summarized_data) == 1:
                    for row in summarized_data: # typically 1 row.
                        c = row[0] if row[0] else 0.0
                        p = row[1] if row[1] else 0.0
                        t = row[2] if row[2] else 0.0
                        g = row[3] if row[3] else 0.0
                    app.logger.debug(f"hour {hour} (from {from_dt} until {until_dt}) : costs {str(c)}, profits {str(p)}, tesla_costs {str(t)}, gas {str(g)}")
                    has_data_this_hour = True
        if has_data_this_hour:
            costs       += '[' + str(hour) + ',' + str(c) + '],'
            profits     += '[' + str(hour) + ',' + str(p) + '],'
            tesla_costs += '[' + str(hour) + ',' + str(t) + '],'
            gas_usages  += '[' + str(hour) + ',' + str(g) + '],'
            total_costs   = total_costs   + c
            total_profits = total_profits + p 
            total_tesla   = total_tesla   + t
            total_gas     = total_gas     + g
        hour += 1
    costs       = costs.strip(',')       + ']'
    profits     = profits.strip(',')     + ']'
    tesla_costs = tesla_costs.strip(',') + ']'
    gas_usages  = gas_usages.strip(',')   + ']'
    
    datum = datum.strftime("%Y-%m-%d")

    total_netto   = total_costs - total_tesla

    total_costs   = f"€{round(total_costs  ,4)}"
    total_profits = f"€{round(total_profits,4)}"
    total_tesla   = f"€{round(total_tesla  ,4)}"
    total_netto   = f"€{round(total_netto  ,4)}"
    total_gas     = f"€{round(total_gas    ,3)}"
    return render_template('euro_history.html', 
                            costs         = costs, 
                            profits       = profits, 
                            tesla_costs   = tesla_costs,
                            datum         = datum,
                            total_costs   = total_costs,
                            total_profits = total_profits,
                            total_tesla   = total_tesla,
                            total_netto   = total_netto,
                            gas_usages    = gas_usages,
                            total_gas     = total_gas
                            )


@app.route('/gas_usage_history', methods=['GET','POST'])
def gas_usage_history():
    today = datetime.strptime(datetime.today().strftime("%Y-%m-%d"),"%Y-%m-%d")
    if request.method == 'POST':
        datum = datetime.strptime(request.form["datum"],"%Y-%m-%d")
        if "go" in request.form:
            if request.form["go"] == "eerder":
                datum = datum + timedelta(days=-1)
            if request.form["go"] == "later":
                datum = datum + timedelta(days=1)
    else:
        datum = today

    hour = 0
    gas_usages   = '['

    total_gas     = 0.0
    
    while hour <= 23:
        g = 0.0
        has_data_this_hour = False

        if datum < today:
            date_hour = datum + timedelta(hours=hour)
            summarized_data = db.get_cum_stats_for_date_hour(date_hour)
            if len(summarized_data) == 1:
                for row in summarized_data: # typically 1 row.
                        g = row[12] if row[12] else 0.0
                app.logger.debug(f"gas {str(g)}")
                has_data_this_hour = True
        else:
            if datetime.now().hour >= hour:
                from_dt  = datetime(datum.year,datum.month,datum.day,hour,0,0)
                until_dt = datetime(datum.year,datum.month,datum.day,hour,59,59)
                summarized_data  = db.get_summarized_euro_history_from_to(from_dt,until_dt)
            
                if len(summarized_data) == 1:
                    for row in summarized_data: # typically 1 row.
                        g = row[3] if row[3] else 0.0
                    app.logger.debug(f"hour {hour} (from {from_dt} until {until_dt}) : gas {str(g)}")
                    has_data_this_hour = True
        if has_data_this_hour:
            gas_usages   += '[' + str(hour) + ',' + str(g) + '],'
            total_gas     = total_gas     + g
        hour += 1
    gas_usages   = gas_usages.strip(',')   + ']'
    
    datum = datum.strftime("%Y-%m-%d")

    total_gas   = f"{round(total_gas  ,4)}m3"
    return render_template('gas_usage_history.html', 
                            datum         = datum,
                            gas_usages    = gas_usages,
                            total_gas     = total_gas
                            )


@app.route('/prices', methods=['GET','POST'])
def prices():
    if request.method == 'POST':
        datum = datetime.strptime(request.form["datum"],"%Y-%m-%d")
        if "go" in request.form:
            if request.form["go"] == "eerder":
                datum = datum + timedelta(days=-1)
            if request.form["go"] == "later":
                datum = datum + timedelta(days=1)
    else:
        datum = datetime.strptime(datetime.today().strftime("%Y-%m-%d"),"%Y-%m-%d")

    price_history = db.get_day_prices(datum)
    prices = '['
    if len(price_history) > 0:
        for row in price_history:
            dt = datetime.fromtimestamp(int(row[0]))
            hour = dt.hour        
            prices += f'[{hour},{row[1]}],'
    prices = prices.strip(',') + ']'
    ddatum = datum.strftime("%Y-%m-%d")
    return render_template('prices.html', datum=ddatum, prices = prices)
  

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
        print("Setting balance to " + str(value))
        db.set_consumer_balance(consumer_name, value)
        data_model.get_consumer(consumer_name).balance_activated = value == 1
        return jsonify({'result': 'Ok'})
    except Exception as e:
        logger.exception(e)
        return jsonify({'result': 'Error: ' + e})



if __name__ == "__main__":
    app.run(host='0.0.0.0',port=8081,debug=True)
    # app.run(host='0.0.0.0',port=8081,debug=True, use_debugger=False, use_reloader=False, passthrough_errors=True)
