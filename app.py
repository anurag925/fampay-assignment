import datetime
import json
import os
from dotenv import load_dotenv
from celery import Celery
from flask import Flask
from celery.schedules import crontab
from datetime import datetime
import logging
import requests

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQL_URI")
app.config["CELERY_broker_url"] = os.getenv("REDIS_URL")
app.config["result_expires"] = 30
app.config["timezone"] = 'UTC'
app.config["beat_schedule"] = {
    'test-celery': {
        'task': 'app.fetch_latest_videos',
        # Every minute
        'schedule': crontab(minute='*'),
    }
}
celery = Celery(app.name, broker=app.config["CELERY_broker_url"])
celery.conf.update(app.config)

db = SQLAlchemy()
db.init_app(app)
with app.app_context():
    db.create_all()
