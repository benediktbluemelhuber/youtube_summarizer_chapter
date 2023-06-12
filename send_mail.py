import streamlit as st
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib,ssl
from email import encoders
from email.mime.base import MIMEBase
from email.utils import formataddr
from email.header import Header
import os
import sys
from datetime import datetime


from email.mime.image import MIMEImage
import urllib.parse
import yaml
def get_email_from_username(username, config_file_path='config.yaml'):
    """Fetches the email associated with a given username in the config file."""
    # Load the YAML config file
    with open(config_file_path, 'r') as file:
        config = yaml.safe_load(file)

    # Look for the username in the config and return the associated email
    usernames = config.get('credentials', {}).get('usernames', {})
    if username in usernames:
        return usernames[username].get('email')
    else:
        return None





def send_mail(email, password):
    context = ssl.create_default_context()
    with smtplib.SMTP("postout.lrz.de", 587) as server:
        server.ehlo()  # Can be omitted
        server.starttls(context=context)
        server.ehlo()  # Can be omitted
        server.login(st.secrets["email"], st.secrets["password"])
        message_text = f"Your new password for the TCW Prof Subscriber is {password}"
        msg = MIMEText(message_text, 'html')
        msg["Subject"] = "PASSWORD RESET: TCW Prof Subscriber"
        msg['From'] = formataddr((str(Header('KI Lab [TUWIB10]', 'utf-8')), "ki-lab.bwl@mgt.tum.de"))
        msg["To"] = email
        try:
            server.sendmail(msg["From"], msg["To"], msg.as_string())
            print('Email to {} successfully sent!\n\n'.format(email))
        except Exception as e:
            print('Email to {} could not be sent :( because {}\n\n'.format("benedikt.bluemelhuber@tcw.de", str(e)))

def send_mail_password_change(username):
    email = get_email_from_username(username)
    context = ssl.create_default_context()
    with smtplib.SMTP("postout.lrz.de", 587) as server:
        server.ehlo()  # Can be omitted
        server.starttls(context=context)
        server.ehlo()  # Can be omitted
        server.login(st.secrets["email"], st.secrets["password"])
        message_text = f"You successfully changed your password for the TCW Prof Transcriber,"
        msg = MIMEText(message_text, 'html')
        msg["Subject"] = "PASSWORD Successfully changed: TCW Prof Subscriber"
        msg['From'] = formataddr((str(Header('KI Lab [TUWIB10]', 'utf-8')), "ki-lab.bwl@mgt.tum.de"))
        msg["To"] = email
        try:
            server.sendmail(msg["From"], msg["To"], msg.as_string())
            print('Email to {} successfully sent!\n\n'.format(email))
        except Exception as e:
            print('Email to {} could not be sent :( because {}\n\n'.format("benedikt.bluemelhuber@tcw.de", str(e)))