"""Kontrollib, kas kõik koolituseks vajalik töötab.

Käivitamine repo kaustas:
  uv run --python 3.12 --no-project setup/check.py
  uv run --python 3.12 --no-project setup/check.py --online   # proovib ka YouTube'i

Iga tööriista kohta tehakse väike päris test, mitte ainult versioonikontroll.
Tulemus salvestatakse ka faili ~/.claude-video/kontroll.txt.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HOME = Path.home()
REPO = Path(__file__).resolve().parent.parent
SKILLS = HOME / ".claude" / "skills"
WIN = sys.platform == "win32"

for p in (HOME / ".pixi" / "bin", HOME / ".local" / "bin"):
    os.environ["PATH"] = str(p) + os.pathsep + os.environ.get("PATH", "")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")


def versions() -> dict:
    v = {}
    for line in (REPO / "setup" / "versions.env").read_text(encoding="utf-8").splitlines():
        m = re.match(r'^\s*([A-Z_]+)\s*=\s*"?([^"]*)"?\s*$', line)
        if m:
            v[m.group(1)] = m.group(2)
    return v


V = versions()
FIX_SCRIPT = "powershell.exe -ExecutionPolicy Bypass -File setup/install.ps1" if WIN else "bash setup/install.sh"
results: list[tuple[str, str, str, str]] = []  # (staatus, nimi, detail, lahendus)


def add(status: str, name: str, detail: str, fix: str = "") -> None:
    results.append((status, name, detail, fix))
    icon = {"ok": "OK  ", "warn": "HOIA", "fail": "VIGA"}[status]
    print(f"[{icon}] {name}: {detail}", flush=True)


def run(cmd: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    exe = shutil.which(cmd[0])
    if exe:
        cmd = [exe, *cmd[1:]]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)


def total_ram_gb() -> float:
    try:
        if WIN:
            import ctypes

            class MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong)] + [
                    (n, ctypes.c_ulonglong) for n in ("a", "b", "c", "d", "e", "f", "g")
                ]

            m = MS()
            m.dwLength = ctypes.sizeof(MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return m.a / 1024**3
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024**3
    except Exception:
        return 0.0


def check_machine() -> None:
    ram = total_ram_gb()
    free = shutil.disk_usage(HOME).free / 1024**3
    detail = f"{platform.system()} {platform.machine()}, mälu {ram:.1f} GB, vaba kettaruum {free:.1f} GB"
    model = os.environ.get("WHISPER_MODEL") or ("large-v3" if ram >= 15 else "medium" if ram >= 7 else "small")
    detail += f", Whisperi mudel {model}"
    # Kontroll käib pärast paigaldust, mil tööriistad juba võtavad oma ruumi.
    # Siin on vaja ainult ruumi videotöö jaoks.
    if free < 2:
        add("fail", "Arvuti", detail + " (videotöö jaoks liiga vähe ruumi)",
            "Vabasta kettaruumi, et vaba oleks vähemalt 5 GB.")
    elif free < 5:
        add("warn", "Arvuti", detail + " (vähe vaba ruumi, videofailid on suured)",
            "Soovitav on vähemalt 5 GB vaba ruumi.")
    elif ram and ram < 7:
        add("warn", "Arvuti", detail + " (väike mälu, eesti keeles rohkem vigu)")
    else:
        add("ok", "Arvuti", detail)


def check_bin(name: str, args: list[str], fix: str) -> str | None:
    if not shutil.which(name):
        add("fail", name, "ei leitud", fix)
        return None
    r = run([name, *args], timeout=60)
    out = (r.stdout + r.stderr).strip().splitlines()
    return out[0] if out else ""


def check_ffmpeg() -> None:
    fix = f"{FIX_SCRIPT} tools"
    first = check_bin("ffmpeg", ["-version"], fix)
    if first is None:
        return
    if check_bin("ffprobe", ["-version"], fix) is None:
        return
    enc = run(["ffmpeg", "-hide_banner", "-encoders"]).stdout
    has264 = " libx264 " in enc
    with tempfile.TemporaryDirectory() as td:
        src, cut = Path(td) / "test.mp4", Path(td) / "cut.mp4"
        r1 = run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=25:duration=3",
                  "-f", "lavfi", "-i", "sine=frequency=440:duration=3", "-shortest", str(src)])
        r2 = run(["ffmpeg", "-v", "error", "-y", "-ss", "0.5", "-i", str(src), "-t", "1.5", str(cut)])
        ok = r1.returncode == 0 and r2.returncode == 0 and cut.exists() and cut.stat().st_size > 0
    version = first.split(" Copyright")[0].replace("ffmpeg version ", "") + f" ({shutil.which('ffmpeg')})"
    if not ok:
        add("fail", "ffmpeg", f"{version}, testlõige ebaõnnestus", fix)
    elif not has264:
        add("warn", "ffmpeg", f"{version}, libx264 puudub (video kvaliteet võib olla nõrgem)", fix)
    else:
        add("ok", "ffmpeg", f"{version}, ffprobe olemas, libx264 olemas, testlõige õnnestus")


def check_node() -> None:
    fix = f"{FIX_SCRIPT} tools"
    first = check_bin("node", ["--version"], fix)
    if first is None:
        return
    m = re.match(r"v(\d+)", first)
    major = int(m.group(1)) if m else 0
    if major < 22:
        add("fail", "Node.js", f"{first}, vaja on vähemalt 22", fix)
    elif not shutil.which("npx"):
        add("fail", "Node.js", f"{first}, aga npx puudub", fix)
    else:
        add("ok", "Node.js", f"{first}, npx olemas")


def check_ytdlp(online: bool) -> None:
    fix = f"{FIX_SCRIPT} tools"
    first = check_bin("yt-dlp", ["--version"], fix)
    if first is None:
        return
    deno = check_bin("deno", ["--version"], fix)
    if deno is None:
        return
    detail = f"yt-dlp {first}, {deno.split('(')[0].strip()}"
    if not online:
        add("ok", "yt-dlp", detail + " (YouTube'i testiks lisa --online)")
        return
    r = run(["yt-dlp", "--simulate", "--no-warnings", "--print", "title",
             "https://www.youtube.com/watch?v=jNQXAC9IVRw"], timeout=120)
    if r.returncode == 0 and r.stdout.strip():
        add("ok", "yt-dlp", detail + f", YouTube'i test õnnestus ({r.stdout.strip()})")
    else:
        add("warn", "yt-dlp", detail + ", YouTube'i test ebaõnnestus. Võimalik, et võrk blokeerib YouTube'i.",
            "Proovi teises võrgus või uuenda: uv tool upgrade yt-dlp")


def check_whisper() -> None:
    fix = f"{FIX_SCRIPT} model"
    script = REPO / "setup" / "whisper.py"
    try:
        r = run(["uv", "run", "--python", V.get("PYTHON_VERSION", "3.12"), str(script), "--selftest"], timeout=360)
    except subprocess.TimeoutExpired:
        add("fail", "Whisper", "test ei lõppenud 6 minutiga",
            f"Käivita kontroll uuesti. Kui kordub, proovi väiksemat mudelit: WHISPER_MODEL=small, siis {fix}")
        return
    model = re.search(r"Mudel: (\S+)", r.stdout)
    name = model.group(1) if model else "?"
    if "pole alla laaditud" in r.stderr:
        add("fail", "Whisper", f"mudel {name} pole alla laaditud", fix)
    elif r.returncode == 0 and "Whisper töötab" in r.stdout:
        add("ok", "Whisper", f"faster-whisper, mudel {name} laetud ja töötab")
    else:
        tail = (r.stderr or r.stdout).strip().splitlines()[-1:] or ["teadmata viga"]
        add("fail", "Whisper", f"mudel {name} ei tööta: {tail[0][:160]}", fix)


def check_hyperframes() -> None:
    fix = f"{FIX_SCRIPT} skills"
    if not shutil.which("npx"):
        add("fail", "HyperFrames", "npx puudub", f"{FIX_SCRIPT} tools")
        return
    hf = f"hyperframes@{V.get('HYPERFRAMES_VERSION', 'latest')}"
    try:
        with tempfile.TemporaryDirectory() as td:
            r = subprocess.run([shutil.which("npx"), "--yes", hf, "doctor", "--json"], cwd=td,
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    except subprocess.TimeoutExpired:
        add("fail", "HyperFrames", "kontroll ei lõppenud 3 minutiga", f"Käivita kontroll uuesti. Kui kordub: {fix}")
        return
    txt = r.stdout
    try:
        data = json.loads(txt[txt.index("{"): txt.rindex("}") + 1])
    except ValueError:
        add("fail", "HyperFrames", "doctor ei andnud vastust: " + (r.stderr.strip().splitlines() or ["?"])[-1][:160], fix)
        return
    checks = {c["name"]: c for c in data.get("checks", [])}
    required = ["Node.js", "FFmpeg", "FFprobe", "Chrome"]
    bad = [n for n in required if not checks.get(n, {}).get("ok")]
    ver = data.get("_meta", {}).get("version", "?")
    if bad:
        hints = "; ".join(f"{n}: {checks.get(n, {}).get('hint') or checks.get(n, {}).get('detail', 'puudub')}" for n in bad)
        add("fail", "HyperFrames", f"versioon {ver}, probleemid: {hints}", fix)
    else:
        add("ok", "HyperFrames", f"versioon {ver}, Node, FFmpeg ja Chrome korras")


def check_skills() -> None:
    # Kursuse skillid ei tohi olla paigaldatud: koolitusel teeb osaleja need sammud ise.
    old = [d for d in ("video-transkriptsioon", "video-loikamine") if (SKILLS / d).exists()]
    if old:
        add("fail", "Vanad kursuse skillid", "alles: " + ", ".join(old) + " (need teeksid koolituse harjutused osaleja eest ära)",
            f"{FIX_SCRIPT} skills")
    hf = sorted(p.name for p in SKILLS.glob("hyperframes*") if (p / "SKILL.md").exists()) if SKILLS.exists() else []
    if hf:
        add("ok", "HyperFramesi skillid", ", ".join(hf))
    else:
        add("warn", "HyperFramesi skillid", "puuduvad (paigalduvad ka moodulis 4 käsuga npx hyperframes init)",
            f"{FIX_SCRIPT} skills")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--online", action="store_true", help="testi ka YouTube'i allalaadimist")
    ap.add_argument("--skip-slow", action="store_true", help="jäta Whisperi ja HyperFramesi test vahele")
    args = ap.parse_args()

    print("Claude AI videomonteerija: töökoha kontroll\n")
    check_machine()
    check_ffmpeg()
    check_node()
    check_ytdlp(args.online)
    check_skills()
    if not args.skip_slow:
        check_whisper()
        check_hyperframes()

    fails = [r for r in results if r[0] == "fail"]
    warns = [r for r in results if r[0] == "warn"]
    lines = ["", "=" * 60]
    if not fails:
        lines.append("KÕIK VALMIS. Töökoht on koolituseks korras.")
    else:
        lines.append(f"PUUDU ON {len(fails)} ASJA. Paranda need enne koolitust:")
        for _, name, detail, fix in fails:
            lines.append(f"  - {name}: {detail}")
            if fix:
                lines.append(f"      Lahendus: {fix}")
    if warns:
        lines.append("")
        lines.append("Märkused (koolitust ei takista):")
        for _, name, detail, fix in warns:
            lines.append(f"  - {name}: {detail}")
            if fix:
                lines.append(f"      Soovitus: {fix}")
    lines.append("=" * 60)
    summary = "\n".join(lines)
    print(summary)

    outdir = HOME / ".claude-video"
    outdir.mkdir(exist_ok=True)
    report = "\n".join(f"[{s.upper():4}] {n}: {d}" for s, n, d, _ in results) + "\n" + summary + "\n"
    (outdir / "kontroll.txt").write_text(report, encoding="utf-8")
    print(f"\nTulemus salvestatud: {outdir / 'kontroll.txt'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
