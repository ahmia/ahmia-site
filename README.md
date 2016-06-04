[![Build Status](https://travis-ci.org/iriahi/ahmia-site.svg?branch=master)](https://travis-ci.org/iriahi/ahmia-site)

![https://ahmia.fi/](https://raw.githubusercontent.com/razorfinger/ahmia/ahmia-redesign/ahmia-logotype.png)

Ahmia is the search engine for `.onion` domains on the Tor anonymity
network. It is led by [Juha Nurmi](//github.com/juhanurmi) and is based
in Finland.

# Development warning

Ahmia is currently under active development and may require a different
stack shortly. **These directions may become outdated. Please check with
Juha if they are still accurate if you have problems.**


# Compatibility

The newest version of Ahmia is built with Python 2.7, Django and
Elasticsearch. You will need to know these technologies to create a
working Ahmia installation. Ahmia crawls using OnionBot.


# Installation guide

## Install dependencies:

### Ubuntu 16.04
```sh
# apt-get install build-essential python-pip
# apt-get install libxml2-dev libxslt1-dev python-dev libpq-dev libffi-dev libssl-dev
```

### Fedora 23
```sh
# dnf install @development-tools redhat-rpm-config python-pip
# dnf install libxml-devel libxslt-devel python-devel postgresql-devel libffi-devel openssl-devel
```

## Install requirements

```sh
$ pip install -r requirements.txt
```

## Verify django settings
If using django dev server (manage.py runserver), you will not get static files if DEBUG is False.

## Migrate db
```sh
$ python manage.py migrate
```

# Support

No support is currently provided. It is up to you for now. This will
change as Ahmia stabilizes.


# License

Ahmia is licensed under the [3-clause BSD
license](https://en.wikipedia.org/wiki/BSD_licenses#3-clause_license_.28.22Revised_BSD_License.22.2C_.22New_BSD_License.22.2C_or_.22Modified_BSD_License.22.29).
