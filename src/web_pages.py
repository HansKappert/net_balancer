from web             import app, db, data_model, tesla
from flask           import request, render_template, url_for, redirect
from geopy.geocoders import Nominatim

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


