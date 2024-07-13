# Python Email Messaging System

This is a Flask-based email messaging system that uses RabbitMQ and Celery for asynchronous task processing. It's designed to run on macOS and uses Nginx as a reverse proxy, with Ngrok for exposing the local server to the internet.

## Features

- Send emails asynchronously
- Real-time status updates using Server-Sent Events (SSE)
- Logging system for tracking email sending status
- Web interface for viewing logs
- Scalable architecture using Celery and RabbitMQ

## Prerequisites

- macOS
- Homebrew
- Python 3.7+
- pip
- Nginx
- RabbitMQ
- Ngrok

## Installation

1. Install the required system dependencies using Homebrew:

```bash
brew install python nginx rabbitmq
```
2. Install Ngrok following the official documentation:
```bash
brew install ngrok/ngrok/ngrok
ngrok config add-authtoken <token>
```
3. Clone this repository:
```bash
git clone https://github.com/Rob-in-son/HNG-stage3.git
cd HNG-stage3
```
4. Create a virtual environment and activate it 
```bash
python3 -m venv messaging_env
source messaging_env/bin/activate
```
5. Install the required Python packages:
```bash
pip install Flask celery pika smtplib
```
6. Copy the sample.config.py file to config.py and update it with your SMTP and Celery settings:
```bash
cp sample.config.py config.py
```
#### Edit config.py with your actual SMTP and Celery settings.
## Nginx Configuration
The Nginx configuration file is located at /opt/homebrew/etc/nginx/nginx.conf. Add the following server block to this file:

```bash 
server {
    listen 80;
    server_name localhost;
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## RabbitMQ Configuration
RabbitMQ should work with its default configuration. If you need to make changes, refer to the RabbitMQ documentation.
Usage

1. Start RabbitMQ:
```bash
brew services start rabbitmq
```
2. Start Celery worker:
```bash
celery -A app.celery worker --loglevel=info
```
3. Start the Flask application:
```bash
python app.py
``` 
4. Start Nginx:
```bash 
brew services start nginx
```
5. Start Ngrok to expose your local server:
```bash
ngrok http http://localhost:80
```
## API Endpoints

- `http://<ngrok-url>/?sendmail=email@example.com`: Sends an email to the specified address
- `http://<ngrok-url>/?talktome`: Logs the current time
- `http://<ngrok-url>//logs`: Displays the application logs

## Troubleshooting

- If you encounter permission issues with Nginx, make sure you're running it with sudo privileges.
- If emails are not being sent, check your SMTP settings in the config.py file.
- If Celery tasks are not being processed, ensure that RabbitMQ is running and the Celery worker is started.