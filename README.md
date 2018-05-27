[![Build Status](https://travis-ci.org/ahmia/ahmia-site.svg?branch=master)](https://travis-ci.org/ahmia/ahmia-site)
[![Code Health](https://landscape.io/github/ahmia/ahmia-site/master/landscape.svg?style=flat)](https://landscape.io/github/ahmia/ahmia-site/master)
[![Requirements Status](https://requires.io/github/ahmia/ahmia-site/requirements.svg?branch=master)](https://requires.io/github/ahmia/ahmia-site/requirements/?branch=master)

![https://ahmia.fi/](https://raw.githubusercontent.com/razorfinger/ahmia/ahmia-redesign/ahmia-logotype.png)

Ahmia is the search engine for `.onion` domains on the Tor anonymity
network. It is led by [Juha Nurmi](//github.com/juhanurmi) and is based
in Finland. This repository contains ahmia.fi source code.

# Compatibility

The newest version of Ahmia is built with Python 3.6, Django 1.11 and
Elasticsearch 5. Python 2.7+ should be ok too, but preferably try Python 3 instead.
You will need to know these technologies to create a working Ahmia installation.
Ahmia crawls using [OnionBot](https://github.com/ahmia/ahmia-crawler).

# Prerequisites
[Ahmia-index](https://github.com/ahmia/ahmia-index) should be installed and running

# Installation guide

## Install dependencies:

### Ubuntu 16.04
```sh
# apt-get install build-essential python-pip python-virtualenv
# apt-get install libxml2-dev libxslt1-dev python-dev libpq-dev libffi-dev libssl-dev
```

### Fedora 23
```sh
# dnf install @development-tools redhat-rpm-config python-pip python-virtualenv
# dnf install libxml-devel libxslt-devel python-devel postgresql-devel libffi-devel openssl-devel
```

## Install requirements in a virtual environment

```sh
$ virtualenv /path/to/venv
$ source /path/to/venv/bin/activate
(venv)$ pip install -r requirements/dev.txt
```

## Configuration

Please copy `example.env` to `.env` and modify the values, to fit your needs.
This is a common step, both for local (dev) and production environment.

You can always override the environment values defined inside `.env` in command line, e.g:

```
DEBUG=False python manage.py test
```

# Run site in dev mode

## Migrate db
```sh
$ python ahmia/manage.py makemigrations ahmia
$ python ahmia/manage.py makemigrations search
$ python ahmia/manage.py migrate
```

## Start development server

Development settings use sqlite as a database.
Default settings should work out of the box.

```sh
$ python ahmia/manage.py runserver
```

## Crontab to remove '/onionsadded' weekly
```sh
0 22 * * * cd ahmia/ && ./manage.py shell < remove_onionsadded.py
```

# FAQ

## How can populate my index to do searches ?
You should use [OnionElasticBot](https://github.com/ahmia/ahmia-crawler/tree/master/onionElasticBot) to populate your index.

## Why can't my browser load django statics ?
The django settings.py is configured in a way that it only serve statics if DEBUG is True. Please verify [here](https://github.com/ahmia/ahmia-site/blob/master/ahmia/ahmia/settings.py#L9) if it's the case. You can change this behaviour [here](https://github.com/ahmia/ahmia-site/blob/master/ahmia/ahmia/urls.py#L18).

## What should I use to host ahmia in a production environment ?

You need to create a postgres database, and insert the database name, user and password
information in `ahmia/settings/prod.py`.

We suggest to deploy ahmia using Apache2 or Nginx with Uwsgi.
Config samples are in [config/](https://github.com/ahmia/ahmia-site/tree/master/conf).

```sh
cp conf/uwsgi/vassals/*.ini /etc/uwsgi/vassals/
cp conf/nginx/django-ahmia /etc/nginx/sites-enabled/django-ahmia
uwsgi --emperor /etc/uwsgi/vassals --uid www-data --gid www-data --daemonize /var/log/uwsgi-emperor.log
service nginx start
```

#### Using the development server

However if you want to have a quick grasp of the production settings, using the development server,
you can run:

```sh
$ python ahmia/manage.py runserver --settings ahmia.settings.prod
```


# Support

No support is currently provided. It is up to you for now. This will
change as Ahmia stabilizes.

# License

Ahmia is licensed under the [3-clause BSD
license](https://en.wikipedia.org/wiki/BSD_licenses#3-clause_license_.28.22Revised_BSD_License.22.2C_.22New_BSD_License.22.2C_or_.22Modified_BSD_License.22.29).
