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
from flask import jsonify
from elasticsearch import Elasticsearch

# loading environment variables
load_dotenv()

# adding app configs
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

# initilize celery
celery = Celery(app.name, broker=app.config["CELERY_broker_url"])
celery.conf.update(app.config)

# init sql db
db = SQLAlchemy()
db.init_app(app)
with app.app_context():
    db.create_all()


# init elastic seearch
ELASTIC_PASSWORD = "LWGNIw4xpSTTNaoFTZqPD7Ah"
CLOUD_ID = "fampay_assignment:dXMtY2VudHJhbDEuZ2NwLmNsb3VkLmVzLmlvOjQ0MyQ5MDgzZTRiY2IzYzk0ZjgxYWNkMTkyYjE3OWQ4NmUxNCQ5ZTVhMzFmODMzNGM0MTdhOGQwMjExMDljOTI0MmVkOQ=="
client = Elasticsearch(
    cloud_id=CLOUD_ID,
    basic_auth=("elastic", ELASTIC_PASSWORD)
)


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

    def to_dict(self):
        return {
            'id': self.id,
            'video_id': self.video_id,
            'title': self.title,
            'description': self.description,
            'publishTime': self.publishTime
        }

# worker method
@celery.task()
def fetch_latest_videos():
    retries = 0
    # keys = ['AIzaSyC4xcY99GAQneyHRPRtkhSVDNO7U4aruv4']
    keys = ['AIzaSyC4xcY99GAQneyHRPRtkhSVDNO7U4aruv4',
            'AIzaSyAPjobf7C6EGppnur0aPhpOR41sB3dR-VU']
    response = None

    while True:
        if retries >= len(keys):
            break

        print(retries)
        url = f"https://youtube.googleapis.com/youtube/v3/search?key={keys[retries]}&q=cricket&part=snippet&type=video&maxResults=50"
        response = requests.get(url)
        print("request ", response.request.path_url, response.text)
        if response.status_code == 200:
            break

        retries += 1

    if response.status_code == 403:
        print("quota has exceeded for all calls")
        return

    items = json.loads(response.text)["items"]
    for item in items:
        video = Video(
            video_id=item['id']['videoId'],
            title=item['snippet']['title'],
            description=item['snippet']['description'],
            publishTime=datetime.fromisoformat(
                item['snippet']['publishTime'][:-1] + '+00:00')
        )
        with app.app_context():
            try:
                db.session.add(video)
                db.session.commit()
                res = client.index(index="test-index", document=video.to_dict())
                print(res)
            except exc.IntegrityError:
                print(str(video))
                logging.info(video)
                db.session.rollback()


@app.route("/videos/<int:page_no>", methods=['GET'])
def fetch_videos(page_no):
    videos = Video.query.order_by(
        Video.publishTime.desc()).paginate(page=page_no, per_page=10).items
    print(videos)
    return jsonify(list(map(lambda x: x.to_dict(), videos)))


@app.route("/search/videos/<string:query>", methods=['GET'])
def search_videos(query):
    resp = client.search(index="test-index", query={"query_string": { "query": query }})
    videos = []
    for item in resp['hits']['hits']:
        print(item)
        videos.append(Video.query.get(item['_source']['id']).to_dict())
    return jsonify(videos)

if __name__ == "__main__":
    app.run(debug=True)