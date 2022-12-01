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
