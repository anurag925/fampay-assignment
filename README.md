python3 -m venv venv
. venv/bin/activate
pip3 freeze > requirements.txt  
celery -A app.celery worker

flask --app app run
celery -A app.celery worker --loglevel=info -B