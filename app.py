from flask import Flask, request
from celery import Celery
import smtplib
from email.message import EmailMessage
import logging
from datetime import datetime
from config import SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, CELERY_BROKER_URL

app = Flask(__name__)
celery = Celery("tasks", broker=CELERY_BROKER_URL)

# Configure logging
logging.basicConfig(filename='/var/log/messaging_system.log', level=logging.INFO)

@celery.task
def send_email(recipient):
    msg = EmailMessage()
    msg.set_content("This is a test email")
    msg['Subject'] = "Test Email"
    msg['From'] = SMTP_USERNAME  # Assuming SMTP_USERNAME is your email address
    msg['To'] = recipient

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)

@app.route('/')
def handle_request():
    if 'sendmail' in request.args:
        recipient = request.args.get('sendmail')
        send_email.delay(recipient)
        return f"Email task queued for {recipient}"
    elif 'talktome' in request.args:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"Talktome request received at {current_time}")
        return f"Logged current time: {current_time}"
    else:
        return "Invalid request"

if __name__ == '__main__':
    app.run(debug=True)