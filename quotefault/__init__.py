# import all relevant packages
import os
import subprocess
from datetime import datetime

import requests
from flask import Flask, render_template, request, flash, session, make_response
from flask_pyoidc.flask_pyoidc import OIDCAuthentication
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# look for a config file to associate with a db/port/ip/servername
if os.path.exists(os.path.join(os.getcwd(), "config.py")):
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.py"))
else:
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.env.py"))
db = SQLAlchemy(app)

# Disable SSL certificate verification warning
requests.packages.urllib3.disable_warnings()

# Disable SQLAlchemy modification tracking
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
auth = OIDCAuthentication(app,
                          issuer=app.config['OIDC_ISSUER'],
                          client_registration_info=app.config['OIDC_CLIENT_CONFIG'])

app.secret_key = 'submission'  # allows message flashing, var not actually used


# create the quote table with all relevant columns
class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    submitter = db.Column(db.String(80))
    quote = db.Column(db.String(200), unique=True)
    speaker = db.Column(db.String(50))
    quoteTime = db.Column(db.DateTime)

    # initialize a row for the Quote table
    def __init__(self, submitter, quote, speaker):
        self.quoteTime = datetime.now()
        self.submitter = submitter
        self.quote = quote
        self.speaker = speaker


def get_metadata():
    uuid = str(session["userinfo"].get("sub", ""))
    uid = str(session["userinfo"].get("preferred_username", ""))
    version = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('utf-8').rstrip()
    metadata = {
        "uuid": uuid,
        "uid": uid,
        "version": version
    }
    return metadata


# run the main page by creating the table(s) in the CSH serverspace and rendering the mainpage template
@app.route('/', methods=['GET'])
@auth.oidc_auth
def main():
    db.create_all()
    metadata = get_metadata()
    if request.cookies.get('flag'):
        return render_template('flag/main.html', metadata=metadata)
    else:
        return render_template('bootstrap/main.html', metadata=metadata)


@app.route('/settings', methods=['GET'])
@auth.oidc_auth
def settings():
    metadata = get_metadata()
    if request.cookies.get('flag'):
        return render_template('flag/settings.html', metadata=metadata)
    else:
        return render_template('bootstrap/settings.html', metadata=metadata)


@app.route('/settings', methods=['POST'])
@auth.oidc_auth
def update_settings():
    metadata = get_metadata()
    if request.form['template'] == "flag":
        resp = make_response(render_template('flag/settings.html', metadata=metadata))
        resp.set_cookie('flag', 'true')
        return resp
    else:
        resp = make_response(render_template('bootstrap/settings.html', metadata=metadata))
        resp.set_cookie('flag', 'false', expires=0)
        return resp


# run when the form submission button is clicked
@app.route('/submit', methods=['POST'])
@auth.oidc_auth
def submit():
    if request.method == 'POST':
        submitter = session['userinfo'].get('preferred_username',
                                            '')  # submitter will grab UN from OIDC when linked to it
        metadata = get_metadata()
        quote = request.form['quoteString']
        speaker = request.form['nameString']
        quoteCheck = Quote.query.filter(Quote.quote == quote).first()  # check for quote duplicate
        # checks for empty quote or submitter
        if quote == '' or speaker == '':
            flash('Empty quote or speaker field, try again!', 'error')
            if request.cookies.get('flag'):
                return render_template('flag/main.html', metadata=metadata), 200
            else:
                return render_template('bootstrap/main.html', metadata=metadata), 200
        elif quoteCheck is None:  # no duplicate quotes, proceed with submission
            # create a row for the Quote table
            new_quote = Quote(submitter=submitter, quote=quote, speaker=speaker)
            db.session.add(new_quote)
            db.session.flush()
            # upload the quote
            db.session.commit()
            # create a message to flash for successful submission
            flash('Submission Successful!')
            # return something to complete submission
            if request.cookies.get('flag'):
                return render_template('flag/main.html', metadata=metadata), 200
            else:
                return render_template('bootstrap/main.html', metadata=metadata), 200
        else:  # duplicate quote found, bounce the user back to square one
            flash('Quote already submitted!', 'warning')
            if request.cookies.get('flag'):
                return render_template('flag/main.html', metadata=metadata), 200
            else:
                return render_template('bootstrap/main.html', metadata=metadata), 200


# display stored quotes
@app.route('/storage', methods=['GET'])
@auth.oidc_auth
def get():
    quotes = Quote.query.all()  # collect all quote rows in the Quote db
    # create a list to display on the templete using a formatted version of each row as individual items
    quote_lst_new = []
    quote_lst_old = []  # for quotes older than a month, reduces clutter by hiding these behind a collapsable section
    quoteCount = 0
    metadata = get_metadata()
    for quote_obj in reversed(quotes):
        if quoteCount < 20:
            quote_lst_new.append(quote_obj)
            quoteCount += 1
        else:
            quote_lst_old.append(quote_obj)
    if request.cookies.get('flag'):
        return render_template('flag/storage.html', newQuotes=quote_lst_new, oldQuotes=quote_lst_old,
                               metadata=metadata)
    else:
        return render_template('bootstrap/storage.html', newQuotes=quote_lst_new, oldQuotes=quote_lst_old,
                               metadata=metadata)
