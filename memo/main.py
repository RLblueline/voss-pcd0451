"""M.E.M.O. main loop.

  python -m memo.main            voice mode (wake word -> STT -> Claude -> TTS)
  python -m memo.main --text     type to her instead (good for desktop testing with MEMO_SIM=1)
"""
import argparse
import logging
import queue
import signal
import threading
import time

from . import config
from .audio import Capture, Player, doa_degrees
from .body import Body
from .brain import Brain
from .lights import Lights
from .printer import Printer
from .tools import ToolBox

log = logging.getLogger("memo")


class Memo:
    def __init__(self, voice=True):
        self.events = queue.Queue()
        self.body = Body()
        self.lights = Lights()
        try:
            self.printer = Printer(self.body)
        except Exception:
            log.exception("printer unavailable")
            self.printer = None
        self.toolbox = ToolBox(self.events, self.printer)
        self.brain = Brain(self.toolbox)
        self.player = Player()
        self.voice = None
        if voice:
            try:
                from .tts import Voice
                self.voice = Voice()
            except Exception as e:
                log.warning("TTS unavailable (%s); replies will be text only", e)
        self.last_activity = time.monotonic()
        self.rested = False
        self._filed = False

    # ------------------------------------------------------------ lifecycle
    def start(self):
        self.body.start()
        self.lights.start()
        self.body.home()
        self.lights.set_mode("idle", "neutral")

    def stop(self):
        self.lights.stop()
        self.body.stop()

    # ------------------------------------------------------------ output
    def _on_tool(self, name, args):
        self.lights.pulse_aud(1.0)
        if name == "notes" and (args or {}).get("action") == "add":
            self.body.filing()
            self._filed = True

    def speak(self, mood, text):
        print(f"M.E.M.O. [{mood}]: {text}", flush=True)
        self.body.mood(mood)
        self.lights.set_mode("speak", mood)
        sfx = (["click"] if self._filed else []) + (["thunk"] if mood == "infraction" else [])
        self._filed = False
        try:
            if self.voice:
                wav = self.voice.render(text, chime=True, sfx=sfx)
                self.player.play(wav, on_level=self.lights.set_level)
        except Exception:
            log.exception("speech failed")
        finally:
            self.lights.set_mode("idle", mood if mood == "concern" else "neutral")
            if mood == "sulk":
                threading.Timer(6.0, lambda: self.events.put(("unsulk", None))).start()
            elif mood != "concern":
                self.body.home()
            self.last_activity = time.monotonic()
            self.rested = False

    def respond(self, text):
        self.lights.set_mode("think")
        self.body.think()
        mood, reply, _ = self.brain.ask(text, on_tool=self._on_tool)
        self.speak(mood, reply)

    def handle_events(self):
        while True:
            try:
                kind, data = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == "timer":
                self.speak("neutral", f"Attention, Employee. Your {data} timer has concluded. "
                                      "Please proceed to the next scheduled activity.")
            elif kind == "unsulk":
                self.body.home(0.4)
        if not self.rested and time.monotonic() - self.last_activity > config.REST_AFTER_S:
            self.body.rest()
            self.lights.set_mode("idle", "neutral")
            self.rested = True

    # ------------------------------------------------------------ voice loop
    def run_voice(self):
        from .stt import Listener, WakeWord
        wake, listener = WakeWord(), Listener()
        cap = Capture()
        cap.start()
        log.info("M.E.M.O. online. Wake word: %s", config.WAKE_MODEL)
        while not self._stopping:
            self.handle_events()
            chunk = cap.get(timeout=0.3)
            if chunk is None or not wake.detect(chunk):
                continue
            angle = doa_degrees(cap.recent(1.0))
            log.info("talker at %s deg", "?" if angle is None else f"{angle:.0f}")
            if angle is not None:
                self.body.look(angle)
            else:
                self.body.listen()
            self.lights.set_mode("listen", "neutral")
            if self.voice:
                self.player.play(self.voice.sound("chime"))
            cap.flush()
            text = listener.listen(cap)
            if text:
                self.respond(text)
            else:
                self.lights.set_mode("idle", "neutral")
                self.body.home()
            cap.flush()
            wake.reset()
            self.last_activity = time.monotonic()
        cap.stop()

    def run_text(self):
        stop = threading.Event()

        def ticker():
            while not stop.is_set():
                self.handle_events()
                time.sleep(0.2)
        threading.Thread(target=ticker, daemon=True).start()
        print("Type to M.E.M.O. (Ctrl-D to quit).")
        try:
            while True:
                line = input("Employee: ").strip()
                if line:
                    self.respond(line)
        except (EOFError, KeyboardInterrupt):
            pass
        stop.set()

    _stopping = False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", action="store_true", help="keyboard input instead of microphones")
    ap.add_argument("--mute", action="store_true", help="no TTS output")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(name)s %(levelname)s %(message)s")
    memo = Memo(voice=not args.mute)

    def _term(*_):
        memo._stopping = True
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, _term)
    memo.start()
    try:
        memo.run_text() if args.text else memo.run_voice()
    finally:
        memo.stop()


if __name__ == "__main__":
    main()
