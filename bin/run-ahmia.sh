#!/bin/sh

# the only mandatory setting is setting VIRTUALENV or not (if system-wide installation)
# VIRTUALENV=venv

USER=$(whoami)   # change this to run gunicorn with alternative user and most likely get permission errors
# GROUP=www-data                               # causes permission error connecting to SOCKET
PROJECT_ROOT=/usr/local/lib/ahmia-site/ahmia   # root dir of django
GUNICORN=gunicorn                              # path to gunicorn executable
APP=ahmia.wsgi:application                     # wsgi application
SOCKET=/tmp/ahmia.sock                         # the socket that nginx will search for
PID=/tmp/project-master.pid                    # the path to the pid of current gunicorn instance
NAME=ahmia-site                                # name of the application (optional)
NUM_WORKERS=6                                  # number of gunicorn processes
MAX_REQUESTS=5000                              # max requests a worker will process
LOG_FILE=gunicorn.log                          # not used if ran as daemon (check at the end)
ENV=LANG='en_US.UTF-8'
DJANGO_SETTINGS_MODULE=ahmia.settings.prod

export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$PROJECT_ROOT:$PYTHONPATH

if [ -f $PID ]; then rm $PID; fi

# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKET)
test -d $RUNDIR || mkdir -p $RUNDIR

# if there is a Virtual environment path set, activate it
if [ $VIRTUALENV ]; then
    . $VIRTUALENV/bin/activate
fi

cd $PROJECT_ROOT

# Remove --daemon if you want to be able to kill current processes with ctrl-C in the console.
# Eitherwise you will have to manually send kill signal, e.g: `killall gunicorn`
exec $GUNICORN $APP --daemon \
  --pid=$PID \
  --bind=unix:$SOCKET \
  --name $NAME \
  --workers $NUM_WORKERS \
  --max-requests $MAX_REQUESTS \
  --log-level=debug \
  --log-file=$LOG_FILE \
  --env $ENV \
  --user=$USER \
# --group=$GROUP
