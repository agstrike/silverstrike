FROM index.docker.io/library/python:slim

WORKDIR /app
# Copy the code
ADD manage.py deploy/requirements.txt deploy/settings.py setup.py urls.py deploy/wsgi.py /app/
ADD silverstrike /app/silverstrike

# install deps
RUN apt-get update -y && apt-get install -y gcc libmariadb-dev python3-dev libffi-dev && \
    pip install --no-cache-dir -r requirements.txt && python setup.py install && apt-get remove -y gcc && apt-get autoremove -y

# configure uwsgi and django
ENV DJANGO_SETTINGS_MODULE=settings UWSGI_WSGI_FILE=wsgi.py UWSGI_HTTP=:8000 UWSGI_MASTER=1 UWSGI_WORKERS=2 UWSGI_THREADS=8 UWSGI_LAZY_APPS=1 UWSGI_WSGI_ENV_BEHAVIOR=holy
# create data dir and collect static files
RUN mkdir /data && chown 2000:2000 /data && python manage.py collectstatic --noinput
USER 2000:2000

CMD python manage.py migrate --noinput && uwsgi
