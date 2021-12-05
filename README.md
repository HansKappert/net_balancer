
## Installeer software

sudo apt-get install python-pip
pip install -r requirements.txt
pip install setuptools
pip install -e .

export FLASK_APP=<path naar /net_balancer/src/net_balancer map>
export FLASK_ENV=development
flask run

## maken package:

Zie https://packaging.python.org/tutorials/packaging-projects/ 
1. verhoog versienummer aan in setup.cfg
2. activeer de venv met 
source venv/bin/activate
3. python3 -m build

## upload naar TestPyPI
1. activeer de venv met 
source venv/bin/activate
2. python3 -m twine upload --repository testpypi dist/*

## achtergron info
Dit project gebruikt kennis en stukjes code die Gé Janssen heeft geschreven om de slimme meter uit te lezen. Dank voor de input. Zie het werk van Gé dat hij hiervoor heeft gemaakt op:
http://gejanssen.com/howto/Slimme-meter-uitlezen/index.html
en
http://gejanssen.com/howto/rpi-rrd-power/index.html

Daarnaast maakt het project gebruik van de Teslapi library, met een kleine aanpassing om het te laten werken op Python 3.7


Niet limitatieve lijst van bronnen die gebruikt zijn bij de realisatie van dit project:
https://www.digitalocean.com/community/tutorials/how-to-make-a-web-application-using-flask-in-python-3
https://flask.palletsprojects.com/en/2.0.x/patterns/packages/

