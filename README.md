[![Build Status](https://travis-ci.org/iriahi/ahmia-site.svg?branch=master)](https://travis-ci.org/iriahi/ahmia-site)
[![Requirements Status](https://requires.io/github/iriahi/ahmia-site/requirements.svg?branch=master)](https://requires.io/github/iriahi/ahmia-site/requirements/?branch=master)

![https://ahmia.fi/](https://raw.githubusercontent.com/razorfinger/ahmia/ahmia-redesign/ahmia-logotype.png)

Ahmia is the search engine for `.onion` domains on the Tor anonymity
network. It is led by [Juha Nurmi](//github.com/juhanurmi) and is based
in Finland.


# Compatibility

The newest version of Ahmia is built with Python 2.7, Django and
Elasticsearch. You will need to know these technologies to create a
working Ahmia installation. Ahmia crawls using [OnionBot](https://github.com/iriahi/ahmia-crawler).


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

# Run the site

## Migrate db
```sh
$ python manage.py migrate
```

## Start development server
```sh
$ python manage.py runserver
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

# Support

No support is currently provided. It is up to you for now. This will
change as Ahmia stabilizes.

# License

Ahmia is licensed under the [3-clause BSD
license](https://en.wikipedia.org/wiki/BSD_licenses#3-clause_license_.28.22Revised_BSD_License.22.2C_.22New_BSD_License.22.2C_or_.22Modified_BSD_License.22.29).
