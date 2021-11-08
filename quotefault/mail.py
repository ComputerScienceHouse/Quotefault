from flask_mail import Message
from flask import render_template
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_report_email(app, mail_client, reporter, quote):
    recipients = ["<eboard@csh.rit.edu>","<rtp@csh.rit.edu>"]
    msg = Message(subject='New QuoteFault Report',
                sender=app.config.get('MAIL_USERNAME'),
                recipients=recipients)
    template = 'mail/report'
    msg.body = render_template(template + '.txt', reporter = reporter, quote = quote )
    msg.html = render_template(template + '.html', reporter = reporter, quote = quote )
    mail_client.send(msg)

def send_email(app, toaddr, subject, body):
    fromaddr = app.config['MAIL_USERNAME']
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = subject
    body = body
    msg.attach(MIMEText(body, 'plain'))
    server = smtplib.SMTP(app.config['MAIL_SERVER'], 25)
    server.starttls()
    server.login('quotefault', app.config['MAIL_PASSWORD'])
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()

def send_quote_notification_email(app, user):
    toaddr = "{}@csh.rit.edu".format(user)
    subject = "You've been quoted"
    body = "Somebody quoted you in Quotefault!\n\n"
    body += "Check Quotefault to see what you were caught saying!"
    send_email(app, toaddr, subject, body)