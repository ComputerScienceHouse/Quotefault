"""
Defines the application's database models
"""

from sqlalchemy import UniqueConstraint

from quotefault import db

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


class APIKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hash = db.Column(db.String(64), unique=True)
    owner = db.Column(db.String(80))
    reason = db.Column(db.String(120))
    __table_args__ = (UniqueConstraint('owner', 'reason', name='unique_key'),)

    def __init__(self, owner, reason):
        self.hash = binascii.b2a_hex(os.urandom(10))
        self.owner = owner
        self.reason = reason
