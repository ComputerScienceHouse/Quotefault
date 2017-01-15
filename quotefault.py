from flask import Flask, url_for
from flask import render_template
from flask import request
from datetime import datetime
app = Flask(__name__)

@app.route('/', methods=['GET'])
def main():
    return render_template('quotefaultmainpage.html')
    if request.method == 'GET':
        quoteComplete = "\"" + request.form.quoteString + "\" - " + request.form.nameString
        quoteTime = datetime.now()