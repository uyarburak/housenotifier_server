# -*- coding: utf-8 -*-
"""
    House Notifier
    ~~~~~~~~

    A house automation application written with Flask and sqlite3.

    :copyright: (c) 2017 by Burak UYAR.
"""
import threading
from sqlite3 import dbapi2 as sqlite3
from pyfcm import FCMNotification
from datetime import datetime, timedelta
from flask import Flask, request, \
     abort, g, flash, _app_ctx_stack
# configuration
DATABASE = '/tmp/house_notifier.db'
DEBUG = True

LAST_DOOR = datetime(1996, 4, 15, 16, 14)
LAST_RING = datetime(1996, 4, 15, 16, 14)
TMP_DOOR = []
TMP_RING = []

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('HOUSE_NOTIFIER_SETTINGS', silent=True)


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    top = _app_ctx_stack.top
    if not hasattr(top, 'sqlite_db'):
        top.sqlite_db = sqlite3.connect(app.config['DATABASE'])
        top.sqlite_db.row_factory = sqlite3.Row
    return top.sqlite_db


@app.teardown_appcontext
def close_database(exception):
    """Closes the database again at the end of the request."""
    top = _app_ctx_stack.top
    if hasattr(top, 'sqlite_db'):
        top.sqlite_db.close()


def run_sql_file(filename):
    """Initializes the database."""
    db = get_db()
    with app.open_resource(filename, mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    run_sql_file('schema.sql')
    print('Initialized the database.')


def query_db(query, args=(), one=False):
    """Queries the database and returns a list of dictionaries."""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv

@app.route('/door')
def door_opened():
    return common_method(door_log, 'LAST_DOOR', 'TMP_DOOR')

@app.route('/ring')
def door_ringed():
    return common_method(door_log, 'LAST_RING', 'TMP_RING')

def common_method(logMethod, variable, arr, timeout=3):
    diff = datetime.now() - app.config[variable]
    if diff > timedelta(minutes=timeout):
        ask_users(arr)
        logMethod()
        app.config[variable] = datetime.now()
        return 'zaa'
    return 'sorry'


def ask_users(arr):
    #push_service = FCMNotification(api_key="<api-key>")
    #result = push_service.notify_topic_subscribers(topic_name="arduino", message_body="Evde misin bebisim xD")
    app.config[arr] = []
    threading.Timer(15, check_answers, args=(arr,)).start()
    print "timer has start"

def check_answers(arr):
    TEMP = app.config[arr]
    print 'checking answers'
    print arr
    print TEMP
    if "1" in TEMP:
        print 'we are home'
        return
    print 'send notification'


def door_log():
    db = get_db()
    db.execute('insert into door_log (id) values (null)');
    db.commit()
    print 'door logged'

def ring_log():
    db = get_db()
    db.execute('insert into ring_log (id) values (null)');
    db.commit()
    print 'ring logged'

@app.route('/phone/<device_id>/<is_wifi>')
def phone_log(device_id, is_wifi):
    app.config['TMP_DOOR'].append(is_wifi)
    app.config['TMP_RING'].append(is_wifi)
    db = get_db()
    db.execute('''insert into phone_log (device_id, is_wifi) values
         (?, ?)''', (device_id, is_wifi));
    db.commit()
    print 'phone logged'
    return 'welldone'