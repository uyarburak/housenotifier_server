# -*- coding: utf-8 -*-
"""
    House Notifier
    ~~~~~~~~

    A house automation application written with Flask and sqlite3.

    :copyright: (c) 2017 by Burak UYAR.
"""
import json
import threading
from sqlite3 import dbapi2 as sqlite3
from pyfcm import FCMNotification
from datetime import datetime, timedelta
from flask import Flask, request, \
     abort, g, flash, _app_ctx_stack
# configuration
DATABASE = '/tmp/house_notifier.db'
DEBUG = True
GCM_TOPIC_NAME = 'arduino'
GCM_API_KEY = 'XXX' # CHANGE THIS
ROUTER_MAC_ID = '08:10:76:00:c3:4b' # CHANGE THIS

LAST_DOOR = datetime(1996, 4, 15, 16, 14)
LAST_RING = datetime(1996, 4, 15, 16, 14)
LAST_GAS = datetime(1996, 4, 15, 16, 14)
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

def send_notification(data_message):
    print 'sending notification'
    push_service = FCMNotification(api_key=app.config['GCM_API_KEY'])
    result = push_service.notify_topic_subscribers(topic_name=app.config['GCM_TOPIC_NAME'], data_message=data_message)

@app.route('/logs/door')
def logs_door():
    return table_to_json('door_log')

@app.route('/logs/ring')
def logs_ring():
    return table_to_json('ring_log')

@app.route('/logs/gas')
def logs_gas():
    return table_to_json('gas_log')

@app.route('/logs/phone')
def logs_phone():
    return table_to_json('phone_log')


def table_to_json(table_name):
    rows = query_db('select * from '+table_name)
    if not rows:
        return '[]'
    atts = rows[0].keys()
    arr = []
    for row in rows:
        obj = {}
        for att in atts:
            obj[att] = row[att]
        arr.append(obj);
    return json.dumps(arr)

@app.route('/door')
def door_opened():
    return common_method(door_log, 'LAST_DOOR', 'TMP_DOOR')

@app.route('/ring')
def door_ringed():
    return common_method(door_log, 'LAST_RING', 'TMP_RING')

@app.route('/gas/<threshold>/<measured_value>')
def gas_alarm(threshold, measured_value):
    diff = datetime.now() - app.config['LAST_GAS']
    if diff > timedelta(minutes=2):
        data_message = {
            "id" : "3",
            "body" : "Gas level out of threshold!",
            "threshold" : threshold,
            "value": measured_value
        }
        send_notification(data_message)
        app.config['LAST_GAS'] = datetime.now()
        gas_log(measured_value)
    return "OK"

def common_method(logMethod, variable, arr, timeout=3):
    diff = datetime.now() - app.config[variable]
    if diff > timedelta(minutes=timeout):
        ask_users(arr)
        logMethod()
        app.config[variable] = datetime.now()
        return 'zaa'
    return 'sorry'


def ask_users(arr):
    data_message = {
            "id" : "-1",
            "body" : "Are you at home?",
            "ssid" : app.config['ROUTER_MAC_ID']
    }
    send_notification(data_message)
    app.config[arr] = []
    threading.Timer(15, check_answers, args=(arr,)).start()
    print "timer has start"

def check_answers(arr):
    if arr == 'TMP_DOOR':
        data_message = {
                "id" : "1",
                "body" : "Door has opened"
        }
    else:
        data_message = {
                "id" : "2",
                "body" : "Bell has rang"
        }
    print 'checking answers'
    if "1" in app.config[arr]: # Do nothing if there is someone at home.
        print 'we are home'
    else: # Send notification to everyone.
        send_notification(data_message)
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

def gas_log(value):
    db = get_db()
    db.execute('insert into gas_log (value) values (?)', [value]);
    db.commit()
    print 'gas logged'

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