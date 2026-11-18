# /// script
# requires-python = ">=3.10"
# ///
"""Pauside analüüs ja lõikamisnimekirja (cut list) mustand.

Loeb work/words.json ja leiab sõnade vahelised pausid.

  uv run pauses.py work/words.json
      -> work/pausid.txt (raport, pikimad eespool)

  uv run pauses.py work/words.json --make-cutlist
      -> lisaks work/cutlist.json: kogu kõne alles, pikad pausid lühendatud.
         Kordusvõtted tuleb sealt veel käsitsi (Claude'iga) välja võtta.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def fmt(t: float) -> str:
    m, s = divmod(t, 60)
    return f"{int(m):02d}:{s:05.2f}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("words", help="work/words.json")
    ap.add_argument("--threshold", type=float, default=0.6, help="paus alates (s), vaikimisi 0.6")
    ap.add_argument("--target", type=float, default=0.25, help="pausi sihtpikkus (s), vaikimisi 0.25")
    ap.add_argument("--edge", type=float, default=0.15, help="vaikus video alguses/lõpus (s)")
    ap.add_argument("--make-cutlist", action="store_true", help="kirjuta ka work/cutlist.json")
    args = ap.parse_args()

    wpath = Path(args.words).expanduser().resolve()
    data = json.loads(wpath.read_text(encoding="utf-8"))
    words = data["words"]
    if not words:
        print("VIGA: words.json-is pole ühtegi sõna", file=sys.stderr)
        return 1
    duration = float(data.get("duration") or words[-1]["end"])
    out = wpath.parent

    gaps = []
    for a, b in zip(words, words[1:]):
        g = b["start"] - a["end"]
        if g >= args.threshold:
            gaps.append({"after": a["word"], "before": b["word"], "start": a["end"], "end": b["start"], "len": g})

    lead, tail = words[0]["start"], duration - words[-1]["end"]
    saved = sum(g["len"] - args.target for g in gaps)
    saved_edges = max(0.0, lead - args.edge) + max(0.0, tail - args.edge)

    lines = [
        f"Pausiraport: {data.get('source', '')}",
        f"Video pikkus {duration:.1f} s. Pause üle {args.threshold} s: {len(gaps)}.",
        f"Lühendades need {args.target} s peale, säästad {saved:.1f} s.",
        f"Vaikus alguses {lead:.1f} s ja lõpus {tail:.1f} s, nende kärpimine säästab {saved_edges:.1f} s.",
        f"Uus pikkus umbes {duration - saved - saved_edges:.1f} s.",
        "",
        "Pikimad pausid:",
    ]
    for g in sorted(gaps, key=lambda g: -g["len"]):
        lines.append(f"  {fmt(g['start'])}  {g['len']:5.2f} s   ...{g['after']} | {g['before']}...")
    report = "\n".join(lines) + "\n"
    (out / "pausid.txt").write_text(report, encoding="utf-8")
    print(report)
    print(f"OK: {out / 'pausid.txt'}")

    if args.make_cutlist:
        half = args.target / 2
        segs = []
        cur_start = max(0.0, words[0]["start"] - args.edge)
        for g in gaps:
            segs.append({"start": round(cur_start, 3), "end": round(g["start"] + half, 3)})
            cur_start = g["end"] - half
        segs.append({"start": round(cur_start, 3), "end": round(min(duration, words[-1]["end"] + args.edge), 3)})
        cut = {
            "source": data.get("source"),
            "note": "Mustand: kogu kõne alles, pausid lühendatud. Eemalda kordusvõtted enne lõikamist.",
            "segments": segs,
        }
        (out / "cutlist.json").write_text(json.dumps(cut, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"OK: {out / 'cutlist.json'} ({len(segs)} lõiku)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
