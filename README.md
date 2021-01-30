esp-remote-sensor-server
This repository: https://github.com/pwboettcher/esp-remote-sensor-server

This is the server-side component for the ESP-based remote sensor software
at https://github.com/pwboettcher/esp-remote-sensor-client

It is a simple Python Flask app that exposes REST endpoints for the remote
sensors to submit measurements, which are logged into a MySQL database.  There
is also a VERY SIMPLY Plotly.js plot that shows the timeseries of the
submitted measurements.

I used [PythonAnywhere](https://pythonanywhere.com) for the hosting.


SETUP (Assuming PythonAnywhere)

Upload this directory into PythonAnywhere.

Create a MySQL database from the dashboard, and make note of the
username/password.  Copy `mysql_config_template.py` into `mysql_config.py`,
and edit your MySQL connection information into it.  Open and run
the db_init.py file to create the tables and verify your MySQL setup.

Next, create a web application through the dashboard.  In the web app
configuration page, point the source code configuration option to the
uploaded source directory.  In the same place, edit the WSGI file to
start up the Flask app.  It should look something like this:

    import sys

    # add your project directory to the sys.path
    project_home = u'/home/<username>/esp-remote-sensor-server'
    if project_home not in sys.path:
        sys.path = [project_home] + sys.path

    # import flask app but need to call it "application" for WSGI to work
    from flask_app import app as application

Adjust any other web app settings you want.  Recommended: require https.
Password aren't supported by the device side.

Then, click "Reload webpage".  Go see if it worked!  The logs are available
right on the `web app` dashboard if something didn't...


OVER THE AIR DEVICE UPDATES

After a new build, upload the compiled `sensor.bin` file from the ESP
respository into the `/static` folder.  Be sure to update the version tag
in the source code.  Set the `fwvers` endpoint in `flask_app.py` to match
the new version, to force devices to reload the firmware from this image.
