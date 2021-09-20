#!/usr/bin/env python
# encoding: utf-8
# import argparse
import logging
from typing import overload
from flask import Flask, request, jsonify, render_template, url_for, flash, redirect
from model import model
from persistence import persistence
from service.tesla_energy_consumer import tesla_energy_consumer
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'HeelLekkerbeLangrijk'

db = persistence()
data_model = model(db)
consumer = tesla_energy_consumer(db) 
data_model.add_consumer(consumer)


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
    if (data_model.override == 1):
        _override_checked = "checked"
    else:
        _override_checked = ""
    return render_template('index.html', 
        model=data_model, 
        override_checked=_override_checked,
        surplus_delay_theshold=data_model.surplus_delay_theshold,
        deficient_delay_theshold=data_model.deficient_delay_theshold
    )    


@app.route('/settings', methods=['GET','POST'])
def settings():
    if request.method == 'POST':
        data_model.surplus_delay_theshold = int(request.form['surplus_delay_theshold'])
        data_model.deficient_delay_theshold = int(request.form['deficient_delay_theshold'])
        return redirect(url_for('index'))
    else:
        return render_template('settings.html', 
        surplus_delay_theshold   =data_model.surplus_delay_theshold,
        deficient_delay_theshold =data_model.deficient_delay_theshold
        )

@app.route('/consumer', methods=['GET','POST'])
def consumer():
    if request.method == 'POST':
        data_model._consumers[0].consumption = int(request.form['consumption'])
        data_model._consumers[0].start_above = int(request.form['start_above'])
        data_model._consumers[0].stop_under  = int(request.form['stop_under'])
        return redirect(url_for('index'))
    else:
        return render_template('consumer.html', 
        consumption   = data_model._consumers[0].consumption,
        start_above   = data_model._consumers[0].start_above,
        stop_under    = data_model._consumers[0].stop_under
        )

@app.route('/data/get', methods=['GET'])
def get_data():
    return jsonify(
        {'surplus': data_model.surplus},
        {'surplus_delay_count':data_model.surplus_delay_count},
        {'current_consumption':data_model.current_consumption},
        {'current_production': data_model.current_production},
        {'deficient_delay_theshold':data_model.deficient_delay_theshold},
        {'surplus_delay_theshold':data_model.surplus_delay_theshold},
        {'override':data_model.override}
        )


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
        data_model.surplus_delay_theshold = request.data
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


@app.route('/override/get', methods=['GET'])
def get_override():
    return jsonify({'value': data_model.override})


@app.route('/override/set/<int:value>', methods=['GET'])
def put_override(value):
    try:
        data_model.override = value
        return jsonify({'result': 'Ok'})
    except:
        return jsonify({'result': 'Error'})

import net_balancer.web_api


if __name__ == "__main__":
    app.run(host='0.0.0.0',port=8081,debug=True)
    # app.run(host='0.0.0.0',port=8081,debug=True, use_debugger=False, use_reloader=False, passthrough_errors=True)
