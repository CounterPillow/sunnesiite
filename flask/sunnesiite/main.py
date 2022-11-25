from datetime import datetime, timezone
from io import BytesIO
import json
from math import ceil
import os.path
import urllib.request
from urllib.parse import urljoin, urlencode

from flask import (
    Blueprint, current_app, request, Response
)
from PIL import Image, ImageDraw, ImageFont


bp = Blueprint('main', __name__)


COLOURS = {
    "red": (138, 76, 91),
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "blue": (85, 94, 126),
    "green": (67, 138, 28),
    "yellow": (255, 243, 56),
    "orange": (232, 126, 0),
    "violet": (194, 164, 244),
}


def fetch_peak(d1, d2):
    # astimezone needed here because python is dumb (offset aware timedelta)
    d_now = datetime.utcnow().astimezone(timezone.utc)
    diff_s = ceil((d_now - d1).total_seconds())

    params = urlencode(
        {
            "start": d1.isoformat(),
            "end": d2.isoformat(),
            "query": 'max_over_time(power_power{location="home"}[' + str(diff_s) + 's])',
        }
    )

    vm_url = urljoin(current_app.config["SUNNESIITE_VM_URI"],
                     f"/api/v1/query?{params}")

    resp = urllib.request.urlopen(vm_url)
    j = json.loads(resp.read().decode('utf-8'))
    if j.get("status", "") != "success":
        raise Exception("Request failed")

    try:
        ts, val = j["data"]["result"][0]["value"]
    except IndexError:
        ts = -1
        val = 0
    return (ts, int(val))


def fetch_data(d1, d2):

    params = urlencode(
        {
            "start": d1.isoformat(),
            "end": d2.isoformat(),
            "step": "2m",
            "query": 'power_power{location="home"}',
        }
    )

    vm_url = urljoin(current_app.config["SUNNESIITE_VM_URI"],
                     f"/api/v1/query_range?{params}")

    resp = urllib.request.urlopen(vm_url)
    data_ts = []
    data_val = []

    j = json.loads(resp.read().decode('utf-8'))
    if j.get("status", "") != "success":
        raise Exception("Request failed")
    try:
        for ts, val in j["data"]["result"][0]["values"]:
            data_ts.append(ts)
            data_val.append(int(val))
    except IndexError:
        pass

    return (data_ts, data_val)


@bp.route("/eink.png", methods=["GET"])
def eink():
    d1 = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
    d2 = d1.replace(hour=22)
    d1 = d1.astimezone(timezone.utc)
    d2 = d2.astimezone(timezone.utc)
    ts, val = fetch_data(d1, d2)
    im = Image.new('RGB', (600, 448), (255, 255, 255))
    draw = ImageDraw.Draw(im)

    MAX_Y = 5000.0
    TICK_POWER_STEP = 1000
    TICK_TIME_STEP = 1
    TICK_LEN = 5
    PLOT_HEIGHT = 400
    X_OFFSET = 80
    Y_OFFSET = 20

    y1 = 0
    y2 = 0
    for i in range(len(val) - 1):
        y1 = Y_OFFSET + PLOT_HEIGHT - int(val[i] / MAX_Y * PLOT_HEIGHT)
        y2 = Y_OFFSET + PLOT_HEIGHT - int(val[i + 1] / MAX_Y * PLOT_HEIGHT)
        draw.line((i + X_OFFSET, y1, i+1 + X_OFFSET, y2), fill=COLOURS["red"],
                  width=3)

    # Y axis
    draw.line((X_OFFSET - 1, Y_OFFSET, X_OFFSET - 1, PLOT_HEIGHT + Y_OFFSET),
              fill=COLOURS["black"])
    # X axis
    draw.line((X_OFFSET - 1, PLOT_HEIGHT + Y_OFFSET, X_OFFSET - 1 + 480, PLOT_HEIGHT + Y_OFFSET),
              fill=COLOURS["black"])

    # Labels
    label_fnt = ImageFont.truetype("LiberationMono-Bold.ttf", 16)
    for tick in range(0, int(MAX_Y) + 1, TICK_POWER_STEP):
        tick_y = Y_OFFSET + PLOT_HEIGHT - int(tick / MAX_Y * PLOT_HEIGHT)
        draw.line((X_OFFSET - 1 - TICK_LEN, tick_y, X_OFFSET - 1, tick_y),
                  fill=COLOURS["black"])
        draw.text((X_OFFSET - 1 - TICK_LEN - 4, tick_y), f"{tick} W", anchor="rm",
                  font=label_fnt, fill=COLOURS["black"])

    for time_tick in range(6, 22 + 1, TICK_TIME_STEP):
        tick_x = int((time_tick - 6) / 16.0 * 480) + X_OFFSET - 1
        draw.line((tick_x, PLOT_HEIGHT + Y_OFFSET, tick_x, PLOT_HEIGHT + Y_OFFSET + TICK_LEN),
                  fill=COLOURS["black"])
        draw.text((tick_x, PLOT_HEIGHT + Y_OFFSET + TICK_LEN + 4), f"{time_tick}",
                  anchor="mt", font=label_fnt, fill=COLOURS["black"])

    # last data point, the min keeps it above the axis
    if len(val) > 0:
        draw.text((X_OFFSET + len(val) + 5, min(y2, PLOT_HEIGHT + Y_OFFSET - 10)), f"{val[len(val) - 1]} W", font=label_fnt,
                anchor="lm", fill=COLOURS["red"])

    # peak text
    peak_ts, peak_val = fetch_peak(d1, d2)
    if peak_ts >= 0:
        draw.text((X_OFFSET + 240, 20), f"Peak: {peak_val} W", anchor="mt", font=label_fnt,
                  fill=COLOURS["green"])


    bio = BytesIO()
    im.save(bio, "PNG")

    resp = Response(status=200, mimetype="image/png", content_type="image/png")
    resp.set_data(bio.getvalue())
    bio.close()

    return resp


@bp.route("/solardata", methods=["POST"])
def solardata():
    api_key = request.args.get('api_key', '')

    if api_key != current_app.config["SUNNESIITE_API_KEY"]:
        return ("Unauthorised\n", 401)

    j = json.loads(request.get_data().decode('utf-8'))

    try:
        ts = datetime.fromisoformat(j["Head"]["Timestamp"])
        pac = sum(j["Body"]["PAC"]["Values"].values())
        day_energy = sum(j["Body"]["DAY_ENERGY"]["Values"].values())
    except (KeyError, ValueError):
        return ("Malformed data\n", 400)

    vm_url = urljoin(current_app.config["SUNNESIITE_VM_URI"],
                     "/write?precision=s")
    vm_data = f"power,location=home power={pac} {int(ts.timestamp())}".encode('utf-8')
    req = urllib.request.Request(vm_url, data=vm_data, method='POST')
    resp = urllib.request.urlopen(req)

    # Switch to just "status" once we're Python 3.9+
    if resp.code >= 300 or resp.code < 200:
        return ("Error submitting to VM\n", 500)

    return "Ok\n"
