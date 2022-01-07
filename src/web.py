from flask import Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'HeelLekkerbeLangrijk'
import web_pages
