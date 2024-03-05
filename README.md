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

### Copy Elasticsearch CA cert in place

```sh
/usr/local/share/ca-certificates/http_ca.crt
```

# Run site in dev mode

## Start development server

Development settings use sqlite as a database.
Default settings should work out of the box.

```sh
python manage.py runserver
```

## Production -- Nginx

__NOTE__: If your deployment directory isn't `/usr/local/lib/ahmia-site` replace accordingly

* Configure and run nginx:
```sh
cp conf/nginx/django-ahmia /etc/nginx/sites-enabled/django-ahmia
service nginx start
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
cp conf/gunicorn/*.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable ahmia.service
systemctl status ahmia.service
systemctl enable ahmia-onion.service
systemctl status ahmia-onion.service
systemctl restart gunicorn
```

## Edit your /lib/systemd/system/nginx.service to add ahmia-site.service ahmia-site-onion.service

```sh
systemctl edit nginx

[Unit]
After=network-online.target remote-fs.target nss-lookup.target ahmia.service ahmia-onion.service
Requires=ahmia.service ahmia-onion.service

systemctl daemon-reload
systemctl cat nginx
```

## Delete added onions once a week

```sh
# EVERY WEEK, Tuesday 12:57
57 12 * * 2 cd /usr/local/lib/ahmia-site && venv/bin/python manage.py deleteonions >> weeklydelete.log 2>&1
```

# License

Ahmia is licensed under the [3-clause BSD license](
https://en.wikipedia.org/wiki/BSD_licenses#3-clause_license_.28.22Revised_BSD_License.22.2C_.22New_BSD_License.22.2C_or_.22Modified_BSD_License.22.29).
