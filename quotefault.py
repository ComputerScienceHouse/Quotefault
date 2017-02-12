#import all relevant packages
from flask import Flask, url_for
from flask import render_template
from flask import request
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)
app.config.from_pyfile('config.py') #associate the app with the right server/database
db = SQLAlchemy(app)

#create the quote table with all relevant columns
class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    submitter = db.Column(db.String(80))
    quote = db.Column(db.String(200), unique=True)
    speaker = db.Column(db.String(50))
    quoteTime = db.Column(db.DateTime)

    #initialize a row for the Quote table
    def __init__(self, submitter, quote, speaker):
        self.quoteTime = datetime.now()
        self.submitter = submitter
        self.quote = quote
        self.speaker = speaker

#run the main page by creating the table(s) in the CSH serverspace and rendering the mainpage template
@app.route('/', methods=['GET'])
def main():
    db.create_all()
    return render_template('quotefaultmainpage.html')

#run when the form submission button is clicked
@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        submitter = request.headers.get("x-webauth-user") #submitter will grab UN from webauth when linked to it
        quote = request.form['quoteString']
        speaker = request.form['nameString']
        #create a row for the Quote table
        new_quote = Quote(submitter=submitter, quote=quote, speaker=speaker)
        db.session.add(new_quote)
        #upload the quote
        db.session.commit()
        #return something to complete submission
        return "Submission Successful!", 200

#display stored quotes
@app.route('/get', methods=['GET'])
def get():
    quotes = Quote.query.all() #collect all quote rows in the Quote db
    quote_str = ""
    for quote_obj in quotes:
        quote_str += str(quote_obj.id) + " \"" + quote_obj.quote + "\" - " + quote_obj.speaker + ", submitted on " + str(quote_obj.quoteTime) + "\n"
    return render_template('quotefaultstorage.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port="6969")