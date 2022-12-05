# sunnesiite

A Python flask and Arduino project for receiving SolarAPI current data in the
flask app, saving it into VictoriaMetrics, and then generating a PNG graph
from a VictoriaMetrics query showing the daily solar production, and a
Inkplate 6COLOR Arduino sketch to fetch and display this PNG periodically


## Usage

### ESP32

Drop a `config.h` with contents like this next to the `.ino`, replace the
values with whatever is the case for you:

```C
#define WIFI_SSID "YourSSID"
#define WIFI_PASSWORD "hunter2"
#define EINK_URL "http://example.example/eink.png"
#define API_URL "http://example.example/untildaytime"
#define TIMEZONE "Europe/Zurich"
```

The default refresh interval is every 4 minutes between 6:00 and 22:00.

You'll need to install `ArduinoJson` (not `Arduino_Json`!) from the libraries
manager.


### Flask

You'll need Python 3.9 or later.

Create a virtualenv and activate it:

```
$ cd flask
$ virtualenv venv
$ source venv/bin/activate
```

Then install the package in editable mode:

```
$ pip install -e .
```

Next, you'll want to create an `instance/config.toml` in your flask directory,
with contents like:

```toml
# Keep this secret, keep this safe. Auto-generate it from a cryptographically
# secure random source, e.g. pwgen -s 64 1
SECRET_KEY = "hunter2"
# Prefix for all the endpoint URLs
SUNNESIITE_PREFIX = ""
# This one needs to be the API key your solarapi push service on the inverter
# uses, make it long, random and secret as well. Anyone who has it can fill
# your time series database with data!
SUNNESIITE_API_KEY = "hunter2"
# URI for your VictoriaMetrics server, as-is if running locally with default
# port
SUNNESIITE_VM_URI = "http://127.0.0.1:8428"
# Change for deployments to something better, see Flask-Caching documentation
CACHE_TYPE = "SimpleCache"
CACHE_DEFAULT_TIMEOUT = 120
```

You can now run the app in development mode:

```
$ flask --app sunnesiite run --port yourport -h yourip
```

If you don't specify `yourip` here, the development server will only listen to
local connections, which means your Inkplate 6COLOR won't be able to fetch from
it.


#### Deploying To Production

If you want to deploy this in production, you'll need something like uwsgi.

You'll want to `pip install --no-binary pyuwsgi pyuwsgi` (see
[Flask's documentation](https://flask.palletsprojects.com/en/latest/deploying/uwsgi/)
for oher ways) and then use the `wsgi` stub script to launch the app, like
this:

```
$ uwsgi --http-socket 127.0.0.1:8000 --master -p $(nproc) -w wsgi:app
```

It's a good idea to make your services actual systemd services, so use an unit
file like this (adjust as appropriate):

```
[Unit]
Description=Sunnesiite Flask Component
After=network.target

[Service]
DynamicUser=true
LogsDirectory=sunnesiite-flask
StateDirectory=sunnesiite-flask

AmbientCapabilities=
CapabilityBoundingSet=
LockPersonality=true
ProtectControlGroups=true
ProtectKernelModules=true
ProtectKernelTunables=true

User=sunnesiite-flask
Group=sunnesiite-flask
ExecStart=/path/to/your/venv/bin/uwsgi --http-socket 127.0.0.1:8000 --master -p 8 -w wsgi:app -H /path/to/your/venv/
WorkingDirectory=/path/to/sunnesiite/flask/
Environment="PATH=/path/to/your/venv/bin"

[Install]
WantedBy=multi-user.target
```

Then throw this behind e.g. an nginx reverse proxy.

For VictoriaMetrics, I'd make doubly sure it only listens to connections from
localhost, unless you are explicitly trying to use a remote VictoriaMetrics
server and have auth stuff figured out (I don't).

Please note that Fronius inverters seemingly only support pushing through plain
text HTTP, not HTTPS. This will mean that your reverse proxy should accept
connections on plain text HTTP and serve the web app there, not try to redirect
to HTTPS.
