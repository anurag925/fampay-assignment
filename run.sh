nohup celery -A app.celery worker --loglevel=info -B &
python -m flask run --host=0.0.0.0 --port=80
