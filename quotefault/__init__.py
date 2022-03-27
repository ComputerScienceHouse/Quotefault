"""
File name: __init__.py
Author: Nicholas Mercadante
Contributors: Devin Matte, Max Meinhold, Joe Abbate
"""
import os
import subprocess
from datetime import datetime

import requests
from flask import Flask, render_template, request, flash, session, make_response, abort, redirect
from flask_migrate import Migrate
from flask_pyoidc.flask_pyoidc import OIDCAuthentication
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.expression import func

app = Flask(__name__)
# look for a config file to associate with a db/port/ip/servername
if os.path.exists(os.path.join(os.getcwd(), "config.py")):
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.py"))
else:
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.env.py"))

#var representing the quote database the app is connected to
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.logger.info('SQLAlchemy pointed at ' + repr(db.engine.url))

# Disable SSL certificate verification warning
requests.packages.urllib3.disable_warnings()

# Disable SQLAlchemy modification tracking
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
auth = OIDCAuthentication(app,
                          issuer=app.config['OIDC_ISSUER'],
                          client_registration_info=app.config['OIDC_CLIENT_CONFIG'])

app.secret_key = 'submission'  # allows message flashing, var not actually used

from .ldap import get_all_members, is_member_of_group
from .mail import send_quote_notification_email, send_report_email
from .models import Quote, Vote, Report

def get_metadata():
    """
    Provide metadata to page
    UUID, UID, Git Version, Plug, and admin permissions obtained
    """
    uuid = str(session["userinfo"].get("sub", ""))
    uid = str(session["userinfo"].get("preferred_username", ""))
    version = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD']
        ).decode('utf-8').rstrip()
    plug = request.cookies.get('plug')
    metadata = {
        "uuid": uuid,
        "uid": uid,
        "version": version,
        "plug": plug,
        "is_admin" : is_member_of_group(uid, 'eboard') or is_member_of_group(uid, 'rtp')
    }
    return metadata

@app.route('/', methods=['GET'])
@auth.oidc_auth
def main():
    """
    Root Website, presents submission page
    """
    metadata = get_metadata()
    all_members = get_all_members()
    return render_template('bootstrap/main.html', metadata=metadata, all_members=all_members)


@app.route('/settings', methods=['GET'])
@auth.oidc_auth
def settings():
    """
    Presents settings page
    """
    metadata = get_metadata()
    return render_template('bootstrap/settings.html', metadata=metadata)


@app.route('/vote', methods=['POST'])
@auth.oidc_auth
def make_vote():
    """
    Called by JS to add vote to DB
    """
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
    if existing_vote.direction != direction:
        existing_vote.direction = direction
        existing_vote.updated_time = datetime.now()
        db.session.commit()
        return '200'
    return '201'


@app.route('/settings', methods=['POST'])
@auth.oidc_auth
def update_settings():
    """
    Update settings from settings page
    """
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
    """
    Submit quote from main page, add to DB
    """
    #submitter will grab UN from OIDC when linked to it
    submitter = session['userinfo'].get('preferred_username', '')

    metadata = get_metadata()
    all_members = get_all_members()
    quote = request.form['quoteString']

    # standardises quotes and validates input
    quote = quote.strip("""'"\t\n """)

    speaker = request.form['nameString']
    # check for quote duplicate
    quote_check = Quote.query.filter(Quote.quote == quote).first()

    # checks for empty quote or submitter
    if quote == '' or speaker == '':
        flash('Empty quote or speaker field, try again!', 'error')
        return render_template(
            'bootstrap/main.html',
            metadata=metadata,
            all_members=all_members
        ), 200
    if submitter == speaker:
        flash('You can\'t quote yourself! Come on', 'error')
        return render_template(
            'bootstrap/main.html',
            metadata=metadata,
            all_members=all_members
        ), 200
    if quote_check is None:  # no duplicate quotes, proceed with submission
        # create a row for the Quote table
        new_quote = Quote(submitter=submitter, quote=quote, speaker=speaker)
        db.session.add(new_quote)
        db.session.flush()
        # upload the quote
        db.session.commit()
        # Send email to person quoted
        if app.config['MAIL_SERVER'] != '':
            send_quote_notification_email(speaker)
        # create a message to flash for successful submission
        flash('Submission Successful!')
        # return something to complete submission
        return render_template(
            'bootstrap/main.html',
            metadata=metadata,
            all_members=all_members
        ), 200
    # duplicate quote found, bounce the user back to square one
    flash('Quote already submitted!', 'warning')
    return render_template(
        'bootstrap/main.html',
        metadata=metadata,
        all_members=all_members
    ), 200


def get_quote_query(speaker: str = "", submitter: str = "", include_hidden: bool = False, order = Quote.quote_time.desc()):
    """Return a query based on the args, with vote count attached to the quotes"""
    # Get all the quotes with their votes
    quote_query = db.session.query(Quote, 
        func.sum(Vote.direction).label('votes')).outerjoin(Vote).group_by(Quote)
    # Put the most recent first
    quote_query = quote_query.order_by(order)
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
    """
    Show submitted quotes, only showing first 20 initially
    """
    metadata = get_metadata()

    # Get the most recent 20 quotes
    quotes = get_quote_query(speaker = request.args.get('speaker'),
        submitter = request.args.get('submitter')).limit(20).all()

    #tie any votes the user has made to their uid
    user_votes = Vote.query.filter(Vote.voter == metadata['uid']).all()
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
    """
    Show beyond the first 20 quotes
    """

    metadata = get_metadata()

    # Get all the quotes
    quotes = get_quote_query(speaker = request.args.get('speaker'),
        submitter = request.args.get('submitter')).all()

    #tie any votes the user has made to their uid
    user_votes = db.session.query(Vote).filter(Vote.voter == metadata['uid']).all()

    return render_template(
        'bootstrap/additional_quotes.html',
        quotes=quotes[20:],
        metadata=metadata,
        user_votes=user_votes
    )

@app.route('/report/<quote_id>', methods=['POST'])
@auth.oidc_auth
def submit_report(quote_id):
    """
    Report a quote and notify EBoard/RTP
    """
    metadata = get_metadata()
    existing_report = Report.query.filter(Report.reporter==metadata['uid'],
        Report.quote_id==quote_id).first()
    if existing_report:
        flash("You already submitted a report for this Quote!")
        return redirect('/storage')
    new_report = Report(quote_id, metadata['uid'], "Report Reason Not Given")
    db.session.add(new_report)
    db.session.commit()
    if app.config['MAIL_SERVER'] != '':
        send_report_email( metadata['uid'], Quote.query.get(quote_id) )
    flash("Report Successful!")
    return redirect('/storage')

@app.route('/review', methods=['GET'])
@auth.oidc_auth
def review():
    """
    Presents page for admins to review reports
    and either hide or keep quote
    """
    metadata = get_metadata()
    if metadata['is_admin']:
        # Get all outstanding reports
        reports = Report.query.filter(Report.reviewed == False).all()

        return render_template(
            'bootstrap/admin.html',
            reports=reports,
            metadata=metadata
        )
    abort(403)

@app.route('/review/<report_id>/<result>', methods=['POST'])
@auth.oidc_auth
def review_submit(report_id, result):
    """
    Called when Admin decides on a quote being hidden or kept
    """
    metadata = get_metadata()
    report = Report.query.get(report_id)
    if not metadata['is_admin']:
        abort(403)
    if not report:
        abort(404)
    if report.reviewed:
        abort(404)
    if result == "keep": 
        report.reviewed = True
        db.session.commit()
        flash("Report Completed: Quote Kept")
    elif result == "hide":
        report.quote.hidden = True
        report.reviewed = True
        db.session.commit()
        flash("Report Completed: Quote Hidden")
    else:
        abort(400)
    return redirect('/review')
    

@app.route('/hide/<quote_id>', methods=['POST'])
@auth.oidc_auth
def hide(quote_id):
    """
    Hides a quote
    """
    metadata = get_metadata()
    quote = Quote.query.get(quote_id)
    if not (metadata['uid'] == quote.submitter or metadata['uid'] == quote.speaker or metadata['is_admin']):
        abort(403)
    if not quote:
        abort(404)
    quote.hidden = True
    db.session.commit()
    flash("Quote Hidden!")
    return redirect('/storage')


@app.route('/unhide/<quote_id>', methods=['POST'])
@auth.oidc_auth
def unhide(quote_id):
    """
    Gives admins power to unhide a hidden quote
    """
    metadata = get_metadata()
    quote = Quote.query.get(quote_id)
    if not metadata['is_admin']:
        abort(403)
    if not quote:
        abort(404)
    quote.hidden = False
    db.session.commit()
    flash("Quote Unhidden!")
    return redirect('/hidden')


@app.route('/hidden', methods=['GET'])
@auth.oidc_auth
def hidden():
    """
    Presents hidden quotes to qualified users
    Users who submitted a hidden quote or were quoted in a hidden quote will see those only
    Admins see all hidden quotes
    """
    metadata = get_metadata()
    if metadata['is_admin']:
        quotes = get_quote_query(include_hidden=True).filter( Quote.hidden ).all()
    else:
        quotes = get_quote_query(include_hidden=True).filter(
            (Quote.speaker == metadata['uid']) | (Quote.submitter == metadata['uid'] )
        ).filter( Quote.hidden ).all()
    return render_template(
        'bootstrap/hidden.html',
        quotes=quotes,
        metadata=metadata
    )

@app.route('/random', methods=['GET'])
@auth.oidc_auth
def random_quote():
  quote = get_quote_query(speaker = request.args.get('speaker'), \
            submitter = request.args.get('submitter'), order = func.random()).limit(1).all()[0][0]
  out = f"{quote.quote} -{quote.speaker} (Submitted by {quote.submitter})"
  return out, 200

@app.errorhandler(403)
def forbidden(e):
    return render_template('bootstrap/403.html', metadata=get_metadata()), 403

@app.errorhandler(404)
def forbidden(e):
    return render_template('bootstrap/404.html', metadata=get_metadata()), 404

@app.errorhandler(400)
def forbidden(e):
    return render_template('bootstrap/400.html', metadata=get_metadata()), 400

@app.errorhandler(409)
def forbidden(e):
    return render_template('bootstrap/409.html', metadata=get_metadata()), 409

