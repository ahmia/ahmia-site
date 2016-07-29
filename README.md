[![Build Status](https://travis-ci.org/ahmia/ahmia-site.svg?branch=master)](https://travis-ci.org/iriahi/ahmia-site)
[![Code Health](https://landscape.io/github/iriahi/ahmia-site/master/landscape.svg?style=flat)](https://landscape.io/github/iriahi/ahmia-site/master)
[![Requirements Status](https://requires.io/github/iriahi/ahmia-site/requirements.svg?branch=master)](https://requires.io/github/iriahi/ahmia-site/requirements/?branch=master)

![https://ahmia.fi/](https://raw.githubusercontent.com/razorfinger/ahmia/ahmia-redesign/ahmia-logotype.png)

Ahmia is the search engine for `.onion` domains on the Tor anonymity
network. It is led by [Juha Nurmi](//github.com/juhanurmi) and is based
in Finland. This repository contains ahmia.fi source code.

# Compatibility

The newest version of Ahmia is built with Python 2.7, Django and
Elasticsearch. You will need to know these technologies to create a
working Ahmia installation. Ahmia crawls using [OnionBot](https://github.com/ahmia/ahmia-crawler).

# Prerequisites
[Ahmia-index](https://github.com/iriahi/ahmia-index) should be installed and running

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

# Run site in dev mode

## Migrate db
```sh
$ python ahmia/manage.py migrate
```

## Start development server
```sh
$ python ahmia/manage.py runserver
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

# FAQ 

## How can populate my index to do searches ?
You should use [OnionElasticBot](https://github.com/ahmia/ahmia-crawler/tree/master/onionElasticBot) to populate your index.

## Why can't my browser load django statics ?
The django settings.py is configured in a way that it only serve statics if DEBUG is True. Please verify [here](https://github.com/ahmia/ahmia-site/blob/master/ahmia/ahmia/settings.py#L9) if it's the case. You can change this behaviour [here](https://github.com/ahmia/ahmia-site/blob/master/ahmia/ahmia/urls.py#L18).

## What should I use to host ahmia in a production environment ?
Config samples are in [config/](https://github.com/ahmia/ahmia-site/tree/master/conf). We suggest Apache2 or Nginx with Uwsgi

# Support

No support is currently provided. It is up to you for now. This will
change as Ahmia stabilizes.

# License

Ahmia is licensed under the [3-clause BSD
license](https://en.wikipedia.org/wiki/BSD_licenses#3-clause_license_.28.22Revised_BSD_License.22.2C_.22New_BSD_License.22.2C_or_.22Modified_BSD_License.22.29).
