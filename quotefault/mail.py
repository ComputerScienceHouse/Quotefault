import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(app, toaddr, subject, body):
    fromaddr = "quotefault@csh.rit.edu"
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
    send_email(toaddr, subject, body)
