#!/usr/bin/env python
# encoding: utf-8
import logging
import os 

from web import app

from typing import overload
from flask import Flask, request, jsonify, render_template, url_for, flash, redirect
from flask.templating import Environment

from common.model import model
from common.persistence import persistence
from common.database_logging_handler import database_logging_handler

from service.tesla_energy_consumer import tesla_energy_consumer

from geopy.geocoders import Nominatim

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
    if (db.get_consumer_override('Tesla') == 1):
        _override_tesla = "checked"
    else:
        _override_tesla = ""

    if (db.get_consumer_disabled('Tesla') == 1):
        _disabled_tesla = "checked"
    else:
        _disabled_tesla = ""

    return render_template('index.html', 
        model=data_model, 
        override_tesla=_override_tesla,
        disabled_tesla=_disabled_tesla,
        surplus_delay_theshold=data_model.log_retention,
        deficient_delay_theshold=data_model.deficient_delay_theshold
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

@app.route('/consumer_tesla', methods=['GET','POST'])
def consumer_tesla():
    if request.method == 'POST':
        data_model._consumers[0].consumption = int(request.form['consumption'])
        tesla.charge_until = int(request.form['charge_until'])
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
        consumption     = data_model._consumers[0].consumption,
        charge_until    = tesla.charge_until,
        latitude_home   = coords_home[0],
        longitude_home  = coords_home[1],   
        latitude_curr   = coords_current[0],
        longitude_curr  = coords_current[1],
        location_now    = location_now,
        location_home   = location_home,
        battery_level   = battery_level
        )

@app.route('/data/get', methods=['GET'])
def get_data():
    json_text = jsonify(
        {'surplus': data_model.surplus},
        {'surplus_delay_count':data_model.surplus_delay_count},
        {'current_consumption':data_model.current_consumption},
        {'current_production': data_model.current_production},
        {'deficient_delay_theshold':data_model.deficient_delay_theshold},
        {'charging_tesla_amp':db.get_consumer_consumption_now("Tesla")},
        {'charging_tesla_watt':230*db.get_consumer_consumption_now("Tesla")}
        )
    return json_text

@app.route('/surplus/get', methods=['GET'])
def get_surplus():
    return jsonify({'value': data_model.surplus})

@app.route('/surplus_delay_count/get', methods=['GET'])
def get_surplus_delay_count():
    return jsonify({'value': data_model.surplus_delay_count})

@app.route('/deficient_delay_count/get', methods=['GET'])
def get_deficient_delay_count():
    return jsonify({'value': data_model.deficient_delay_count})

@app.route('/current_consumption/get', methods=['GET'])
def get_current_consumption():
    return jsonify({'value': data_model.current_consumption})

@app.route('/current_production/get', methods=['GET'])
def get_current_production():
    return jsonify({'value': data_model.current_production})

@app.route('/deficient_delay_theshold/get', methods=['GET'])
def get_deficient_delay_theshold():
    return jsonify({'value': data_model.deficient_delay_theshold})

@app.route('/surplus_delay_theshold/set', methods=['GET'])
def put_surplus_delay_theshold():
    value = request.args.get('value')
    try:
        value = int(value)
        data_model.log_retention = request.data
        return jsonify({'result': 'Ok'})
    except:
        return jsonify({'result': 'Error'})

@app.route('/deficient_delay_theshold/set/<int:value>', methods=['GET'])
def put_deficient_delay_theshold(value):
    try:
        data_model.deficient_delay_theshold = value
        return jsonify({'result': 'Ok'})
    except:
        return jsonify({'result': 'Error'})


#@app.route('/override/get', methods=['GET'])
#def get_override():    
#    return jsonify({'value': data_model.override})


@app.route('/override/set/<int:value>/<string:consumer_name>', methods=['GET'])
def put_override(value, consumer_name):
    try:
        logger.info("Setting override to " + str(value))
        db.set_consumer_override(consumer_name, value)
        return jsonify({'result': 'Ok'})
    except Exception as e:
        logger.exception(e)
        return jsonify({'result': 'Error'})

@app.route('/disabled/set/<int:value>/<string:consumer_name>', methods=['GET'])
def put_disabled(value, consumer_name):
    try: 
        if value == 1:
            logger.info("Disabling energy mediation for  " + consumer_name)
        else:
            logger.info("Enabling energy mediation for  "  + consumer_name)
        db.set_consumer_disabled(consumer_name, value)
        return jsonify({'result': 'Ok'})
    except Exception as e:
        logger.exception(e)
        return jsonify({'result': 'Error'})

import web_api



if __name__ == "__main__":
    app.run(host='0.0.0.0',port=8081,debug=True)
    # app.run(host='0.0.0.0',port=8081,debug=True, use_debugger=False, use_reloader=False, passthrough_errors=True)
