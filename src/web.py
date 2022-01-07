from flask import Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'HeelLekkerbeLangrijk'

import web_pages

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=8081,debug=True)
    # app.run(host='0.0.0.0',port=8081,debug=True, use_debugger=False, use_reloader=False, passthrough_errors=True)
