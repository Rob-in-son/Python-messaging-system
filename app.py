from flask import Flask, request
from celery import Celery
import smtplib
from email.message import EmailMessage
import logging
from datetime import datetime
from config import SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD


app = Flask(__name__)
