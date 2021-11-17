"""
Defines the application's database models
"""
import binascii
from datetime import datetime
import os
from sqlalchemy import UniqueConstraint
from quotefault import db

# create the quote table with all relevant columns
class Quote(db.Model):
    """
    Quote table in SQL
    """
    __tablename__ = 'quote'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    submitter = db.Column(db.String(80), nullable=False)
    quote = db.Column(db.String(200), unique=True, nullable=False)
    speaker = db.Column(db.String(50), nullable=False)
    quote_time = db.Column(db.DateTime, nullable=False)
    hidden = db.Column(db.Boolean, default=False)

    votes = db.relationship('Vote', back_populates='quote')
    reports = db.relationship('Report', back_populates='quote')

    # initialize a row for the Quote table
    def __init__(self, submitter, quote, speaker):
        self.quote_time = datetime.now()
        self.submitter = submitter
        self.quote = quote
        self.speaker = speaker


class Vote(db.Model):
    """
    Vote table in SQL
    """
    __tablename__ = 'vote'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    quote_id = db.Column(db.ForeignKey("quote.id"))
    voter = db.Column(db.String(200), nullable=False)
    direction = db.Column(db.Integer, nullable=False)
    updated_time = db.Column(db.DateTime, nullable=False)

    quote = db.relationship(Quote, back_populates='votes')
    test = db.UniqueConstraint("quote_id", "voter")

    # initialize a row for the Vote table
    def __init__(self, quote_id, voter, direction):
        self.quote_id = quote_id
        self.voter = voter
        self.direction = direction
        self.updated_time = datetime.now()


class APIKey(db.Model):
    """
    APIKey table in SQL
    """
    __tablename__ = 'api_key'
    id = db.Column(db.Integer, primary_key=True)
    hash = db.Column(db.String(64), unique=True)
    owner = db.Column(db.String(80))
    reason = db.Column(db.String(120))
    __table_args__ = (UniqueConstraint('owner', 'reason', name='unique_key'),)

    def __init__(self, owner, reason):
        self.hash = binascii.b2a_hex(os.urandom(10))
        self.owner = owner
        self.reason = reason

class Report(db.Model):
    """
    Report table in SQL
    """
    __tablename__ = 'report'
    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'), nullable=False)
    reporter = db.Column(db.Text, nullable=False)
    reason = db.Column(db.Text, nullable=True)
    reviewed = db.Column(db.Boolean, nullable=False, default=False)

    quote = db.relationship(Quote, back_populates='reports')

    def __init__(self, quote_id, reporter, reason):
        self.hash = binascii.b2a_hex(os.urandom(10))
        self.quote_id = quote_id
        self.reporter = reporter
        self.reason = reason

