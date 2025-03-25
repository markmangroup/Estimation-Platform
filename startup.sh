# set environment variables required by your Django application
export DEBUG="False"

# install any required dependencies
pip install -r requirements.txt

# perform Django database migrations
python src/manage.py migrate

# collect static files (if applicable)
python src/manage.py collectstatic --noinput

# Start Gunicorn server
export PYTHONPATH=$(pwd)/src
gunicorn src.laurel.wsgi:application --bind 0.0.0.0:8000