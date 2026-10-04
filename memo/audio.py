"""Stereo I2S capture, playback with level envelope, and GCC-PHAT direction of arrival.

Channel 0 = left mic (L/R -> GND) at -X, channel 1 = right mic (L/R -> 3.3 V) at +X.
"""
import collections
import logging
import queue
import shutil
import subprocess
import threading
import time
import wave

import numpy as np

from . import config

log = logging.getLogger("memo.audio")


# ------------------------------------------------------------------ helpers
def to_mono(stereo):
    """(n, 2) int16 -> (n,) int16."""
    return ((stereo[:, 0].astype(np.int32) + stereo[:, 1]) // 2).astype(np.int16)


def rms(x):
    x = np.asarray(x, dtype=np.float64)
    return float(np.sqrt(np.mean(x * x))) if x.size else 0.0


class Decimator3:
    """48 kHz -> 16 kHz windowed-sinc FIR decimator with state, per channel."""

    def __init__(self, channels=2, taps=63):
        n = np.arange(taps) - (taps - 1) / 2
        cutoff = 7000.0 / 48000.0
        h = 2 * cutoff * np.sinc(2 * cutoff * n) * np.hamming(taps)
        self.h = (h / h.sum()).astype(np.float64)
        self.tail = np.zeros((taps - 1, channels))
        self.phase = 0

    def process(self, block):
        x = np.vstack([self.tail, block.astype(np.float64)])
        self.tail = x[-(len(self.h) - 1):]
        y = np.stack([np.convolve(x[:, c], self.h, mode="valid") for c in range(x.shape[1])], axis=1)
        out = y[self.phase::3]
        self.phase = (self.phase - len(y)) % 3
        return np.clip(out, -32768, 32767).astype(np.int16)


# ------------------------------------------------------------------ capture
class Capture:
    """Runs arecord in a thread; yields (CHUNK, 2) int16 blocks at 16 kHz."""

    def __init__(self):
        self.q = queue.Queue(maxsize=64)
        self.ring = collections.deque(maxlen=int(2.0 * config.RATE / config.CHUNK))
        self._stop = threading.Event()
        self._proc = None
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._run, name="capture", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._proc:
            self._proc.terminate()

    def _run(self):
        if config.SIM:
            silence = np.zeros((config.CHUNK, 2), np.int16)
            while not self._stop.is_set():
                time.sleep(config.CHUNK / config.RATE)
                self._push(silence)
            return
        rate = config.CAPTURE_RATE
        ratio = rate // config.RATE
        dec = Decimator3() if ratio == 3 else None
        if ratio not in (1, 3):
            raise ValueError("MEMO_CAPTURE_RATE must be 16000 or 48000")
        cmd = ["arecord", "-q", "-D", config.ALSA_CAPTURE, "-c", "2", "-r", str(rate),
               "-f", "S16_LE", "-t", "raw"]
        nbytes = config.CHUNK * ratio * 2 * 2
        while not self._stop.is_set():
            log.info("starting capture: %s", " ".join(cmd))
            self._proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            while not self._stop.is_set():
                buf = self._proc.stdout.read(nbytes)
                if len(buf) < nbytes:
                    log.warning("capture stream ended; restarting")
                    break
                block = np.frombuffer(buf, np.int16).reshape(-1, 2)
                if dec:
                    block = dec.process(block)
                block = np.clip(block.astype(np.float32) * config.MIC_GAIN, -32768, 32767).astype(np.int16)
                self._push(block)
            self._proc.kill()
            time.sleep(1.0)

    def _push(self, block):
        self.ring.append(block)
        try:
            self.q.put_nowait(block)
        except queue.Full:
            try:
                self.q.get_nowait()
            except queue.Empty:
                pass
            self.q.put_nowait(block)

    def get(self, timeout=0.5):
        try:
            return self.q.get(timeout=timeout)
        except queue.Empty:
            return None

    def flush(self):
        while True:
            try:
                self.q.get_nowait()
            except queue.Empty:
                return

    def recent(self, seconds):
        blocks = list(self.ring)[-max(1, int(seconds * config.RATE / config.CHUNK)):]
        return np.vstack(blocks) if blocks else np.zeros((0, 2), np.int16)


# ------------------------------------------------------------------ direction of arrival
def gcc_phat(sig, ref, fs, max_tau=None, interp=16):
    """Delay (s) of `sig` relative to `ref`. Positive = sig arrives later."""
    sig = np.asarray(sig, np.float64)
    ref = np.asarray(ref, np.float64)
    n = sig.size + ref.size
    R = np.fft.rfft(sig, n) * np.conj(np.fft.rfft(ref, n))
    cc = np.fft.irfft(R / (np.abs(R) + 1e-12), n=interp * n)
    max_shift = interp * n // 2
    if max_tau is not None:
        max_shift = min(int(interp * fs * max_tau) + 1, max_shift)
    cc = np.concatenate((cc[-max_shift:], cc[:max_shift + 1]))
    shift = int(np.argmax(np.abs(cc))) - max_shift
    return shift / float(interp * fs)


def doa_degrees(stereo, fs=config.RATE):
    """Angle of the talker from straight out, positive toward +X. None if too quiet."""
    if stereo.shape[0] < 256 or rms(stereo) < config.DOA_MIN_RMS:
        return None
    d, c = config.MIC_SPACING_M, config.SPEED_OF_SOUND
    tau = gcc_phat(stereo[:, 1], stereo[:, 0], fs, max_tau=d / c)
    s = np.clip(-tau * c / d, -1.0, 1.0)   # right mic later -> source on -X side
    ang = float(np.degrees(np.arcsin(s)))
    return float(np.clip(ang, -config.DOA_MAX_DEG, config.DOA_MAX_DEG))


# ------------------------------------------------------------------ playback
def wav_envelope(path, frame_s=0.02):
    with wave.open(str(path), "rb") as w:
        rate, ch, width = w.getframerate(), w.getnchannels(), w.getsampwidth()
        data = np.frombuffer(w.readframes(w.getnframes()), np.int16 if width == 2 else np.uint8)
    if ch > 1:
        data = data.reshape(-1, ch).mean(axis=1)
    hop = max(1, int(rate * frame_s))
    env = np.array([rms(data[i:i + hop]) for i in range(0, len(data), hop)])
    peak = np.percentile(env, 95) if env.size else 1.0
    return np.clip(env / (peak + 1e-9), 0, 1), len(data) / float(rate)


class Player:
    def play(self, path, on_level=None, frame_s=0.02):
        env, duration = wav_envelope(path, frame_s)
        proc = None
        if not config.SIM and shutil.which("aplay"):
            proc = subprocess.Popen(["aplay", "-q", "-D", config.ALSA_PLAYBACK, str(path)])
        t0 = time.monotonic()
        while True:
            t = time.monotonic() - t0
            if proc is not None and proc.poll() is not None:
                break
            if proc is None and t >= duration:
                break
            i = int(t / frame_s)
            if on_level:
                on_level(float(env[i]) if i < len(env) else 0.0)
            time.sleep(frame_s)
        if on_level:
            on_level(0.0)
