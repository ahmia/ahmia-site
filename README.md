![https://ahmia.fi/](https://raw.githubusercontent.com/ahmia/ahmia-site/master/ahmia-logotype.png)

Ahmia is the search engine for `.onion` domains on the Tor anonymity
network. It is led by [Juha Nurmi](//github.com/juhanurmi) and is based
in Finland. This repository contains crawlers used by [Ahmia](https://ahmia.fi/) search engine.

# Compatibility

The newest version of Ahmia is built with Python 3, Django 5 and Elasticsearch 8.
You will need to know these technologies to create a working Ahmia installation.
Ahmia crawls using [ahmia-crawler](https://github.com/ahmia/ahmia-crawler).

# Prerequisites
[Ahmia-index](https://github.com/ahmia/ahmia-index) should be installed and running

# Installation guide

```sh
pip install -r requirements.txt
```

## Configuration

This is a common step, both for local (dev) and production environment.

```sh
cp ahmia/example.env ahmia/.env
```

Please **modify the values** in `.env`, to fit your needs. You have to specify
at least the postgresql credentials, if you are using the production settings.


## Setup Website

### Migrate db
```sh
python manage.py makemigrations ahmia
python manage.py migrate
```

### Make the static files
```sh
python manage.py collectstatic
```

# Run site in dev mode

## Start development server

Development settings use sqlite as a database.
Default settings should work out of the box.

```sh
python manage.py runserver
```

## Production -- Nginx

* Configure and run nginx:
```sh
(sudo) cp conf/nginx/django-ahmia /etc/nginx/sites-enabled/django-ahmia
(sudo) service nginx start
```

Increase worker_connections in /etc/nginx/nginx.conf:

```
events {
        worker_connections 2048;
}
```

## Production -- Gunicorn

EITHER:

* Run gunicorn via bash scripts (work as daemons ~ edit files to change):
```sh
bash ./bin/run-ahmia.sh
bash ./bin/run-ahmia-onion.sh
```

OR

* **configure and** run gunicorn (tested with gunicorn==21.2.0) as systemd daemon
```sh
(sudo) cp conf/gunicorn/*.service /etc/systemd/system/
(sudo) service gunicorn (re)start
(sudo) systemctl enable /etc/systemd/system/ahmia.service
(sude) systemctl enable /etc/systemd/system/msydqstlz2kzerdg.service
```

It is **highly recommended** editing `/etc/systemd/system/gunicorn.service` to replace:
-- `User` with the login user (eithewise gunicorn will be ran as **root**).
-- `ExecStart` value, with your gunicorn path  (needed if gunicorn in virtualenv)

## Copy Elasticsearch CA cert in place

```sh
/usr/local/share/ca-certificates/http_ca.crt
```

## Crontab

* Rule to remove onions added by users weekly
```sh
0 0 */7 * * python3 /usr/local/lib/ahmia-site/ahmia/manage.py remove_onions --settings=ahmia.settings.prod
```

__NOTE__: If your deployment directory isn't `/usr/local/lib/ahmia-site` replace accordingly

# License

Ahmia is licensed under the [3-clause BSD license](
https://en.wikipedia.org/wiki/BSD_licenses#3-clause_license_.28.22Revised_BSD_License.22.2C_.22New_BSD_License.22.2C_or_.22Modified_BSD_License.22.29).
