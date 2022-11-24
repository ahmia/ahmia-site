[![Build Status](https://travis-ci.org/ahmia/ahmia-site.svg?branch=master)](https://travis-ci.org/ahmia/ahmia-site)
[![Code Health](https://landscape.io/github/ahmia/ahmia-site/master/landscape.svg?style=flat)](https://landscape.io/github/ahmia/ahmia-site/master)
[![Requirements Status](https://requires.io/github/ahmia/ahmia-site/requirements.svg?branch=master)](https://requires.io/github/ahmia/ahmia-site/requirements/?branch=master)

![https://ahmia.fi/](https://raw.githubusercontent.com/razorfinger/ahmia/ahmia-redesign/ahmia-logotype.png)

Ahmia is the search engine for `.onion` domains on the Tor anonymity
network. It is led by [Juha Nurmi](//github.com/juhanurmi) and is based
in Finland. This repository contains ahmia.fi source code.

# Compatibility

The newest version of Ahmia is built with Python 3.6, Django 1.11 and Elasticsearch 6.2 (5.6 is also compatible).
You will need to know these technologies to create a working Ahmia installation.
Ahmia crawls using [OnionBot](https://github.com/ahmia/ahmia-crawler).

# Prerequisites
[Ahmia-index](https://github.com/ahmia/ahmia-index) should be installed and running

# Installation guide

## Install dependencies:

### Ubuntu 16.04
```sh
$ (sudo) apt-get install build-essential python3 python3-pip python3-dev python3-setuptools
python3-virtualenv libxml2-dev libxslt1-dev python3-dev libpq-dev libffi-dev libssl-dev
```

### Fedora 23
```sh
$ (sudo) dnf install @development-tools redhat-rpm-config python3-pip python3-virtualenv
$ (sudo) dnf install libxml-devel libxslt-devel python3-devel postgresql-devel libffi-devel openssl-devel
```

## Install requirements in a virtual environment

```sh
$ virtualenv /path/to/venv
$ source /path/to/venv/bin/activate
(venv)$ pip install -r requirements/dev.txt
```

Or globally, for instance, in production server:

```sh
$ pip3 install -r requirements/prod.txt
```

## Configuration

This is a common step, both for local (dev) and production environment.

```
$ cp ahmia/ahmia/settings/example.env ahmia/ahmia/settings/.env
```

Please **modify the values** in `.env`, to fit your needs. You have to specify
at least the postgresql credentials, if you are using the production settings.


## Setup Website

### Migrate db
```sh
$ python3 ahmia/manage.py makemigrations
$ python3 ahmia/manage.py migrate
```

### Make the static files
```sh
$ python3 ahmia/manage.py collectstatic
```

# Run site in dev mode

## Start development server

Development settings use sqlite as a database.
Default settings should work out of the box.

```sh
$ python3 ahmia/manage.py runserver
```

## Crontab

* Rule to remove onions added by users weekly
```sh
0 0 */7 * * python3 /usr/local/lib/ahmia-site/ahmia/manage.py remove_onions --settings=ahmia.settings.prod
```

* Rule to update usage statistics hourly (could be once per day as well)
```sh
59 * * * * python3 /usr/local/lib/ahmia-site/ahmia/manage.py update_stats --settings=ahmia.settings.prod
```

* Rule to clean up some DB tables on the first day of each month
```sh
0 0 1 * * python3 /usr/local/lib/ahmia-site/ahmia/manage.py cleanup_db --settings=ahmia.settings.prod
```

* Rule to build PagePopularity Score Index every 10 days
```sh
0 0 */10 * * python3 /usr/local/lib/ahmia-site/ahmia/manage.py calc_page_pop --settings=ahmia.settings.prod
```

__NOTE__: If you are using virtualenv replace `python3` with the absolute path to your virtualenv's python executable, e.g `/path/to/venv/lib/python`

__NOTE__: If your deployment directory isn't `/usr/local/lib/ahmia-site` replace accordingly
# FAQ

## How can I populate my index to do searches ?
You should use [OnionElasticBot](https://github.com/ahmia/ahmia-crawler/tree/master/ahmia) to populate your index.

## Why can't my browser load django statics ?
The django settings.py is configured in a way that it only serves statics if DEBUG is True.
Please verify [here](https://github.com/ahmia/ahmia-site/blob/master/ahmia/ahmia/settings/dev.py#L6)
if it's the case. You can change this behaviour
[here](https://github.com/ahmia/ahmia-site/blob/master/ahmia/ahmia/urls.py#L71).

## What should I use to host ahmia in a production environment ?

We suggest to deploy ahmia using Apache2 or Nginx with Gunicorn.
Config samples are in [config/](https://github.com/ahmia/ahmia-site/tree/master/conf).

* Moreover you need to create a postgres database, and insert the database credentials in
`ahmia/ahmia/settings/.env`.

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

EITHER:

* Run gunicorn via bash scripts (work as daemons ~ edit files to change):
```sh
bash ./bin/run-ahmia.sh
bash ./bin/run-ahmia-onion.sh
```

OR

* Alternatively you can **configure and** run gunicorn as systemd daemon
```sh
(sudo) cp conf/gunicorn/*.service /etc/systemd/system/
(sudo) service gunicorn (re)start
(sudo) systemctl enable /etc/systemd/system/ahmia.service
(sude) systemctl enable /etc/systemd/system/msydqstlz2kzerdg.service
```

In that case it is **highly recommended** editing `/etc/systemd/system/gunicorn.service` to replace:
-- `User` with the login user (eithewise gunicorn will be ran as **root**).
-- `ExecStart` value, with your gunicorn path  (needed if gunicorn in virtualenv)

## How to run the Django Dev Server using the Production Settings?

If you want to have a quick grasp of the production settings, using the development server:

```sh
$ python3 ahmia/manage.py runserver --settings=ahmia.settings.prod
```

__NOTE__: You can also append `--settings=ahmia.settings.prod` to any other `manage.py` command.

# Support

No support is currently provided. It is up to you for now. This will change as Ahmia stabilizes.

# License

Ahmia is licensed under the [3-clause BSD license](
https://en.wikipedia.org/wiki/BSD_licenses#3-clause_license_.28.22Revised_BSD_License.22.2C_.22New_BSD_License.22.2C_or_.22Modified_BSD_License.22.29).
