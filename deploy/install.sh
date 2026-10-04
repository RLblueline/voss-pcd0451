#!/usr/bin/env bash
# M.E.M.O. installer for Raspberry Pi OS Lite (Bookworm, 64-bit) on a Pi Zero 2 W.
# Run from the unpacked project folder:  sudo ./deploy/install.sh
set -euo pipefail
SRC="$(cd "$(dirname "$0")/.." && pwd)"
DEST=/opt/memo
PIPER_URL=https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_aarch64.tar.gz
VOICE_URL=https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/low
VOSK_URL=https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip

apt-get update
apt-get install -y python3-venv python3-dev sox alsa-utils unzip curl i2c-tools python3-gpiozero python3-lgpio

# Serial port for the printer, not a login console
raspi-config nonint do_serial_cons 1 || true
raspi-config nonint do_serial_hw 0 || true

if ! grep -q googlevoicehat-soundcard /boot/firmware/config.txt; then
  cat "$SRC/deploy/config.txt.snippet" >> /boot/firmware/config.txt
  echo ">> config.txt updated; reboot after install"
fi

id memo >/dev/null 2>&1 || useradd --system --home "$DEST" --shell /usr/sbin/nologin memo
mkdir -p "$DEST/models" "$DEST/data"
cp -r "$SRC/memo" "$SRC/tests" "$SRC/requirements.txt" "$DEST/"

python3 -m venv --system-site-packages "$DEST/venv"
"$DEST/venv/bin/pip" install --upgrade pip
"$DEST/venv/bin/pip" install -r "$DEST/requirements.txt"
"$DEST/venv/bin/python" -c "import openwakeword.utils as u; u.download_models()"

cd "$DEST/models"
[ -x piper/piper ] || curl -L "$PIPER_URL" | tar xz
[ -f en_US-amy-low.onnx ] || { curl -LO "$VOICE_URL/en_US-amy-low.onnx"; curl -LO "$VOICE_URL/en_US-amy-low.onnx.json"; }
if [ ! -d vosk-model-small-en-us-0.15 ]; then curl -LO "$VOSK_URL"; unzip -q vosk-model-small-en-us-0.15.zip; rm vosk-model-small-en-us-0.15.zip; fi
ln -sf "$DEST/models/piper/piper" /usr/local/bin/piper

[ -f /etc/memo.env ] || { install -m 600 "$SRC/deploy/memo.env.example" /etc/memo.env; echo ">> edit /etc/memo.env (API key, lat/lon)"; }
chown -R memo:memo "$DEST"
install -m 644 "$SRC/deploy/memo.service" /etc/systemd/system/memo.service
systemctl daemon-reload
systemctl enable memo
echo ">> done. Calibrate first:  cd $DEST && sudo -u memo venv/bin/python -m memo.calibrate zero"
echo ">> then:  sudo systemctl start memo ; journalctl -u memo -f"
