"""Offline tests (no hardware, no API). Run:  MEMO_SIM=1 python -m unittest discover tests"""
import json
import os
import queue
import shutil
import sys
import tempfile
import time
import unittest
import wave
from pathlib import Path
from types import SimpleNamespace as NS

TMP = tempfile.mkdtemp()
os.environ["MEMO_SIM"] = "1"
os.environ["MEMO_DATA"] = TMP
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from memo import audio, body, config, lights, persona, printer, tools  # noqa: E402
from memo.brain import Brain  # noqa: E402


class TestPersona(unittest.TestCase):
    def test_tags(self):
        self.assertEqual(persona.parse_mood("[infraction] Late again."), ("infraction", "Late again."))
        self.assertEqual(persona.parse_mood("  [ Approve ]  Nice **work**."), ("approve", "Nice work."))
        self.assertEqual(persona.parse_mood("No tag here."), ("neutral", "No tag here."))
        self.assertEqual(persona.parse_mood("[bogus] Hi"), ("neutral", "[bogus] Hi"))
        self.assertEqual(persona.parse_mood("[sulk] Fine. [sulk]"), ("sulk", "Fine."))

    def test_prompt(self):
        self.assertIn("PCD-0451", persona.system_prompt())


class FakeClient:
    """First call asks for set_timer, second returns the final text."""

    def __init__(self):
        self.calls = []
        self.messages = self

    def create(self, **kw):
        self.calls.append(kw)
        if len(self.calls) == 1:
            return NS(stop_reason="tool_use", content=[
                NS(type="text", text="One moment."),
                NS(type="tool_use", id="tu_1", name="set_timer", input={"seconds": 600, "label": "pasta"})])
        return NS(stop_reason="end_turn", content=[NS(type="text", text="[approve] Pasta timer filed, Employee.")])


class TestBrain(unittest.TestCase):
    def test_tool_loop(self):
        tb = tools.ToolBox(queue.Queue())
        client = FakeClient()
        brain = Brain(tb, client=client)
        seen = []
        mood, text, used = brain.ask("set a pasta timer for ten minutes", on_tool=lambda n, a: seen.append(n))
        self.assertEqual((mood, text), ("approve", "Pasta timer filed, Employee."))
        self.assertEqual(used, ["set_timer"])
        self.assertEqual(seen, ["set_timer"])
        self.assertEqual(json.loads(tb.dispatch("list_timers", {}))["timers"][0]["label"], "pasta")
        second = client.calls[1]["messages"]
        self.assertEqual(second[-1]["content"][0]["type"], "tool_result")
        self.assertEqual(second[-2]["content"][1]["type"], "tool_use")
        self.assertEqual(len(brain.history), 2)
        tb.dispatch("cancel_timer", {"label": "all"})

    def test_history_cap(self):
        brain = Brain(tools.ToolBox(queue.Queue()), client=FakeClient())
        for i in range(20):
            brain._remember(f"u{i}", f"a{i}")
        self.assertEqual(len(brain.history), 2 * config.HISTORY_TURNS)
        self.assertEqual(brain.history[0]["role"], "user")

    def test_api_failure(self):
        class Boom:
            messages = None

            def __init__(self):
                self.messages = self

            def create(self, **kw):
                raise RuntimeError("offline")
        mood, text, _ = Brain(tools.ToolBox(queue.Queue()), client=Boom()).ask("hi")
        self.assertIn("head office", text)


class TestTools(unittest.TestCase):
    def setUp(self):
        self.tb = tools.ToolBox(queue.Queue(), printer=printer.Printer())

    def test_checklist_and_notes(self):
        d = lambda n, a: json.loads(self.tb.dispatch(n, a))
        d("checklist", {"action": "add", "item": "Batteries"})
        d("checklist", {"action": "check", "item": "batteries"})
        self.assertTrue(d("checklist", {"action": "list"})["items"][0]["done"])
        r = d("notes", {"action": "add", "text": "Ate the last donut"})
        self.assertTrue(r["ok"])
        self.assertEqual(len(d("notes", {"action": "search", "text": "donut"})["notes"]), 1)
        self.assertTrue(d("print_memo", {"kind": "checklist"})["ok"])
        self.assertIn("[X] Batteries", self.tb.printer.last_preview)

    def test_timer_fires(self):
        self.tb.t_set_timer(1, "tea")
        self.assertEqual(self.tb.events.get(timeout=3), ("timer", "tea"))

    def test_weather_fake_http(self):
        def http(url):
            if "geocoding" in url:
                return {"results": [{"latitude": 1, "longitude": 2, "name": "Testville"}]}
            return {"current": {"temperature_2m": 70, "apparent_temperature": 69, "weather_code": 2,
                                "wind_speed_10m": 5},
                    "daily": {"time": ["a", "b"], "temperature_2m_max": [75, 77],
                              "temperature_2m_min": [60, 61], "precipitation_probability_max": [10, 40],
                              "weather_code": [3, 61]}}
        self.tb.http = http
        w = json.loads(self.tb.dispatch("get_weather", {"place": "Testville"}))
        self.assertEqual(w["now"]["conditions"], "partly cloudy")
        self.assertEqual(w["tomorrow"]["conditions"], "light rain")

    def test_unknown_tool(self):
        self.assertIn("error", json.loads(self.tb.dispatch("nope", {})))


class TestPrinter(unittest.TestCase):
    def test_formats(self):
        for kind in ("memo", "writeup", "commendation", "checklist"):
            job = printer.build(kind, "Subject \u2014 test", "Body with \u201cquotes\u201d " * 6,
                                items=[{"item": "Water", "done": False}], record_no=7)
            for text, style in job.lines:
                width = config.PRINTER_COLS // 2 if style == "big" else config.PRINTER_COLS
                self.assertLessEqual(len(text), width)
            job.render().decode("ascii")


class TestDOA(unittest.TestCase):
    def _stereo(self, delay_samples):
        rng = np.random.default_rng(0)
        x = rng.normal(0, 3000, 16000 + 20)
        d = 10
        right = x[d:d + 16000]                          # ch1
        left = x[d - delay_samples:d - delay_samples + 16000]  # ch0 delayed copy when delay > 0
        return np.stack([left, right], axis=1).astype(np.int16)

    def test_sides(self):
        self.assertAlmostEqual(audio.doa_degrees(self._stereo(0)), 0.0, delta=3)
        pos = audio.doa_degrees(self._stereo(2))       # left mic hears it later -> source at +X
        neg = audio.doa_degrees(self._stereo(-2))
        expected = np.degrees(np.arcsin(2 / 16000 * 343 / 0.08))
        self.assertAlmostEqual(pos, expected, delta=4)
        self.assertAlmostEqual(neg, -expected, delta=4)

    def test_quiet(self):
        self.assertIsNone(audio.doa_degrees(np.zeros((16000, 2), np.int16)))

    def test_decimator(self):
        t = np.arange(48000) / 48000
        x = (10000 * np.sin(2 * np.pi * 440 * t)).astype(np.int16)
        dec = audio.Decimator3()
        out = np.vstack([dec.process(np.stack([x[i:i + 3840]] * 2, 1)) for i in range(0, 48000, 3840)])
        self.assertEqual(out.shape, (16000, 2))
        spec = np.abs(np.fft.rfft(out[2000:, 0]))
        freq = np.argmax(spec) * 16000 / len(out[2000:, 0])
        self.assertAlmostEqual(freq, 440, delta=3)


class TestWorkspace(unittest.TestCase):
    def test_presets(self):
        for p in (body.HOME, body.SULK, body.ZERO, body.REST):
            self.assertTrue(body.workspace_ok(p), p)
        for a in range(-60, 61, 10):
            self.assertTrue(body.workspace_ok(dict(body.HOME, **body.look_pose(a))), a)
        stamp = dict(body.HOME, shoulder=-5.0, elbow=5.0, pitch=15.0)
        self.assertTrue(body.workspace_ok(stamp))

    def test_rejects(self):
        self.assertFalse(body.workspace_ok(dict(body.HOME, yaw=180)))                 # yaw limit
        self.assertFalse(body.workspace_ok(dict(body.HOME, shoulder=75, elbow=0)))    # tilt servo out of range
        self.assertFalse(body.workspace_ok(dict(body.HOME, yaw=5, shoulder=75, elbow=-75)))  # head into housing

    def test_level_head(self):
        self.assertEqual(body.tilt_of(body.HOME), 0.0)
        p = body.clamp_pose(dict(body.HOME, shoulder=60, elbow=0, pitch=0))
        self.assertLessEqual(body.tilt_of(p), config.LIMITS["tilt"][1])

    def test_stamp_drop(self):
        _, (_, _, z_hi) = body.fk(90, 15, -15)
        _, (_, _, z_lo) = body.fk(90, -5, 5)
        self.assertGreater(z_hi - z_lo, 40)                                          # ~2 in drop

    def test_pulse_mapping(self):
        cal = body.load_calibration()
        self.assertAlmostEqual(body.joint_to_us(cal, "yaw", 90), 1500)
        self.assertAlmostEqual(body.joint_to_us(cal, "shoulder", 0), 1500)
        self.assertAlmostEqual(body.joint_to_us(cal, "tilt", 0), 1500)
        self.assertLess(body.joint_to_us(cal, "shutter", 0), body.joint_to_us(cal, "shutter", 1))

    def test_motion_and_quiesce(self):
        b = body.Body()
        b.start()
        b.move({"pitch": 20, "shutter": 0.5}, speed=4)
        with b.quiesce():
            self.assertFalse(b.moving)
            self.assertTrue(b.out.enabled)                                           # arm keeps holding
            self.assertAlmostEqual(b.current["pitch"], 20, delta=0.01)
        b.move({"yaw": 5, "shoulder": 75, "elbow": -75})                             # invalid -> arm ignored
        b.wait(5)
        self.assertEqual((b.current["yaw"], b.current["shoulder"]), (90, 20))
        b.rest()
        b.wait(8)
        time.sleep(0.1)
        self.assertTrue(b.out.enabled)
        self.assertEqual(b.out.released, set(body.RELEASABLE))
        b.move({"pitch": 5})
        b.wait(5)
        self.assertFalse(b.out.released)
        b.stop()
        self.assertFalse(b.out.enabled)


class TestLights(unittest.TestCase):
    def test_encode(self):
        data = lights.encode([(255, 0, 0)] * config.LED_COUNT)
        self.assertEqual(len(data), 48 + 9 * config.LED_COUNT)
        self.assertEqual(lights._LUT[0], bytes([0b10010010, 0b01001001, 0b00100100]))

    def test_frames(self):
        L = lights.Lights()
        for mode in ("idle", "listen", "think", "speak", "off"):
            for mood in persona.MOODS:
                L.set_mode(mode, mood)
                f = L.frame(1.23)
                self.assertEqual(len(f), config.LED_COUNT)
        L.set_mode("off")
        self.assertTrue(all(p == (0, 0, 0) for p in L.frame(5.0)))


@unittest.skipUnless(shutil.which("sox"), "sox not installed")
class TestSox(unittest.TestCase):
    def test_chain_and_sfx(self):
        from memo import tts
        sfx = tts.make_sfx(Path(TMP) / "sfx")
        src = Path(TMP) / "src.wav"
        tts._sox("-n", *tts.FMT, src, "synth", "1.0", "sine", "300")
        dst = Path(TMP) / "dst.wav"
        import subprocess
        subprocess.run(tts.intercom_cmd(src, dst), check=True, capture_output=True)
        out = Path(TMP) / "all.wav"
        tts._sox(sfx["chime"], sfx["thunk"], sfx["click"], dst, out)
        with wave.open(str(out)) as w:
            self.assertEqual((w.getframerate(), w.getnchannels()), (16000, 1))
            self.assertGreater(w.getnframes(), 16000)
        env, dur = audio.wav_envelope(out)
        self.assertGreater(dur, 1.0)
        self.assertLessEqual(env.max(), 1.0)


if __name__ == "__main__":
    unittest.main()
