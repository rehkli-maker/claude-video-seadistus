# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "faster-whisper==1.2.1",
#   "ctranslate2==4.9.0",
#   "av==15.1.0",  # uuem av (19) ei sobi faster-whisper 1.2.1-ga; 15.1 töötab ka macOS 13-ga
# ]
# ///
"""Transkribeerib video või heli sõnaaegadega.

Väljund (vaikimisi kausta work/ video kõrval oleva projekti juurde):
  words.json            iga sõna koos algus- ja lõpuajaga ning kindlusega
  transcript.txt        loetav tekst ajatemplitega lõikude kaupa
  kahtlased-sonad.txt   sõnad, milles Whisper pole kindel (nimed, terminid, võõrsõnad)

Algset faili ei muudeta.

Käivitamine:
  uv run transcribe.py raw/minu-video.mp4
  uv run transcribe.py raw/minu-video.mp4 --model medium --prompt "Tartu Ülikool, Claude"
  uv run transcribe.py --download-only      # ainult mudeli allalaadimine
  uv run transcribe.py --selftest           # kontroll, kas mudel laeb ja jookseb
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Mudel mälu järgi. Eesti keeles on large-v3 selgelt parim, medium on mõistlik kompromiss.
MODEL_BY_RAM = [(15.0, "large-v3"), (7.0, "medium"), (0.0, "small")]
UNCERTAIN_BELOW = 0.6


def total_ram_gb() -> float:
    try:
        if sys.platform == "win32":
            import ctypes

            class MS(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            m = MS()
            m.dwLength = ctypes.sizeof(MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return m.ullTotalPhys / 1024**3
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024**3
    except Exception:
        return 8.0


def pick_model(requested: str | None) -> str:
    if requested and requested != "auto":
        return requested
    env = os.environ.get("WHISPER_MODEL")
    if env:
        return env
    ram = total_ram_gb()
    for limit, name in MODEL_BY_RAM:
        if ram >= limit:
            return name
    return "small"


def load_model(name: str, device: str, local_only: bool = False):
    from faster_whisper import WhisperModel

    compute = "float16" if device == "cuda" else "int8"
    threads = max(1, (os.cpu_count() or 4))
    return WhisperModel(name, device=device, compute_type=compute, cpu_threads=threads,
                        local_files_only=local_only)


def fmt_ts(t: float) -> str:
    m, s = divmod(t, 60)
    return f"{int(m):02d}:{s:05.2f}"


def main() -> int:
    ap = argparse.ArgumentParser(description="Transkriptsioon sõnaaegadega (faster-whisper)")
    ap.add_argument("input", nargs="?", help="video- või helifail")
    ap.add_argument("--out-dir", help="väljundkaust (vaikimisi: <projekt>/work)")
    ap.add_argument("--model", default="auto", help="auto, small, medium, large-v3 või HF mudeli nimi")
    ap.add_argument("--language", default="et", help="keelekood, vaikimisi et")
    ap.add_argument("--prompt", default=None, help="nimed ja terminid, mis aitavad õigesti tuvastada")
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="cuda ainult NVIDIA kaardiga")
    ap.add_argument("--download-only", action="store_true", help="laadi ainult mudel alla")
    ap.add_argument("--selftest", action="store_true", help="kontrolli, kas mudel laeb ja jookseb")
    args = ap.parse_args()

    model_name = pick_model(args.model)
    print(f"Arvuti: {platform.system()} {platform.machine()}, mälu {total_ram_gb():.1f} GB")
    print(f"Mudel: {model_name} ({args.device})")

    if args.download_only:
        from faster_whisper.utils import download_model

        t0 = time.time()
        path = download_model(model_name)
        print(f"OK: mudel {model_name} on olemas ({time.time() - t0:.0f} s): {path}")
        return 0

    t0 = time.time()
    try:
        # Kontroll ei tohi mudelit alla laadida: see võtaks liiga kaua ja kontroll katkeks.
        model = load_model(model_name, args.device, local_only=args.selftest)
    except Exception as e:
        if not args.selftest:
            raise
        print(f"VIGA: mudel {model_name} pole alla laaditud ({type(e).__name__})", file=sys.stderr)
        return 1
    print(f"Mudel laetud {time.time() - t0:.1f} s")

    if args.selftest:
        import numpy as np

        audio = np.zeros(16000 * 2, dtype=np.float32)
        segs, _ = model.transcribe(audio, language=args.language, word_timestamps=True)
        list(segs)
        print("OK: Whisper töötab")
        return 0

    if not args.input:
        ap.error("anna sisendfail või kasuta --download-only / --selftest")
    src = Path(args.input).expanduser().resolve()
    if not src.exists():
        print(f"VIGA: faili ei leitud: {src}", file=sys.stderr)
        return 1

    if args.out_dir:
        out = Path(args.out_dir).expanduser().resolve()
    else:
        project = src.parent.parent if src.parent.name.lower() in ("raw", "toores", "toormaterjal") else src.parent
        out = project / "work"
    out.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    segments, info = model.transcribe(
        str(src),
        language=args.language,
        word_timestamps=True,
        vad_filter=False,  # pausid peavad alles jääma, neid analüüsitakse hiljem
        beam_size=5,
        initial_prompt=args.prompt,
        condition_on_previous_text=False,
    )

    words, segs = [], []
    for seg in segments:
        segs.append({"id": seg.id, "start": round(seg.start, 3), "end": round(seg.end, 3), "text": seg.text.strip()})
        for w in seg.words or []:
            words.append({
                "i": len(words),
                "word": w.word.strip(),
                "start": round(w.start, 3),
                "end": round(w.end, 3),
                "prob": round(w.probability, 3),
                "segment": seg.id,
            })
        print(f"  [{fmt_ts(seg.start)}] {seg.text.strip()}", flush=True)

    elapsed = time.time() - t0
    data = {
        "source": str(src),
        "model": model_name,
        "language": info.language,
        "duration": round(info.duration, 3),
        "transcribe_seconds": round(elapsed, 1),
        "segments": segs,
        "words": words,
    }
    (out / "words.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    lines = [f"[{fmt_ts(s['start'])} - {fmt_ts(s['end'])}] {s['text']}" for s in segs]
    (out / "transcript.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    unsure = []
    for w in words:
        if w["prob"] < UNCERTAIN_BELOW:
            ctx = " ".join(x["word"] for x in words[max(0, w["i"] - 4): w["i"] + 5])
            unsure.append(f"{fmt_ts(w['start'])}  {w['word']:<20} kindlus {w['prob']:.2f}   ...{ctx}...")
    header = f"Sõnad, mille kindlus on alla {UNCERTAIN_BELOW} ({len(unsure)} tk). Kontrolli need üle.\n\n"
    (out / "kahtlased-sonad.txt").write_text(header + "\n".join(unsure) + "\n", encoding="utf-8")

    print()
    print(f"OK: {len(words)} sõna, {len(segs)} lõiku, video {info.duration:.1f} s, töö {elapsed:.0f} s")
    print(f"    {out / 'words.json'}")
    print(f"    {out / 'transcript.txt'}")
    print(f"    {out / 'kahtlased-sonad.txt'}  ({len(unsure)} kahtlast sõna)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
