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

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.String(64), unique=True, nullable=False)
    title = db.Column(db.String(255))
    description = db.Column(db.String(255))
    publishTime = db.Column(db.DateTime)
    # created_on = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    # updated_on = db.Column(db.TIMESTAMP, onupdate=db.func.current_timestamp())

    def __init__(self, video_id, title, description, publishTime) -> None:
        self.video_id = video_id
        self.title = title
        self.description = description
        self.publishTime = publishTime

    def __repr__(self) -> str:
        return f"Video <video_id = {self.video_id}, title = {self.title}, publishTime = {self.publishTime}>"

