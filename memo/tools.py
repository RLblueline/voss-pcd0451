"""Tools M.E.M.O. can call. Every handler returns a JSON string."""
import json
import logging
import threading
import time
import urllib.parse
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path

from . import config
from . import printer as printer_mod

log = logging.getLogger("memo.tools")

SCHEMAS = [
    {"name": "get_time", "description": "Current local date and time.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "set_timer", "description": "Start a countdown timer. Announced aloud when it ends.",
     "input_schema": {"type": "object", "properties": {
         "seconds": {"type": "integer", "description": "Total duration in seconds"},
         "label": {"type": "string", "description": "Short name, e.g. 'pasta'"}},
         "required": ["seconds"]}},
    {"name": "list_timers", "description": "List running timers and time remaining.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "cancel_timer", "description": "Cancel a timer by label, or all timers.",
     "input_schema": {"type": "object", "properties": {
         "label": {"type": "string", "description": "Label to cancel, or 'all'"}},
         "required": ["label"]}},
    {"name": "get_weather", "description": "Current weather and today/tomorrow forecast. "
                                          "Defaults to home; pass a place name for elsewhere.",
     "input_schema": {"type": "object", "properties": {
         "place": {"type": "string", "description": "Optional city name"}}}},
    {"name": "checklist", "description": "The Mandatory Preparedness Checklist (to-do list).",
     "input_schema": {"type": "object", "properties": {
         "action": {"type": "string", "enum": ["list", "add", "check", "uncheck", "remove", "clear_done"]},
         "item": {"type": "string"}}, "required": ["action"]}},
    {"name": "notes", "description": "Employee's permanent record: saved notes.",
     "input_schema": {"type": "object", "properties": {
         "action": {"type": "string", "enum": ["add", "list", "search", "delete"]},
         "text": {"type": "string", "description": "Note text, search query, or note id to delete"}},
         "required": ["action"]}},
    {"name": "print_memo", "description": "Print on the thermal printer. Kinds: memo, writeup "
                                         "(notice of infraction), commendation, checklist.",
     "input_schema": {"type": "object", "properties": {
         "kind": {"type": "string", "enum": ["memo", "writeup", "commendation", "checklist"]},
         "subject": {"type": "string"},
         "body": {"type": "string", "description": "Under 60 words"}},
         "required": ["kind"]}},
]

WMO = {0: "clear", 1: "mostly clear", 2: "partly cloudy", 3: "overcast", 45: "fog", 48: "freezing fog",
       51: "light drizzle", 53: "drizzle", 55: "heavy drizzle", 61: "light rain", 63: "rain",
       65: "heavy rain", 66: "freezing rain", 67: "freezing rain", 71: "light snow", 73: "snow",
       75: "heavy snow", 77: "snow grains", 80: "rain showers", 81: "rain showers",
       82: "violent rain showers", 85: "snow showers", 86: "snow showers", 95: "thunderstorms",
       96: "thunderstorms with hail", 99: "thunderstorms with hail"}


class JsonStore:
    def __init__(self, path, default):
        self.path, self.default = Path(path), default
        self.lock = threading.Lock()

    def load(self):
        try:
            return json.loads(self.path.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return json.loads(json.dumps(self.default))

    def save(self, data):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(self.path)


def _http_json(url, timeout=6):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode())


class ToolBox:
    def __init__(self, events, printer=None, http=_http_json):
        self.events = events          # queue for ("timer", label)
        self.printer = printer
        self.http = http
        self.timers = {}              # id -> (label, end_monotonic, Timer)
        self.checklist = JsonStore(config.DATA_DIR / "checklist.json", [])
        self.notes = JsonStore(config.DATA_DIR / "notes.json", [])
        self.schemas = SCHEMAS

    def dispatch(self, name, args):
        fn = getattr(self, "t_" + name, None)
        try:
            out = fn(**(args or {})) if fn else {"error": f"unknown tool {name}"}
        except Exception as e:
            log.exception("tool %s failed", name)
            out = {"error": str(e)}
        return json.dumps(out)

    # ------------------------------------------------------------ time / timers
    def t_get_time(self):
        now = datetime.now()
        return {"local": now.strftime("%A %B %d %Y %I:%M %p"), "iso": now.isoformat(timespec="seconds")}

    def t_set_timer(self, seconds, label="timer"):
        seconds = int(seconds)
        if seconds <= 0 or seconds > 24 * 3600:
            return {"error": "duration must be between 1 second and 24 hours"}
        tid = uuid.uuid4().hex[:6]
        t = threading.Timer(seconds, self._fire, args=(tid,))
        t.daemon = True
        self.timers[tid] = (label, time.monotonic() + seconds, t)
        t.start()
        return {"ok": True, "label": label, "seconds": seconds}

    def _fire(self, tid):
        entry = self.timers.pop(tid, None)
        if entry:
            self.events.put(("timer", entry[0]))

    def t_list_timers(self):
        now = time.monotonic()
        return {"timers": [{"label": l, "remaining_s": int(end - now)} for l, end, _ in self.timers.values()]}

    def t_cancel_timer(self, label):
        hit = [tid for tid, (l, _, _) in self.timers.items()
               if label.lower() == "all" or l.lower() == label.lower()]
        for tid in hit:
            self.timers.pop(tid)[2].cancel()
        return {"cancelled": len(hit)}

    # ------------------------------------------------------------ weather
    def t_get_weather(self, place=None):
        lat, lon, name = config.LAT, config.LON, "home"
        if place:
            q = urllib.parse.urlencode({"name": place, "count": 1})
            res = self.http("https://geocoding-api.open-meteo.com/v1/search?" + q).get("results")
            if not res:
                return {"error": f"could not find {place}"}
            lat, lon, name = res[0]["latitude"], res[0]["longitude"], res[0]["name"]
        if lat is None or lon is None:
            return {"error": "home location not configured (set MEMO_LAT and MEMO_LON)"}
        q = urllib.parse.urlencode({
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,apparent_temperature,weather_code,wind_speed_10m",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code",
            "temperature_unit": config.TEMP_UNIT, "wind_speed_unit": config.WIND_UNIT,
            "timezone": "auto", "forecast_days": 2})
        d = self.http("https://api.open-meteo.com/v1/forecast?" + q)
        cur, day = d["current"], d["daily"]
        days = [{"high": day["temperature_2m_max"][i], "low": day["temperature_2m_min"][i],
                 "rain_chance_pct": day["precipitation_probability_max"][i],
                 "conditions": WMO.get(day["weather_code"][i], "unknown")} for i in range(len(day["time"]))]
        return {"place": name, "units": config.TEMP_UNIT,
                "now": {"temp": cur["temperature_2m"], "feels_like": cur["apparent_temperature"],
                        "conditions": WMO.get(cur["weather_code"], "unknown"),
                        "wind": cur["wind_speed_10m"], "wind_unit": config.WIND_UNIT},
                "today": days[0], "tomorrow": days[1] if len(days) > 1 else None}

    # ------------------------------------------------------------ checklist
    def t_checklist(self, action, item=None):
        with self.checklist.lock:
            items = self.checklist.load()
            find = lambda: next((i for i in items if item and i["item"].lower() == item.lower()), None)
            if action == "add":
                if not item:
                    return {"error": "item required"}
                if not find():
                    items.append({"item": item, "done": False})
            elif action in ("check", "uncheck"):
                it = find()
                if not it:
                    return {"error": f"no item '{item}'", "items": items}
                it["done"] = action == "check"
            elif action == "remove":
                it = find()
                if not it:
                    return {"error": f"no item '{item}'", "items": items}
                items.remove(it)
            elif action == "clear_done":
                items = [i for i in items if not i["done"]]
            elif action != "list":
                return {"error": f"unknown action {action}"}
            self.checklist.save(items)
            return {"items": items}

    # ------------------------------------------------------------ notes
    def t_notes(self, action, text=None):
        with self.notes.lock:
            notes = self.notes.load()
            if action == "add":
                if not text:
                    return {"error": "text required"}
                n = {"id": len(notes) + 1 if not notes else notes[-1]["id"] + 1,
                     "time": datetime.now().isoformat(timespec="minutes"), "text": text}
                notes.append(n)
                self.notes.save(notes)
                return {"ok": True, "record_no": n["id"]}
            if action == "list":
                return {"notes": notes[-10:], "total": len(notes)}
            if action == "search":
                q = (text or "").lower()
                return {"notes": [n for n in notes if q in n["text"].lower()][-10:]}
            if action == "delete":
                before = len(notes)
                notes = [n for n in notes if str(n["id"]) != str(text)]
                self.notes.save(notes)
                return {"deleted": before - len(notes)}
            return {"error": f"unknown action {action}"}

    # ------------------------------------------------------------ printing
    def t_print_memo(self, kind, subject="", body=""):
        if not self.printer:
            return {"error": "printer offline"}
        items = self.checklist.load() if kind == "checklist" else None
        record_no = len(self.notes.load()) + 1
        job = printer_mod.build(kind, subject, body, items=items, record_no=record_no)
        self.printer.print_job(job)
        return {"ok": True, "printed_lines": len(job.lines)}
