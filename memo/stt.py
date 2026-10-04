"""Local wake word (openWakeWord) and streaming speech-to-text (webrtcvad + Vosk)."""
import json
import logging
import time


from . import config
from .audio import to_mono

log = logging.getLogger("memo.stt")


class WakeWord:
    def __init__(self):
        from openwakeword.model import Model
        self.model = Model(wakeword_models=[config.WAKE_MODEL], inference_framework="onnx")
        self._last = 0.0

    def detect(self, stereo_chunk):
        scores = self.model.predict(to_mono(stereo_chunk))
        score = max(scores.values()) if scores else 0.0
        now = time.monotonic()
        if score >= config.WAKE_THRESHOLD and now - self._last > config.WAKE_COOLDOWN_S:
            self._last = now
            log.info("wake word (score %.2f)", score)
            return True
        return False

    def reset(self):
        self.model.reset()


class Listener:
    """Records one utterance after the wake word and returns its transcript."""

    FRAME = 320  # 20 ms at 16 kHz

    def __init__(self):
        import vosk
        import webrtcvad
        vosk.SetLogLevel(-1)
        self.model = vosk.Model(str(config.VOSK_MODEL))
        self.vad = webrtcvad.Vad(config.VAD_AGGRESSIVENESS)
        self._vosk = vosk

    def listen(self, capture):
        rec = self._vosk.KaldiRecognizer(self.model, config.RATE)
        started = False
        silent_frames = 0
        end_frames = config.SILENCE_END_MS // 20
        t0 = time.monotonic()
        speech_t0 = None
        while True:
            chunk = capture.get(timeout=1.0)
            now = time.monotonic()
            if chunk is None:
                if now - t0 > config.NO_SPEECH_TIMEOUT_S:
                    break
                continue
            mono = to_mono(chunk)
            rec.AcceptWaveform(mono.tobytes())
            for i in range(0, len(mono) - self.FRAME + 1, self.FRAME):
                voiced = self.vad.is_speech(mono[i:i + self.FRAME].tobytes(), config.RATE)
                if voiced:
                    if not started:
                        started, speech_t0 = True, now
                    silent_frames = 0
                elif started:
                    silent_frames += 1
            if started and silent_frames >= end_frames:
                break
            if not started and now - t0 > config.NO_SPEECH_TIMEOUT_S:
                break
            if started and now - speech_t0 > config.MAX_UTTERANCE_S:
                break
        text = json.loads(rec.FinalResult()).get("text", "").strip()
        log.info("heard: %r", text)
        return text
