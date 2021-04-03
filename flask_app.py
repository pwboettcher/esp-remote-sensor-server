# Copyright 2021 Peter Boettcher
# Distributed under the terms of the MIT License

from flask import Flask, request, jsonify, redirect, render_template, make_response
import MySQLdb

app = Flask(__name__)
app.config.from_object('mysql_config.Config')

def connect_db():
    db=MySQLdb.connect(host=app.config['MYSQL_HOST'],
                       user=app.config['MYSQL_USER'],
                       passwd=app.config['MYSQL_PASSWD'],
                       db=app.config['MYSQL_DB'])
    return db

# Just show the plot
@app.route('/')
def root():
    return render_template('plot.html')

# API endpoint to get x/y data for plotting.  The data is provided
# exactly as plotly wants
@app.route('/get_data/<int:days>')
def get_data(days: int = 1):
    db=connect_db()
    cursor = db.cursor()
    data = []
    cursor.execute("SELECT id, stype, name from sensors")
    idmap = {}
    for r in cursor:
        traceobj = {'id': r[0], 'name': r[2], 'x': [], 'y': []}
        if r[0]==11:
            color = 'green'
        elif r[0]==12:
            color = 'orange'
        else:
            color = None

        if r[1] == 'pir':
            traceobj['yaxis'] = 'y2'
        if color:
            traceobj['line'] = {'color': color}

        idmap[r[0]] = len(data)
        data.append( traceobj )

    validated_days = int(days)
    if validated_days < 1:
        validated_days = 1
    elif validated_days > 365:
        validated_days = 365
    cursor.execute("SELECT DATE_FORMAT( CONVERT_TZ(time, 'UTC', 'America/New_York'), '%Y-%m-%d %k:%i:%s') as t, id, val "
                   #" from measurements WHERE timestampdiff(DAY, time, '2020-01-01') BETWEEN -60 AND 120")
                    " from measurements WHERE timestampdiff(DAY, time, now()) <= " + str(validated_days))

    for d in cursor:
        idx = idmap.get(d[1], -1)
        if idx >= 0:
            data[idx]['x'].append(d[0])
            data[idx]['y'].append(d[2])

    return jsonify(measurements=data)

def do_log(msg):
    db=connect_db()
    cursor = db.cursor()
    cursor.execute("INSERT INTO log (msg) VALUES (%s)", (str(msg), ))
    db.commit()

# Accept incoming measurements, map the sensor serial number to id,
# and insert into database
@app.route('/post_measurements', methods=['GET', 'POST'])
def post_temps():
    db=connect_db()
    js = request.get_json(force=True)
    print(js)

    for s in js['measurements']:
        if 'debug' in s:
            print(s['debug'])
        sn = s['id']
        t = s['val']
        data = None
        while not data:
            cursor = db.cursor()
            cursor.execute("SELECT id from sensors where sn = %s", (sn,))
            data = cursor.fetchone()
            if data:
                id = data[0]
            else:
                cursor = db.cursor()
                cursor.execute("INSERT INTO sensors (sn, stype) VALUES (%s, %s)", (sn, s['type']))

        cursor = db.cursor()
        if not t:
            t = 0.0
        cursor.execute("INSERT INTO measurements (id, val) VALUES (%s, %s)", (id, float(t)))
        db.commit()

    return jsonify({'success': [1, 1]})

# Just track boot and initial connection of device.  Advertise
# current firmware version we have, in case device wants to
# update over-the-air
@app.route('/hello', methods=['GET', 'POST'])
def hello():
    js = request.get_json(force=True)
    do_log('New connection from ' + js['chip'] + ' with sensors:')
    sstr = ''
    for s in js['sensors']:
        sstr = sstr + '[%s %s] ' % (s['type'], s['id'])
    do_log(sstr)
    return jsonify(data={'fwversion': 12})

# Template-based user-page to view and edit names of sensors
@app.route('/sensors')
def sensors():
    db=connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, sn, name from sensors")
    sensors = [ {'id': r[0], 'sn': r[1], 'name': r[2]} for r in cursor ]
    return render_template('sensors.html', sensors=sensors)

# API endpoint for "save" callback from /sensors page
@app.route('/sensoredit', methods=['GET', 'POST'])
def sensoredit():
    db=connect_db()
    res = request.get_json(force=True)

    for r in res['sensors']:
        cursor = db.cursor()
        cursor.execute("UPDATE sensors SET name=%s WHERE id=%s", (r[1],r[0]))

    db.commit()
    return jsonify({'success': 1})

@app.route('/logs')
def logs():
    db=connect_db()
    cursor = db.cursor()
    cursor.execute("SELECT time, msg from log ORDER BY time DESC LIMIT 50")
    text = [ str(r[0]) + ' ' + r[1] for r in cursor ]
    response = make_response("\n".join(text), 200)
    response.mimetype = "text/plain"
    return response
