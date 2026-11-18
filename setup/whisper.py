# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "faster-whisper==1.2.1",
#   "ctranslate2==4.9.0",
#   "av==15.1.0",  # uuem av (19) ei sobi faster-whisper 1.2.1-ga; 15.1 töötab ka macOS 13-ga
# ]
# ///
"""Whisperi mudeli seadistus ja kontroll.

See skript EI transkribeeri videoid. Transkriptsiooni teeb osaleja koolitusel ise,
Claude Code'iga suheldes. Siin on ainult kaks asja:

  uv run --python 3.12 setup/whisper.py --download-only   # mudeli allalaadimine (faas model)
  uv run --python 3.12 setup/whisper.py --selftest        # kontroll, kas mudel laeb ja jookseb

Mudel valitakse arvuti mälu järgi. Teise mudeli saab valida keskkonnamuutujaga
WHISPER_MODEL (small, medium, large-v3).
"""

from __future__ import annotations

import argparse
import os
import platform
import sys
import time

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Mudel mälu järgi. Eesti keeles on large-v3 selgelt parim, medium on mõistlik kompromiss.
MODEL_BY_RAM = [(15.0, "large-v3"), (7.0, "medium"), (0.0, "small")]


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


def main() -> int:
    ap = argparse.ArgumentParser(description="Whisperi mudeli allalaadimine ja kontroll")
    ap.add_argument("--model", default="auto", help="auto, small, medium, large-v3 või HF mudeli nimi")
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="cuda ainult NVIDIA kaardiga")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--download-only", action="store_true", help="laadi mudel alla")
    group.add_argument("--selftest", action="store_true", help="kontrolli, kas mudel laeb ja jookseb")
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
        model = load_model(model_name, args.device, local_only=True)
    except Exception as e:
        print(f"VIGA: mudel {model_name} pole alla laaditud ({type(e).__name__})", file=sys.stderr)
        return 1
    print(f"Mudel laetud {time.time() - t0:.1f} s")

    import numpy as np

    audio = np.zeros(16000 * 2, dtype=np.float32)
    segs, _ = model.transcribe(audio, language="et", word_timestamps=True)
    list(segs)
    print("OK: Whisper töötab")
    return 0


if __name__ == "__main__":
    sys.exit(main())
