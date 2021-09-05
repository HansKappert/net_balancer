#!/usr/bin/env python
# encoding: utf-8
# import argparse
import logging
from typing import overload
from flask import Flask, request, jsonify, render_template, url_for, flash, redirect
from model import model
from persistence import persistence
from service.tesla_energy_consumer import tesla_energy_consumer

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
        lines=log_lines
    )    


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
        return redirect(url_for('index'))
    else:
        return render_template('consumer.html', 
        consumption   =data_model._consumers[0].consumption
        )


import net_balancer.web_api


if __name__ == "__main__":

    """ 
    ap = argparse.ArgumentParser()
    ap.add_argument("-u", "--user_email", type=str,
                    help="Tesla account user name (e-mail address)")
    ap.add_argument("-p", "--password", type=str,
                    help="Password of the Tesla account")
    ap.add_argument("-l", "--loglevel", type=str,
                    help="logging level: d=debug, i=info, w=warning, e=error")
    ap.add_argument("-d", "--device_name", type=str,
                        help="tty device name as listed by ls /dev/tt*")
    args = ap.parse_args()

    default_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    if args.loglevel == None or args.loglevel == 'i':
        logging.basicConfig(level=logging.INFO, format=default_format)
    elif args.loglevel == 'd':
        logging.basicConfig(level=logging.DEBUG, format=default_format)
    elif args.loglevel == 'w':
        logging.basicConfig(level=logging.WARN, format=default_format)
    elif args.loglevel == 'e':
        logging.basicConfig(level=logging.ERROR, format=default_format)
        
    if (args.user_email == None or args.password == None):
        print("Please specify your Tesla account credentials")
        quit()

    if (args.device_name == None):
        print("Please specify the Smart Meter device name")
        quit()

    logging.debug ("User name    : " + args.user_email)
    logging.debug ("User password is secret, remember")
    """

    app.run(host='0.0.0.0',port=8081,debug=True)
    # app.run(host='0.0.0.0',port=8081,debug=True, use_debugger=False, use_reloader=False, passthrough_errors=True)
