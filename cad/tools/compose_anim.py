"""Caption the rendered frames and build docs/img/voss_routine.mp4 and .gif."""
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SRC = Path("/tmp/voss_anim")
DST = Path(__file__).resolve().parents[2] / "docs" / "img"
FPS = 6
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 20)
small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)

frames = sorted(SRC.glob("f*.png"))
tmp = SRC / "cap"
tmp.mkdir(exist_ok=True)
gif = []
for i, f in enumerate(frames):
    im = Image.open(f).convert("RGB")
    d = ImageDraw.Draw(im)
    cap = (SRC / (f.stem + ".txt")).read_text()
    d.rectangle([0, 0, im.width, 34], fill=(30, 30, 32))
    d.text((12, 6), "V.O.S.S. // PCD-0451", font=font, fill=(255, 176, 70))
    d.rectangle([0, im.height - 34, im.width, im.height], fill=(30, 30, 32))
    d.text((12, im.height - 27), cap, font=small, fill=(235, 235, 230))
    im.save(tmp / f"c{i:04d}.png")
    gif.append(im.resize((400, 450)).quantize(colors=128, method=Image.Quantize.MEDIANCUT))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(tmp / "c%04d.png"),
                "-vf", "minterpolate=fps=24:mi_mode=blend", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                str(DST / "voss_routine.mp4")], check=True)
gif[0].save(DST / "voss_routine.gif", save_all=True, append_images=gif[1:], duration=int(1000 / FPS), loop=0, optimize=True)
print("wrote", DST / "voss_routine.mp4", DST / "voss_routine.gif")
