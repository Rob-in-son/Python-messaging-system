# Import necessary modules
from flask import Flask, request, Response, stream_with_context, render_template
from celery import Celery
import smtplib
from email.message import EmailMessage
import logging
import json
import time
from datetime import datetime
from config import SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, CELERY_BROKER_URL, RESULT_BACKEND

# Initialize Flask app
app = Flask(__name__)

# Initialize Celery with broker and result backend from config
celery = Celery("app", broker=CELERY_BROKER_URL, result_backend=RESULT_BACKEND)

# Configure logging to write to a file with INFO level
logging.basicConfig(filename='/var/log/messaging_system.log', level=logging.INFO)

@celery.task(name='app.send_email')
def send_email(recipient):
    """
    Celery task to send an email.
    """
    # Create a new email message
    msg = EmailMessage()
    # Set the email content
    msg.set_content("This is a test email")
    # Set the email subject
    msg['Subject'] = "Test Email"
    # Set the sender's email address
    msg['From'] = SMTP_USERNAME 
    # Set the recipient's email address
    msg['To'] = recipient

    try:
        # Attempt to establish a secure connection with the SMTP server
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            # Login to the SMTP server
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            # Send the email message
            server.send_message(msg)
        
        # Get the current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Log the successful email send
        logging.info(f"Email sent successfully to {recipient} at {current_time}")
        return True
    except Exception as e:
        # Get the current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Log the email send failure
        logging.error(f"Failed to send email to {recipient} at {current_time}. Error: {str(e)}")
        return False

def event_stream(task):
    """
    Generator function for Server-Sent Events (SSE).
    Yields task status updates.
    """
    while True:
        # Check if the task has completed
        if task.ready():
            if task.successful():
                # If task was successful, yield a completion message
                yield f"data: {json.dumps({'status': 'COMPLETED', 'message': 'Email sent successfully'})}\n\n"
            else:
                # If task failed, yield an error message
                yield f"data: {json.dumps({'status': 'FAILED', 'message': str(task.result)})}\n\n"
            break
        else:
            # If task is still pending, yield a waiting message
            yield f"data: {json.dumps({'status': 'PENDING', 'message': 'Email is being sent...'})}\n\n"
        # Wait for 1 second before checking the task status again
        time.sleep(1)

@app.route('/')
def handle_request():
    """
    Main route handler for the application.
    Handles 'sendmail' and 'talktome' requests.
    """
    # Check if 'sendmail' parameter is in the request
    if 'sendmail' in request.args:
        # Get the recipient email from the request parameters
        recipient = request.args.get('sendmail')
        # Queue the email sending task
        task = send_email.delay(recipient)
        # Return a streaming response with task status updates
        return Response(stream_with_context(event_stream(task)), content_type='text/event-stream')
    # Check if 'talktome' parameter is in the request
    elif 'talktome' in request.args:
        # Get the current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Log the 'talktome' request
        logging.info(f"Talktome request received at {current_time}")
        # Return the logged time
        return f"Logged current time: {current_time}"
    else:
        # Return an error message for invalid requests
        return "Invalid request"

@app.route('/logs')
def logs():
    """
    Route to display application logs.
    """
    try:
        # Attempt to open the log file
        with open('/var/log/messaging_system.log', 'r') as f:
            # Read the entire log file content
            log_content = ''.join(f.readlines())
    except FileNotFoundError:
        # Set an error message if the log file is not found
        log_content = "Log file not found."

    # Return the log content wrapped in HTML for basic styling
    return f"<pre style='font-family:monospace; background-color:#eee; padding: 10px;'>{log_content}</pre>"
    
if __name__ == '__main__':
    # Run the Flask app in debug mode if this script is executed directly
    app.run(debug=True)