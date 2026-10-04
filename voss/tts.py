"""Piper TTS -> sox intercom filter -> chime/sfx concatenation. All audio is 16 kHz mono s16."""
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import config

log = logging.getLogger("voss.tts")

FMT = ["-r", "16000", "-c", "1", "-b", "16"]


def intercom_cmd(src, dst):
    """sox chain: telephone band, a little grit, compression, small-room slap."""
    return ["sox", str(src), *FMT, str(dst),
            "highpass", "350", "lowpass", "3200",
            "overdrive", "6", "12",
            "compand", "0.01,0.15", "-70,-70,-40,-20,0,-6", "-4", "-90", "0.05",
            "echo", "0.8", "0.7", "18", "0.15",
            "gain", "-n", "-1",
            "pad", "0", "0.15"]


def _sox(*args):
    subprocess.run(["sox", *map(str, args)], check=True, capture_output=True)


def make_sfx(outdir):
    """Generate the chime, thunk and relay-click sounds once."""
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    chime, thunk, click = out / "chime.wav", out / "thunk.wav", out / "click.wav"
    if not chime.exists():
        a, b = out / "_a.wav", out / "_b.wav"
        _sox("-n", *FMT, a, "synth", "0.11", "sine", "1318.5", "fade", "q", "0.005", "0.11", "0.03", "gain", "-9")
        _sox("-n", *FMT, b, "synth", "0.22", "sine", "987.8", "fade", "q", "0.005", "0.22", "0.12", "gain", "-9")
        _sox(a, b, chime, "pad", "0", "0.08")
        a.unlink(); b.unlink()
    if not thunk.exists():
        a, b = out / "_a.wav", out / "_b.wav"
        _sox("-n", *FMT, a, "synth", "0.22", "sine", "70-40", "fade", "q", "0.002", "0.22", "0.18")
        _sox("-n", *FMT, b, "synth", "0.08", "brownnoise", "fade", "q", "0.001", "0.08", "0.07")
        _sox("-m", a, b, thunk, "gain", "-n", "-2", "pad", "0", "0.12")
        a.unlink(); b.unlink()
    if not click.exists():
        _sox("-n", *FMT, click, "synth", "0.012", "whitenoise", "fade", "q", "0", "0.012", "0.01",
             "gain", "-8", "pad", "0", "0.06")
    return {"chime": chime, "thunk": thunk, "click": click}


class Voice:
    def __init__(self):
        if not shutil.which("sox"):
            raise RuntimeError("sox not installed")
        self.tmp = Path(tempfile.gettempdir()) / "voss"
        self.tmp.mkdir(exist_ok=True)
        self.sfx = make_sfx(config.DATA_DIR / "sfx")

    def _piper(self, text, dst):
        if not shutil.which(config.PIPER_BIN):
            raise RuntimeError("piper not found")
        subprocess.run([config.PIPER_BIN, "-m", str(config.PIPER_MODEL), "-f", str(dst)],
                       input=text.encode(), check=True, capture_output=True)

    def render(self, text, chime=True, sfx=None):
        """Return a WAV path: [chime] [sfx...] voice."""
        raw, fx, out = self.tmp / "raw.wav", self.tmp / "fx.wav", self.tmp / "out.wav"
        self._piper(text, raw)
        if config.INTERCOM_FX:
            subprocess.run(intercom_cmd(raw, fx), check=True, capture_output=True)
        else:
            _sox(raw, *FMT, fx)
        parts = ([self.sfx["chime"]] if chime else []) + [self.sfx[s] for s in (sfx or [])] + [fx]
        _sox(*parts, out) if len(parts) > 1 else _sox(fx, out)
        return out

    def sound(self, name):
        return self.sfx[name]
