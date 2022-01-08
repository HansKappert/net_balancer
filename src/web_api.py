from web import app
from flask import Flask, jsonify

from web import app, db, data_model, logger
from flask import Flask, request, jsonify


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
