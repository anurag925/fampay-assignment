from dotenv import load_dotenv
from celery import Celery
from flask import Flask
app = Flask(__name__)
app.config["CELERY_broker_url"] = os.getenv("REDIS_URL")
celery = Celery(app.name, broker=app.config["CELERY_broker_url"])
celery.conf.update(app.config)
