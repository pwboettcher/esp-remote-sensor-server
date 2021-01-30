# Copyright 2021 Peter Boettcher
# Distributed under the terms of the MIT License

from flask import Flask, request, jsonify, redirect, render_template
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
@app.route('/get_data')
def get_data():
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

    cursor.execute("SELECT DATE_FORMAT( CONVERT_TZ(time, 'UTC', 'America/New_York'), '%Y-%m-%d %k:%i:%s') as t, id, val "
                   " from measurements WHERE timestampdiff(DAY, time, '2020-01-01') BETWEEN -60 AND 120")
                   # " from measurements WHERE timestampdiff(HOUR, time, now()) <= 24")

    for d in cursor:
        idx = idmap.get(d[1], -1)
        if idx >= 0:
            data[idx]['x'].append(d[0])
            data[idx]['y'].append(d[2])

    return jsonify(measurements=data)

# Accept incoming measurements, map the sensor serial number to id,
# and insert into database
@app.route('/post_measurements', methods=['GET', 'POST'])
def post_temps():
    db=connect_db()
    js = request.get_json(force=True)

    for s in js['measurements']:
        if 'debug' in s:
            print(s['debug'])
        sn = s['id']
        t = s['val']
        data = None
        while not data:
            cursor = db.cursor()
            cursor.execute("SELECT id from sensors where sn = '%s'" % sn)
            data = cursor.fetchone()
            if data:
                id = data[0]
            else:
                cursor = db.cursor()
                cursor.execute("INSERT INTO sensors (sn, stype) VALUES ('%s', '%s')" % (sn, s['type']))

        cursor = db.cursor()
        if not t:
            t = 0.0
        cursor.execute("INSERT INTO measurements (id, val) VALUES (%i, %f)" % (id, float(t)))
        db.commit()

    return jsonify({'success': [1, 1]})

# Just track boot and initial connection of device.  Advertise
# current firmware version we have, in case device wants to
# update over-the-air
@app.route('/hello', methods=['GET', 'POST'])
def hello():
    js = request.get_json(force=True)
    print(js)
    return jsonify(data={'fwversion': 11})

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

