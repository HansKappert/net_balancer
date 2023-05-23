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

data_model = model(db)
tesla = tesla_energy_consumer(db)

tesla_user = os.environ["TESLA_USER"]
try:
    tesla.initialize(email=tesla_user)
    data_model.add_consumer(tesla)
except Exception as e:
    logging.exception(e)


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
            line = dt + ";{0};{1};{2};{3:.2f};{4:.2f};{5:.7f};{6:.7f};{7:.7f};{8:.2f}\n".format(row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9] if row[9] else 0)
            line = line.replace('.',',')
            f.write(line)
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
            line = "{0};{1};{2};{3};{4};{5};{6};{7:.2f};{8:.2f};{9:.7f};{10:.7f};{11:.7f};{12:.2f}\n".format(row[0],row[1],row[2],row[3],
            row[4]  if row[4] else 0,
            row[5]  if row[5] else 0,
            row[6]  if row[6] else 0,
            row[7]  if row[7] else 0,
            row[8]  if row[8] else 0,
            row[9]  if row[9] else 0,
            row[10] if row[10] else 0,
            row[11] if row[11] else 0,
            row[12] if row[12] else 0)
            line = line.replace('.',',')
            f.write(line)
        f.close()
    if os.path.isfile(file_name):
        return send_file(file_name, as_attachment=True)
    else:
        app.logger.error(f"Cannot find the file ({file_name}) I just created!")



@app.route('/kwh_now', methods=['GET','POST'])
def kwh_now():
    if request.method == 'POST':
        minutes = int(request.form["minutes"])
    else:
        minutes = 60

    history = db.get_history(minutes)
    app.logger.info(f"Page: kwh_now received {len(history)} records from the database.")
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
    
    return render_template('kwh_now.html', 
                            start_datetime_str = datetime_str, 
                            consumptions       = consumptions, 
                            productions        = productions, 
                            tesla_consumptions = tesla_consumptions,
                            minutes            = minutes)

def get_cum_data(datum, today):
    hour = 0
    profits         = '['
    costs           = '['
    tesla_costs     = '['
    gas_usages      = '['
    el_consumptions = '['
    el_deliveries   = '['
    el_consumptions_tesla = '['

    total_costs     = 0.0
    total_profits   = 0.0
    total_tesla     = 0.0
    total_gas       = 0.0
    total_el_cons   = 0.0
    total_el_deliv  = 0.0
    total_el_cons_tesla = 0.0

    while hour <= 24:
        c = 0.0
        p = 0.0
        t = 0.0
        g = 0.0
        elc = 0.0 # electricity consumption
        eld = 0.0 # electricity delivery
        elt = 0.0 # electricity consumption for tesla
        has_data_this_hour = False

        prev_hour = datetime.now() - timedelta(hours=1)
        if datum <= today:
            date_hour = datum + timedelta(hours=hour)
            if date_hour > datetime.now():
                break
            if date_hour < prev_hour:
                summarized_data = db.get_cum_stats_for_date_hour(date_hour)
            else:
                summarized_data = db.get_stats_for_date_hour(date_hour)
            
            if len(summarized_data) == 1:
                for row in summarized_data: # typically 1 row.
                        eld = row[4]  if row[4] else 0.0
                        elc = row[5]  if row[5] else 0.0
                        elt = row[6]  if row[6] else 0.0
                        c   = row[9]  if row[9] else 0.0
                        p   = row[10] if row[10] else 0.0
                        t   = row[11] if row[11] else 0.0
                        g   = row[12] if row[12] else 0.0
                #app.logger.debug(f"hour {hour} : costs {str(c)}, profits {str(p)}, tesla_costs {str(t)}, gas {str(g)}")
                has_data_this_hour = True

        if has_data_this_hour:
            costs                 += '[' + str(hour) + ',' + str(c  ) + '],'
            profits               += '[' + str(hour) + ',' + str(p  ) + '],'
            tesla_costs           += '[' + str(hour) + ',' + str(t  ) + '],'
            el_consumptions       += '[' + str(hour) + ',' + str(elc) + '],'
            el_deliveries         += '[' + str(hour) + ',' + str(eld) + '],'
            el_consumptions_tesla += '[' + str(hour) + ',' + str(elt) + '],'
            gas_usages            += '[' + str(hour) + ',' + str(g  ) + '],'
            total_costs           += c
            total_profits         += p 
            total_tesla           += t
            total_gas             += g
            total_el_cons         += elc
            total_el_deliv        += eld
            total_el_cons_tesla   += elt
        hour += 1
    costs                 = costs.strip(',')           + ']'
    profits               = profits.strip(',')         + ']'
    tesla_costs           = tesla_costs.strip(',')     + ']'
    gas_usages            = gas_usages.strip(',')      + ']'
    el_consumptions       = el_consumptions.strip(',') + ']'
    el_consumptions_tesla = el_consumptions_tesla.strip(',') + ']'
    el_deliveries         = el_deliveries.strip(',')   + ']'
    total_netto           = total_costs - total_tesla - total_profits
    total_el_netto        = total_el_cons - total_el_cons_tesla - total_el_deliv
    total_costs           = f"{total_costs:.2f}"
    total_profits         = f"{total_profits:.2f}"
    total_tesla           = f"{total_tesla:.2f}"
    total_netto           = f"{total_netto:.2f}"
    total_gas             = f"{total_gas:.3f}"
    total_el_cons         = f"{total_el_cons:.1f}"
    total_el_cons_tesla   = f"{total_el_cons_tesla:.1f}"
    total_el_deliv        = f"{total_el_deliv:.1f}"
    total_el_netto        = f"{total_el_netto:.1f}"
    return costs,            \
            profits,         \
            tesla_costs,     \
            el_consumptions, \
            el_consumptions_tesla, \
            el_deliveries,   \
            gas_usages,      \
            datum,           \
            total_costs,     \
            total_profits,   \
            total_tesla,     \
            total_netto,     \
            total_gas,       \
            total_el_cons,   \
            total_el_deliv,   \
            total_el_cons_tesla, \
            total_el_netto

@app.route('/euro_history', methods=['GET','POST'])
def euro_history():
#    today = datetime.strptime(datetime.today().strftime("%Y-%m-%d"),"%Y-%m-%d")
    now = datetime.now()
    today = datetime(now.year, now.month, now.day, 0,0,0)
    if request.method == 'POST':
        datum = datetime.strptime(request.form["datum"],"%Y-%m-%d")
        if "go" in request.form:
            if request.form["go"] == "eerder":
                datum = datum + timedelta(days=-1)
            if request.form["go"] == "later":
                datum = datum + timedelta(days=1)
    else:
        datum = today

    (costs,
    profits, 
    tesla_costs,
    el_consumptions,
    el_consumptions_tesla,
    el_deliveries,
    gas_usages,
    datum,
    total_costs,
    total_profits,
    total_tesla,
    total_netto,
    total_gas,
    total_el_cons,
    total_el_deliv,
    total_el_cons_tesla,
    total_el_netto) = get_cum_data(datum, today)
    
    datum = datum.strftime("%Y-%m-%d")

    return render_template('euro_history.html', 
                            costs                 = costs, 
                            profits               = profits, 
                            tesla_costs           = tesla_costs,
                            el_consumptions       = el_consumptions,
                            el_consumptions_tesla = el_consumptions_tesla,
                            el_deliveries         = el_deliveries,
                            gas_usages            = gas_usages,
                            datum                 = datum,
                            total_costs           = total_costs,
                            total_profits         = total_profits,
                            total_tesla           = total_tesla,
                            total_netto           = total_netto,
                            total_gas             = total_gas,
                            total_el_cons         = total_el_cons,
                            total_el_deliv        = total_el_deliv,
                            total_el_cons_tesla   = total_el_cons_tesla,
                            total_el_netto        = total_el_netto
                            )


@app.route('/kwh_history', methods=['GET','POST'])
def kwh_history():
    #    today = datetime.strptime(datetime.today().strftime("%Y-%m-%d"),"%Y-%m-%d")
    now = datetime.now()
    today = datetime(now.year, now.month, now.day, 0,0,0)
    if request.method == 'POST':
        datum = datetime.strptime(request.form["datum"],"%Y-%m-%d")
        if "go" in request.form:
            if request.form["go"] == "eerder":
                datum = datum + timedelta(days=-1)
            if request.form["go"] == "later":
                datum = datum + timedelta(days=1)
    else:
        datum = today

    (costs,
    profits, 
    tesla_costs,
    el_consumptions,
    el_consumptions_tesla,
    el_deliveries,
    gas_usages,
    datum,
    total_costs,
    total_profits,
    total_tesla,
    total_netto,
    total_gas,
    total_el_cons,
    total_el_deliv,
    total_el_cons_tesla,
    total_el_netto) = get_cum_data(datum, today)
    
    datum = datum.strftime("%Y-%m-%d")

    return render_template('kwh_history.html', 
                            costs                 = costs, 
                            profits               = profits, 
                            tesla_costs           = tesla_costs,
                            el_consumptions       = el_consumptions,
                            el_consumptions_tesla = el_consumptions_tesla,
                            el_deliveries         = el_deliveries,
                            gas_usages            = gas_usages,
                            datum                 = datum,
                            total_costs           = total_costs,
                            total_profits         = total_profits,
                            total_tesla           = total_tesla,
                            total_netto           = total_netto,
                            total_gas             = total_gas,
                            total_el_cons         = total_el_cons,
                            total_el_deliv        = total_el_deliv,
                            total_el_cons_tesla   = total_el_cons_tesla,
                            total_el_netto        = total_el_netto
                            )


@app.route('/gas_usage_history', methods=['GET','POST'])
def gas_usage_history():
    #    today = datetime.strptime(datetime.today().strftime("%Y-%m-%d"),"%Y-%m-%d")
    now = datetime.now()
    today = datetime(now.year, now.month, now.day, 0,0,0)
    if request.method == 'POST':
        datum = datetime.strptime(request.form["datum"],"%Y-%m-%d")
        if "go" in request.form:
            if request.form["go"] == "eerder":
                datum = datum + timedelta(days=-1)
            if request.form["go"] == "later":
                datum = datum + timedelta(days=1)
    else:
        datum = today

    (costs,
    profits, 
    tesla_costs,
    el_consumptions,
    el_consumptions_tesla,
    el_deliveries,
    gas_usages,
    datum,
    total_costs,
    total_profits,
    total_tesla,
    total_netto,
    total_gas,
    total_el_cons,
    total_el_deliv,
    total_el_cons_tesla,
    total_el_netto) = get_cum_data(datum, today)
    
    datum = datum.strftime("%Y-%m-%d")

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
    total = 0
    prices = '['
    if len(price_history) > 0:
        for row in price_history:
            dt = datetime.fromtimestamp(int(row[0]))
            hour = dt.hour        
            total += row[1]
            prices += f'[{hour},{row[1]}],'
    prices = prices.strip(',') + ']'
    ddatum = datum.strftime("%Y-%m-%d")
    avg    = round(total/len(price_history),2) if len(price_history)>0 else 0
    return render_template('prices.html', 
                            datum=ddatum, 
                            prices = prices, 
                            avg= avg 
                            )
  

@app.route('/consumer_tesla', methods=['GET','POST'])
def consumer_tesla():
    if request.method == 'POST':
        data_model._consumers[0].max_consumption_power = int(request.form['max_consumption_power'])
        tesla.balance_above     = int(request.form['balance_above'])
        tesla.charge_until      = int(request.form['charge_until'])
        tesla.price_percentage  = int(request.form['price_percentage'])
        if 'set_home_location' in request.form:
            set_home_location = request.form['set_home_location']
            if set_home_location=='on':
                coords_current = db.get_tesla_current_coords()
                db.set_tesla_home_coords(coords_current[0],coords_current[1])
        return redirect(url_for('index'))
    else:
        coords_home = db.get_tesla_home_coords()
        coords_current = db.get_tesla_current_coords()
        price_percentage  = db.get_tesla_price_percentage()
        
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
            est_battery_range     = tesla.est_battery_range,
            price_percentage      = price_percentage
        )




###
#    Web API routings
###

@app.route('/data/get', methods=['GET'])
def get_data():
    if data_model.get_consumer("Tesla"):
        charging_tesla_amp    = data_model.get_consumer("Tesla").consumption_amps_now
        charging_tesla_watt   = data_model.get_consumer("Tesla").consumption_power_now
        charging_tesla_status = data_model.get_consumer("Tesla").status
    
    json_text = jsonify(
        {'surplus': data_model.surplus},
        {'current_consumption'   : data_model.current_consumption},
        {'current_production'    : data_model.current_production},
        {'charging_tesla_amp'    : charging_tesla_amp},
        {'charging_tesla_watt'   : charging_tesla_watt},
        {'charging_tesla_status' : charging_tesla_status}
        
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
