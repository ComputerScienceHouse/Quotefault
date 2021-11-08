# import all relevant packages
import os
import subprocess
from datetime import datetime



import requests
from csh_ldap import CSHLDAP
from flask import Flask, render_template, request, flash, session, make_response
from flask_mail import Mail, Message
from flask_migrate import Migrate
from flask_pyoidc.flask_pyoidc import OIDCAuthentication
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.orm.query import Query
from werkzeug.utils import redirect

from config import LDAP_BIND_DN

app = Flask(__name__)
# look for a config file to associate with a db/port/ip/servername
if os.path.exists(os.path.join(os.getcwd(), "config.py")):
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.py"))
else:
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.env.py"))

#var representing the quote database the app is connected to
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail_client = Mail(app)
app.logger.info('SQLAlchemy pointed at ' + repr(db.engine.url))

# pylint: disable=wrong-import-position
from .models import Quote, Vote, Report

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

from .ldap import get_all_members, is_member_of_group
from .mail import send_quote_notification_email, send_report_email

def get_metadata():
    uuid = str(session["userinfo"].get("sub", ""))
    uid = str(session["userinfo"].get("preferred_username", ""))
    version = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('utf-8').rstrip()
    plug = request.cookies.get('plug')
    metadata = {
        "uuid": uuid,
        "uid": uid,
        "version": version,
        "plug": plug,
        "is_admin" : is_member_of_group(uid,'eboard') or is_member_of_group(uid,'rtp')
    }
    return metadata

# run the main page by creating the table(s) in the CSH serverspace and rendering the mainpage template
@app.route('/', methods=['GET'])
@auth.oidc_auth
def main():
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
    #submitter will grab UN from OIDC when linked to it
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
            send_quote_notification_email(app, mail_client, speaker)
        # create a message to flash for successful submission
        flash('Submission Successful!')
        # return something to complete submission
        return render_template('bootstrap/main.html', metadata=metadata, all_members=all_members), 200
    else:  # duplicate quote found, bounce the user back to square one
        flash('Quote already submitted!', 'warning')
        return render_template('bootstrap/main.html', metadata=metadata, all_members=all_members), 200


def get_quote_query(speaker: str = "", submitter: str = "", include_hidden: bool = False):
    """Return a query based on the args, with vote count attached to the quotes"""

    # Get all the quotes with their votes
    quote_query = db.session.query(Quote, func.sum(Vote.direction).label('votes')).outerjoin(Vote).group_by(Quote)

    # Put the most recent first
    quote_query = quote_query.order_by(Quote.quote_time.desc())

    # Filter hidden quotes
    if not include_hidden:
        quote_query = quote_query.filter(Quote.hidden == False)

    # Filter by speaker and submitter, if applicable
    if request.args.get('speaker'):
        quote_query = quote_query.filter(Quote.speaker == request.args.get('speaker'))
    if request.args.get('submitter'):
        quote_query = quote_query.filter(Quote.submitter == request.args.get('submitter'))

    return quote_query

# display first 20 stored quotes
@app.route('/storage', methods=['GET'])
@auth.oidc_auth
def get():
    metadata = get_metadata()

    # Get the most recent 20 quotes
    quotes = get_quote_query(speaker = request.args.get('speaker'), submitter = request.args.get('submitter')).limit(20).all()
    
    #tie any votes the user has made to their uid
    user_votes = db.session.query(Vote).filter(Vote.voter == metadata['uid']).all()

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

    # Get all the quotes
    quotes = get_quote_query(speaker = request.args.get('speaker'), submitter = request.args.get('submitter')).all()

    #tie any votes the user has made to their uid
    user_votes = db.session.query(Vote).filter(Vote.voter == metadata['uid']).all()

    return render_template(
        'bootstrap/additional_quotes.html',
        quotes=quotes[20:],
        metadata=metadata,
        user_votes=user_votes
    )

@app.route('/report/<id>', methods=['POST'])
@auth.oidc_auth
def report(id):
    metadata = get_metadata()
    existing_report = Report.query.filter(Report.reporter==metadata['uid'], Report.quote_id==id).first()
    if existing_report:
        flash("You already submitted a report for this Quote!")
        return redirect('/storage')
    new_report = Report(id, metadata['uid'], None)
    db.session.add(new_report)
    db.session.commit()
    if app.config['MAIL_SERVER'] != '':
        send_report_email( app, mail_client, metadata['uid'], Quote.query.get(id) )

    flash("Report Successful!")
    return redirect('/storage')

@app.route('/review', methods=['GET'])
@auth.oidc_auth
def review():
    metadata = get_metadata()
    if metadata['is_admin']:
        # Get the most recent 20 quotes
        reports = Report.query.filter(Report.reviewed==False).all()

        return render_template(
            'bootstrap/admin.html',
            reports=reports,
            metadata=metadata
        )
    return redirect('/')

@app.route('/review/<id>/<result>', methods=['POST'])
@auth.oidc_auth
def review_submit(id, result):
    metadata = get_metadata()
    result = int(result)
    if metadata['is_admin']:
        # 1 = Keep, 0 = Hide
        if result:
            report = Report.query.get(id)
            report.reviewed = True
            db.session.commit()
            flash("Report Completed: Quote Kept")
        else:
            report = Report.query.get(id)
            report.quote.hidden = True
            report.reviewed = True
            db.session.commit()
            flash("Report Completed: Quote Hidden")
        return redirect('/review')
    return redirect('/')

@app.route('/hide/<id>', methods=['POST'])
@auth.oidc_auth
def hide(id):
    quote = Quote.query.get(id)
    quote.hidden = True
    db.session.commit()
    flash("Quote Hidden!")
    return redirect('/storage')

@app.route('/unhide/<id>', methods=['POST'])
@auth.oidc_auth
def unhide(id):
    metadata = get_metadata()
    if metadata['is_admin']:
        quote = Quote.query.get(id)
        quote.hidden = False
        db.session.commit()
        flash("Quote Unhidden!")
        return redirect('/hidden')
    return redirect('/')

@app.route('/hidden', methods=['GET'])
@auth.oidc_auth
def hidden():
    metadata = get_metadata()
    if metadata['is_admin']:
        quotes = Quote.query.filter( Quote.hidden ).all()
    else:
        quotes = Quote.query.filter( (Quote.speaker == metadata['uid']) | (Quote.submitter == metadata['uid'] ) ).filter( Quote.hidden ).all()
    return render_template(
        'bootstrap/hidden.html',
        quotes=quotes,
        metadata=metadata
    )