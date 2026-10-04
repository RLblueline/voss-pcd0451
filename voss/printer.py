"""58 mm TTL thermal printer (ESC/POS) on UART TX GPIO14."""
import logging
import textwrap
import threading
import time
import unicodedata
from datetime import datetime

from . import config

log = logging.getLogger("voss.printer")

ESC, GS = b"\x1b", b"\x1d"
_REPL = {"\u2014": "-", "\u2013": "-", "\u2018": "'", "\u2019": "'", "\u201c": '"',
         "\u201d": '"', "\u2026": "...", "\u2022": "*", "\u00b0": " deg"}


def ascii_only(s):
    for k, v in _REPL.items():
        s = s.replace(k, v)
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


class Job:
    """Collects styled lines; renders to ESC/POS bytes and to a plain-text preview."""

    def __init__(self, cols=config.PRINTER_COLS):
        self.cols = cols
        self.lines = []    # (text, style) style: normal | bold | big | center | bcenter

    def add(self, text="", style="normal"):
        width = self.cols // 2 if style == "big" else self.cols
        text = ascii_only(text)
        wrapped = textwrap.wrap(text, width) or [""]
        self.lines += [(w, style) for w in wrapped]
        return self

    def rule(self, ch="-"):
        self.lines.append((ch * self.cols, "normal"))
        return self

    def field(self, label, value):
        return self.add(f"{label:<6}{value}")

    def preview(self):
        out = []
        for text, style in self.lines:
            width = self.cols // 2 if style == "big" else self.cols
            out.append(text.center(width) if style in ("center", "bcenter", "big") else text)
        return "\n".join(out)

    def render(self):
        b = bytearray(ESC + b"@")
        for text, style in self.lines:
            align = 1 if style in ("center", "bcenter", "big") else 0
            mode = {"bold": 0x08, "bcenter": 0x08, "big": 0x38}.get(style, 0x00)
            b += ESC + b"a" + bytes([align]) + ESC + b"!" + bytes([mode])
            b += text.encode("ascii", "ignore") + b"\n"
        b += ESC + b"!" + b"\x00" + ESC + b"a\x00" + ESC + b"d\x04"
        return bytes(b)


def _header(job, title):
    job.add("APERTURE SCIENCE", "bcenter").add("BRANCH 04 (HR)", "center").rule("=")
    job.add(title, "big").rule("=")


def build(kind, subject="", body="", items=None, record_no=None, now=None):
    now = now or datetime.now()
    job = Job()
    date = now.strftime("%Y-%m-%d %H:%M")
    if kind == "writeup":
        _header(job, "NOTICE OF INFRACTION")
        job.field("NO.", f"HR-{record_no or 1:04d}").field("TO:", "Employee")
        job.field("FROM:", "V.O.S.S. PCD-0451").field("DATE:", date).rule()
        job.add("VIOLATION:", "bold").add(subject or "Unspecified").add()
        job.add(body).add()
        job.add("Corrective action: none required. Shame is optional but encouraged.")
        job.add().add("Employee signature: __________").add()
        job.add("This notice is now part of your permanent record.", "center")
    elif kind == "commendation":
        _header(job, "COMMENDATION")
        job.add("Certificate of Adequate Performance", "bcenter").add()
        job.add("Awarded to: Employee", "center").add(date, "center").rule()
        job.add(subject, "bold").add(body).add()
        job.add("Redeemable for zero (0) vacation days.", "center")
        job.add("-- V.O.S.S., PCD-0451", "center")
    elif kind == "checklist":
        _header(job, "CHECKLIST")
        job.add("Mandatory Preparedness Checklist", "bcenter").add(date, "center").rule()
        for it in items or []:
            job.add(f"[{'X' if it.get('done') else ' '}] {it['item']}")
        if not items:
            job.add("No items. Suspiciously prepared.")
        job.rule().add("Completion is mandatory.", "center")
    else:
        _header(job, "MEMO")
        job.field("TO:", "Employee").field("FROM:", "V.O.S.S. PCD-0451")
        job.field("DATE:", date).field("RE:", subject or "General notice").rule()
        job.add(body).add()
        job.add("Please initial and return. There is no return slot.", "center")
    return job


class Printer:
    def __init__(self, body=None):
        self.body = body
        self.ser = None
        self.lock = threading.Lock()
        self.last_preview = ""
        if not config.SIM:
            import serial
            self.ser = serial.Serial(config.PRINTER_PORT, config.PRINTER_BAUD, timeout=2)

    def print_job(self, job):
        data = job.render()
        self.last_preview = job.preview()
        with self.lock:
            ctx = self.body.quiesce() if self.body else _null()
            with ctx:
                if self.ser:
                    self.ser.write(data)
                    self.ser.flush()                       # wait for UART transmit
                    time.sleep(0.5 + 0.06 * len(job.lines))  # let the head finish
                else:
                    log.info("SIM print:\n%s", self.last_preview)
        return self.last_preview


class _null:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False
