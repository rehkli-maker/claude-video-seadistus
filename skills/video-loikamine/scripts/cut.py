# /// script
# requires-python = ">=3.10"
# ///
"""Lõikab video lõikamisnimekirja (cutlist.json) järgi ja kontrollib sünkrooni.

  uv run cut.py work/cutlist.json
  uv run cut.py work/cutlist.json --input raw/video.mp4 --out work/cut.mp4

cutlist.json:
  {"source": "raw/video.mp4",
   "segments": [{"start": 0.20, "end": 5.10, "note": "sissejuhatus"}, ...]}

Lõigud pannakse kokku antud järjekorras. Lõikekohad joondatakse kaadripiirile,
et pilt ja heli ei läheks paljude lõigete peale lahku. Lõikekohtadele
lisatakse 10 ms heli sujuvus, et ei tekiks klõpse. Algset faili ei muudeta.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

FADE = 0.01


def need(tool: str) -> str:
    path = shutil.which(tool)
    if not path:
        sys.exit(f"VIGA: {tool} puudub. Käivita kursuse paigaldus (setup/install.sh või install.ps1).")
    return path


def probe(path: Path) -> dict:
    out = subprocess.run(
        [need("ffprobe"), "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    return json.loads(out)


def stream_durations(info: dict) -> tuple[float | None, float | None]:
    v = a = None
    for s in info.get("streams", []):
        d = s.get("duration")
        if d is None:
            continue
        if s["codec_type"] == "video" and v is None:
            v = float(d)
        if s["codec_type"] == "audio" and a is None:
            a = float(d)
    return v, a


def pick_encoder() -> list[str]:
    enc = subprocess.run([need("ffmpeg"), "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
    if " libx264 " in enc:
        return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p"]
    if "h264_videotoolbox" in enc:
        return ["-c:v", "h264_videotoolbox", "-b:v", "12M", "-pix_fmt", "yuv420p"]
    if "h264_mf" in enc:
        return ["-c:v", "h264_mf", "-b:v", "12M", "-pix_fmt", "yuv420p"]
    if "libopenh264" in enc:
        return ["-c:v", "libopenh264", "-b:v", "12M", "-pix_fmt", "yuv420p"]
    return ["-c:v", "mpeg4", "-q:v", "2"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cutlist", help="work/cutlist.json")
    ap.add_argument("--input", help="lähtevideo (vaikimisi cutlist.json 'source')")
    ap.add_argument("--out", help="väljund (vaikimisi cutlist.json kõrval cut.mp4)")
    args = ap.parse_args()

    cpath = Path(args.cutlist).expanduser().resolve()
    cut = json.loads(cpath.read_text(encoding="utf-8"))
    src = Path(args.input or cut.get("source") or "").expanduser()
    if not src.is_absolute():
        src = (cpath.parent / src).resolve() if (cpath.parent / src).exists() else src.resolve()
    if not src.exists():
        print(f"VIGA: lähtevideot ei leitud: {src}", file=sys.stderr)
        return 1
    out = Path(args.out).expanduser().resolve() if args.out else cpath.parent / "cut.mp4"
    if out.resolve() == src.resolve():
        print("VIGA: väljund ei tohi olla sama fail mis algne video", file=sys.stderr)
        return 1

    info = probe(src)
    vstreams = [s for s in info["streams"] if s["codec_type"] == "video"]
    astreams = [s for s in info["streams"] if s["codec_type"] == "audio"]
    if not vstreams or not astreams:
        print("VIGA: videos peab olema nii pilt kui heli", file=sys.stderr)
        return 1
    fps = Fraction(vstreams[0].get("avg_frame_rate") or vstreams[0]["r_frame_rate"])
    if fps <= 0:
        fps = Fraction(vstreams[0]["r_frame_rate"])
    src_dur = float(info["format"]["duration"])

    def snap(t: float) -> float:
        return float(round(Fraction(t).limit_denominator(100000) * fps) / fps)

    segs = []
    for s in cut["segments"]:
        a, b = snap(max(0.0, float(s["start"]))), snap(min(src_dur, float(s["end"])))
        if b - a >= 2 / float(fps):
            segs.append((a, b))
    if not segs:
        print("VIGA: cutlist.json-is pole ühtegi kasutatavat lõiku", file=sys.stderr)
        return 1

    parts, labels = [], []
    for i, (a, b) in enumerate(segs):
        d = b - a
        parts.append(f"[0:v]trim=start={a:.6f}:end={b:.6f},setpts=PTS-STARTPTS[v{i}]")
        parts.append(
            f"[0:a]atrim=start={a:.6f}:end={b:.6f},asetpts=PTS-STARTPTS,"
            f"afade=t=in:d={FADE},afade=t=out:st={max(0.0, d - FADE):.6f}:d={FADE}[a{i}]"
        )
        labels.append(f"[v{i}][a{i}]")
    parts.append(f"{''.join(labels)}concat=n={len(segs)}:v=1:a=1[v][a]")
    graph = ";".join(parts)

    expected = sum(b - a for a, b in segs)
    print(f"Lõike: {len(segs)}. Algne {src_dur:.2f} s -> uus {expected:.2f} s (fps {float(fps):.3f})")

    cmd = [
        need("ffmpeg"), "-hide_banner", "-loglevel", "error", "-stats", "-y",
        "-i", str(src), "-filter_complex", graph, "-map", "[v]", "-map", "[a]",
        *pick_encoder(), "-fps_mode", "cfr", "-r", str(fps),
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(out),
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(cmd)
    if r.returncode != 0:
        print("VIGA: ffmpeg ebaõnnestus", file=sys.stderr)
        return r.returncode

    v, a = stream_durations(probe(out))
    print(f"OK: {out}")
    print(f"Sünkroonikontroll: pilt {v:.3f} s, heli {a:.3f} s, oodatud {expected:.3f} s")
    if v is not None and a is not None and abs(v - a) > 0.1:
        print(f"HOIATUS: pilt ja heli erinevad {abs(v - a):.3f} s. Vaata lõpu sünkroon üle.")
        return 3
    print("Sünkroon korras (erinevus alla 0,1 s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
