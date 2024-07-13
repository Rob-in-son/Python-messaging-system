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

# Set up logging configuration
# This will log all INFO level and above messages to the specified file
logging.basicConfig(filename='/var/log/messaging_system.log', level=logging.INFO)

# Initialize Celery with broker and result backend from config
# This allows for asynchronous task processing
celery = Celery("app", broker=CELERY_BROKER_URL, result_backend=RESULT_BACKEND)

@celery.task(name='app.send_email')
def send_email(recipient):
    """
    Celery task to send an email.
    This function is decorated as a Celery task, allowing it to be executed asynchronously.
    """
    # Get current time for logging purposes
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create email message
    msg = EmailMessage()
    msg.set_content("This is a test email")
    msg['Subject'] = "Test Email"
    msg['From'] = SMTP_USERNAME 
    msg['To'] = recipient

    try:
        # Attempt to send the email using SMTP_SSL
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            # Login to the SMTP server
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            # Send the email
            server.send_message(msg)
        
        # Log success and return True
        logging.info(f"Email sent successfully to {recipient} at {current_time}")
        return True
    except Exception as e:
        # Log error and return False if sending fails
        logging.error(f"Failed to send email to {recipient} at {current_time}. Error: {str(e)}")
        return False

def event_stream(task):
    """
    Generator function for Server-Sent Events (SSE).
    This function yields task status updates, allowing real-time updates to be sent to the client.
    """
    while True:
        if task.ready():
            # If task is completed, prepare and send final status
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if task.successful():
                status_message = {'status': 'COMPLETED', 'message': 'Email sent successfully'}
                logging.info(f"Email task completed successfully at {current_time}")
            else:
                status_message = {'status': 'FAILED', 'message': str(task.result)}
                logging.error(f"Email task failed at {current_time}. Error: {str(task.result)}")
            # Yield the status message in SSE format
            yield f"data: {json.dumps(status_message)}\n\n"
            break
        else:
            # If task is still pending, send update
            yield f"data: {json.dumps({'status': 'PENDING', 'message': 'Email is being sent...'})}\n\n"
        # Wait for 1 second before checking task status again
        time.sleep(1)

@app.route('/')
def handle_request():
    """
    Main route handler for the application.
    This function handles both 'sendmail' and 'talktome' requests.
    """
    # Get current time for logging purposes
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if 'sendmail' in request.args:
        # Handle sendmail request
        recipient = request.args.get('sendmail')
        # Queue the email sending task
        task = send_email.delay(recipient)
        logging.info(f"Email task queued for {recipient} at {current_time}")
        # Return a streaming response for real-time updates
        return Response(stream_with_context(event_stream(task)), content_type='text/event-stream')
    elif 'talktome' in request.args:
        # Handle talktome request
        logging.info(f"Talktome request received at {current_time}")
        return f"Logged current time: {current_time}"
    else:
        # Handle invalid request
        logging.warning(f"Invalid request received at {current_time}")
        return "Invalid request"

@app.route('/logs')
def logs():
    """
    Route to display application logs.
    This function reads and returns the content of the log file.
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
    # Debug mode should not be used in production
    app.run(debug=True)