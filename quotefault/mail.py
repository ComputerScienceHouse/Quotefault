"""
File name: mail.py
Author: Nicholas Mercadante
Contributors: Joe Abbate
"""
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from flask import render_template
from flask_mail import Mail, Message
from quotefault import app

mail_client = Mail(app)

def send_report_email(reporter, quote):
    """
    Send email to eboard/rtp for a new report
    """
    recipients = ["<eboard@csh.rit.edu>","<rtp@csh.rit.edu>"]
    msg = Message(subject='New QuoteFault Report',
                sender=app.config.get('MAIL_USERNAME'),
                recipients=recipients)
    template = 'mail/report'
    msg.body = render_template(template + '.txt', reporter = reporter, quote = quote, server = app.config['SERVER_NAME'])
    msg.html = render_template(template + '.html', reporter = reporter, quote = quote, server = app.config['SERVER_NAME'])
    mail_client.send(msg)

def send_email(toaddr, subject, body):
    """
    Helper function for quote notification email
    """
    fromaddr = app.config['MAIL_USERNAME']
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    server = smtplib.SMTP(app.config['MAIL_SERVER'], 25)
    server.starttls()
    server.login('quotefault', app.config['MAIL_PASSWORD'])
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()

def send_quote_notification_email(user):
    """
    Send user email when they are quoted
    """
    toaddr = f"{user}@csh.rit.edu"
    subject = "You've been quoted"
    body = "Somebody quoted you in Quotefault!\n\n"
    body += "Check Quotefault to see what you were caught saying!"
    send_email(toaddr, subject, body)

