# slimmemeter-rpi
zie ook

http://gejanssen.com/howto/Slimme-meter-uitlezen/index.html
en
http://gejanssen.com/howto/rpi-rrd-power/index.html

## Installeer software

sudo apt-get install python-pip
pip install -r requirements.txt
pip install setuptools
pip install -e .

export FLASK_APP=/home/pi/net_balancer/net_balancer
export FLASK_ENV=development
flask run

Gebruikte informatie van:
https://www.digitalocean.com/community/tutorials/how-to-make-a-web-application-using-flask-in-python-3
https://flask.palletsprojects.com/en/2.0.x/patterns/packages/
