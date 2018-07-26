# import all relevant packages
import os
import subprocess
from datetime import datetime

import requests
from csh_ldap import CSHLDAP
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

# Create CSHLDAP connection
_ldap = CSHLDAP(app.config["LDAP_BIND_DN"],
                app.config["LDAP_BIND_PW"])

app.secret_key = 'submission'  # allows message flashing, var not actually used

from .ldap import get_all_members, ldap_get_member


# create the quote table with all relevant columns
class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    submitter = db.Column(db.String(80))
    quote = db.Column(db.String(200), unique=True)
    speaker = db.Column(db.String(50))
    quote_time = db.Column(db.DateTime)

    # initialize a row for the Quote table
    def __init__(self, submitter, quote, speaker):
        self.quote_time = datetime.now()
        self.submitter = submitter
        self.quote = quote
        self.speaker = speaker


def get_metadata():
    uuid = str(session["userinfo"].get("sub", ""))
    uid = str(session["userinfo"].get("preferred_username", ""))
    version = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('utf-8').rstrip()
    plug = request.cookies.get('plug')
    metadata = {
        "uuid": uuid,
        "uid": uid,
        "version": version,
        "plug": plug
    }
    return metadata


# run the main page by creating the table(s) in the CSH serverspace and rendering the mainpage template
@app.route('/', methods=['GET'])
@auth.oidc_auth
def main():
    db.create_all()
    metadata = get_metadata()
    all_members = get_all_members()
    if request.cookies.get('flag'):
        return render_template('flag/main.html', metadata=metadata)
    else:
        return render_template('bootstrap/main.html', metadata=metadata, all_members=all_members)


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
        resp.set_cookie('flag', 'True')
        return resp
    else:
        resp = make_response(render_template('bootstrap/settings.html', metadata=metadata))
        resp.set_cookie('flag', 'False', expires=0)
        if request.form['plug'] == "off":
            resp.set_cookie('plug', 'False')
        else:
            resp.set_cookie('plug', 'True', expires=0)
        return resp


# run when the form submission button is clicked
@app.route('/submit', methods=['POST'])
@auth.oidc_auth
def submit():
    # submitter will grab UN from OIDC when linked to it
    submitter = session['userinfo'].get('preferred_username', '')
    metadata = get_metadata()
    all_members = get_all_members()
    quote = request.form['quoteString']

    # standardises quotation marks to remove them
    if quote[0] == '"' or quote[0] == "'":
        quote = quote[1:]
    if quote[-1] == '"' or quote[-1] == "'":
        quote = quote[:-1]
    quote = '"' + quote + '"'

    speaker = request.form['nameString']
    # check for quote duplicate
    quoteCheck = Quote.query.filter(Quote.quote == quote).first()

    # checks for empty quote or submitter
    if quote == '' or speaker == '':
        flash('Empty quote or speaker field, try again!', 'error')
        if request.cookies.get('flag'):
            return render_template('flag/main.html', metadata=metadata), 200
        return render_template('bootstrap/main.html', metadata=metadata, all_members=all_members), 200
    elif submitter == speaker:
        flash('You can\'t quote yourself! Come on', 'error')
        if request.cookies.get('flag'):
            return render_template('flag/main.html', metadata=metadata), 200
        return render_template('bootstrap/main.html', metadata=metadata, all_members=all_members), 200
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
        return render_template('bootstrap/main.html', metadata=metadata, all_members=all_members), 200
    else:  # duplicate quote found, bounce the user back to square one
        flash('Quote already submitted!', 'warning')
        if request.cookies.get('flag'):
            return render_template('flag/main.html', metadata=metadata), 200
        return render_template('bootstrap/main.html', metadata=metadata, all_members=all_members), 200


# display stored quotes
@app.route('/storage', methods=['GET'])
@auth.oidc_auth
def get():
    metadata = get_metadata()
    metadata['submitter'] = request.args.get('submitter')  # get submitter from url query string
    metadata['speaker'] = request.args.get('speaker')  # get submitter from url query string

    if metadata['speaker'] is not None and metadata['submitter'] is not None:
        quotes = Quote.query.order_by(Quote.quote_time.desc()).filter(Quote.submitter == metadata['submitter'],
                                                                     Quote.speaker == metadata['speaker']).all()
    elif metadata['submitter'] is not None:
        quotes = Quote.query.order_by(Quote.quote_time.desc()).filter(Quote.submitter == metadata['submitter']).all()
    elif metadata['speaker'] is not None:
        quotes = Quote.query.order_by(Quote.quote_time.desc()).filter(Quote.speaker == metadata['speaker']).all()
    else:
        quotes = Quote.query.order_by(Quote.quote_time.desc()).limit(20).all()  # collect all quote rows in the Quote db

    if request.cookies.get('flag'):
        return render_template('flag/storage.html', quotes=quotes, metadata=metadata)
    else:
        return render_template('bootstrap/storage.html', quotes=quotes,
                               metadata=metadata)


# display stored quotes
@app.route('/additional', methods=['GET'])
@auth.oidc_auth
def additional_quotes():
    quotes = Quote.query.order_by(Quote.quote_time.desc()).all()  # collect all quote rows in the Quote db
    metadata = get_metadata()
    if request.cookies.get('flag'):
        return render_template('flag/additional_quotes.html', quotes=quotes[20:], metadata=metadata)
    else:
        return render_template('bootstrap/additional_quotes.html', quotes=quotes[20:],
                               metadata=metadata)
