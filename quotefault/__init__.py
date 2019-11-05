# import all relevant packages
import os
import subprocess
from datetime import datetime

import requests
from csh_ldap import CSHLDAP
from flask import Flask, render_template, request, flash, session, make_response
from flask_pyoidc.flask_pyoidc import OIDCAuthentication
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

app = Flask(__name__)
# look for a config file to associate with a db/port/ip/servername
if os.path.exists(os.path.join(os.getcwd(), "config.py")):
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.py"))
else:
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.env.py"))
#var representing the quote database the app is connected to
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
from .mail import send_quote_notification_email


# create the quote table with all relevant columns
class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    submitter = db.Column(db.String(80), nullable=False)
    quote = db.Column(db.String(200), unique=True, nullable=False)
    speaker = db.Column(db.String(50), nullable=False)
    quote_time = db.Column(db.DateTime, nullable=False)

    # initialize a row for the Quote table
    def __init__(self, submitter, quote, speaker):
        self.quote_time = datetime.now()
        self.submitter = submitter
        self.quote = quote
        self.speaker = speaker


class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    quote_id = db.Column(db.ForeignKey("quote.id"))
    voter = db.Column(db.String(200), nullable=False)
    direction = db.Column(db.Integer, nullable=False)
    updated_time = db.Column(db.DateTime, nullable=False)

    quote = db.relationship(Quote)
    test = db.UniqueConstraint("quote_id", "voter")

    # initialize a row for the Vote table
    def __init__(self, quote_id, voter, direction):
        self.quote_id = quote_id
        self.voter = voter
        self.direction = direction
        self.updated_time = datetime.now()


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
    return render_template('bootstrap/main.html', metadata=metadata, all_members=all_members)


@app.route('/settings', methods=['GET'])
@auth.oidc_auth
def settings():
    metadata = get_metadata()
    return render_template('bootstrap/settings.html', metadata=metadata)


@app.route('/vote', methods=['POST'])
@auth.oidc_auth
def make_vote():
    # submitter will grab UN from OIDC when linked to it
    submitter = session['userinfo'].get('preferred_username', '')

    quote = request.form['quote_id']
    direction = request.form['direction']

    existing_vote = Vote.query.filter_by(voter=submitter, quote_id=quote).first()
    if existing_vote is None:
        vote = Vote(quote, submitter, direction)
        db.session.add(vote)
        db.session.commit()
        return '200'
    elif existing_vote.direction != direction:
        existing_vote.direction = direction
        existing_vote.updated_time = datetime.now()
        db.session.commit()
        return '200'
    else:
        return '201'


@app.route('/settings', methods=['POST'])
@auth.oidc_auth
def update_settings():
    metadata = get_metadata()
    resp = make_response(render_template('bootstrap/settings.html', metadata=metadata))
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

    # standardises quotes and validates input
    quote = quote.strip("""'"\t\n """)

    speaker = request.form['nameString']
    # check for quote duplicate
    quoteCheck = Quote.query.filter(Quote.quote == quote).first()

    # checks for empty quote or submitter
    if quote == '' or speaker == '':
        flash('Empty quote or speaker field, try again!', 'error')
        return render_template('bootstrap/main.html', metadata=metadata, all_members=all_members), 200
    elif submitter == speaker:
        flash('You can\'t quote yourself! Come on', 'error')
        return render_template('bootstrap/main.html', metadata=metadata, all_members=all_members), 200
    elif quoteCheck is None:  # no duplicate quotes, proceed with submission
        # create a row for the Quote table
        new_quote = Quote(submitter=submitter, quote=quote, speaker=speaker)
        db.session.add(new_quote)
        db.session.flush()
        # upload the quote
        db.session.commit()
        # Send email to person quoted
        if app.config['MAIL_SERVER'] != '':
            send_quote_notification_email(app, speaker)
        # create a message to flash for successful submission
        flash('Submission Successful!')
        # add quote to CSH quote jar via QuoteJar API
        url = 'https://api.quote-jar.com/quotes/jar/32'
        body = {"quote": quote, "quotee": speaker}
        headers = {'content-type': 'application/json', 'token': app.config['QUOTEJAR_AUTH_KEY']}
        requests.post(url, data=json.dumps(body), headers=headers)
        # return something to complete submission
        return render_template('bootstrap/main.html', metadata=metadata, all_members=all_members), 200
    else:  # duplicate quote found, bounce the user back to square one
        flash('Quote already submitted!', 'warning')
        return render_template('bootstrap/main.html', metadata=metadata, all_members=all_members), 200


# display first 20 stored quotes
@app.route('/storage', methods=['GET'])
@auth.oidc_auth
def get():
    metadata = get_metadata()
    metadata['submitter'] = request.args.get('submitter')  # get submitter from url query string
    metadata['speaker'] = request.args.get('speaker')  # get speaker from url query string

    #return the first 20 quotes according to query strings (or lack thereof), as well as their associated vote value
    if metadata['speaker'] is not None and metadata['submitter'] is not None:
        quotes = db.session.query(Quote, func.sum(Vote.direction).label('votes')).outerjoin(Vote).group_by(Quote).order_by(Quote.quote_time.desc()).filter(Quote.submitter == metadata['submitter'], Quote.speaker == metadata['speaker']).limit(20).all()
    elif metadata['submitter'] is not None:
        quotes = db.session.query(Quote, func.sum(Vote.direction).label('votes')).outerjoin(Vote).group_by(Quote).order_by(Quote.quote_time.desc()).filter(Quote.submitter == metadata['submitter']).limit(20).all()
    elif metadata['speaker'] is not None:
        quotes = db.session.query(Quote, func.sum(Vote.direction).label('votes')).outerjoin(Vote).group_by(Quote).order_by(Quote.quote_time.desc()).filter(Quote.speaker == metadata['speaker']).limit(20).all()
    else:
        quotes = db.session.query(Quote, func.sum(Vote.direction).label('votes')).outerjoin(Vote).group_by(Quote).order_by(Quote.quote_time.desc()).limit(20).all()
    
    #tie any votes the user has made to their uid
    user_votes = db.session.query(Vote).filter(Vote.voter == metadata['submitter']).all()

    return render_template(
        'bootstrap/storage.html',
        quotes=quotes,
        metadata=metadata,
        user_votes=user_votes
    )


# display ALL stored quotes
@app.route('/additional', methods=['GET'])
@auth.oidc_auth
def additional_quotes():

    metadata = get_metadata()
    metadata['submitter'] = request.args.get('submitter')  # get submitter from url query string
    metadata['speaker'] = request.args.get('speaker')  # get speaker from url query string

    #return quotes according to query strings (or lack thereof)
    if metadata['speaker'] is not None and metadata['submitter'] is not None:
        quotes = db.session.query(Quote, func.sum(Vote.direction).label('votes')).outerjoin(Vote).group_by(Quote).order_by(Quote.quote_time.desc()).filter(Quote.submitter == metadata['submitter'], Quote.speaker == metadata['speaker']).all()
    elif metadata['submitter'] is not None:
        quotes = db.session.query(Quote, func.sum(Vote.direction).label('votes')).outerjoin(Vote).group_by(Quote).order_by(Quote.quote_time.desc()).filter(Quote.submitter == metadata['submitter']).all()
    elif metadata['speaker'] is not None:
        quotes = db.session.query(Quote, func.sum(Vote.direction).label('votes')).outerjoin(Vote).group_by(Quote).order_by(Quote.quote_time.desc()).filter(Quote.speaker == metadata['speaker']).all()
    else:
        quotes = db.session.query(Quote, func.sum(Vote.direction).label('votes')).outerjoin(Vote).group_by(Quote).order_by(Quote.quote_time.desc()).all()

    #tie any votes the user has made to their uid
    user_votes = db.session.query(Vote).filter(Vote.voter == metadata['uid']).all()


    return render_template(
        'bootstrap/additional_quotes.html',
        quotes=quotes[20:],
        metadata=metadata,
        user_votes=user_votes
    )
