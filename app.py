from dotenv import load_dotenv
from celery import Celery
from flask import Flask
app = Flask(__name__)
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
