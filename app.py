from flask import Flask, request, Response, stream_with_context
from celery import Celery
import smtplib
from email.message import EmailMessage
import logging
import json
import time
from datetime import datetime
from config import SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, CELERY_BROKER_URL, RESULT_BACKEND

app = Flask(__name__)
celery = Celery("app", broker=CELERY_BROKER_URL, result_backend=RESULT_BACKEND)

# Configure logging
logging.basicConfig(filename='/var/log/messaging_system.log', level=logging.INFO)

@celery.task(name='app.send_email')
def send_email(recipient):
    msg = EmailMessage()
    msg.set_content("This is a test email")
    msg['Subject'] = "Test Email"
    msg['From'] = SMTP_USERNAME 
    msg['To'] = recipient

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        # Log successful email send
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"Email sent successfully to {recipient} at {current_time}")
        return True
    except Exception as e:
        # Log email send failure
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.error(f"Failed to send email to {recipient} at {current_time}. Error: {str(e)}")
        return False

def event_stream(task):
    while True:
        if task.ready():
            if task.successful():
                yield f"data: {json.dumps({'status': 'COMPLETED', 'message': 'Email sent successfully'})}\n\n"
            else:
                yield f"data: {json.dumps({'status': 'FAILED', 'message': str(task.result)})}\n\n"
            break
        else:
            yield f"data: {json.dumps({'status': 'PENDING', 'message': 'Email is being sent...'})}\n\n"
        time.sleep(1)

@app.route('/')
def handle_request():
    if 'sendmail' in request.args:
        recipient = request.args.get('sendmail')
        task = send_email.delay(recipient)
        return Response(stream_with_context(event_stream(task)), content_type='text/event-stream')
    elif 'talktome' in request.args:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"Talktome request received at {current_time}")
        return f"Logged current time: {current_time}"
    else:
        return "Invalid request"

if __name__ == '__main__':
    app.run(debug=True)