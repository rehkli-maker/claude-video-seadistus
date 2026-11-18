#!/usr/bin/env bash
# Claude AI videomonteerija: tööriistade paigaldus (macOS ja Linux)
#
# Admin-õigusi ega Homebrew'd pole vaja. Kõik läheb kasutaja kodukausta:
#   ~/.local/bin   uv ja yt-dlp
#   ~/.pixi/bin    ffmpeg, ffprobe, node, npm, npx, deno, git
#   ~/.claude/skills   HyperFramesi skillid
#
# Kasutamine:
#   bash setup/install.sh tools    # uv, pixi, ffmpeg, Node 22, Deno, Git, yt-dlp
#   bash setup/install.sh skills   # HyperFramesi skillid + renderdamise Chrome
#   bash setup/install.sh model    # Whisperi mudeli allalaadimine (võib võtta 5-15 min)
#   bash setup/install.sh check    # kontroll ja kokkuvõte
#   bash setup/install.sh all      # kõik järjest
#
# Skripti võib julgelt uuesti käivitada: olemasolev jääb alles, puuduv lisatakse.

set -uo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "$REPO_DIR/setup/versions.env"

export PATH="$HOME/.local/bin:$HOME/.pixi/bin:$PATH"
SKILLS_DIR="$HOME/.claude/skills"

say()  { printf '\n==> %s\n' "$*"; }
ok()   { printf '    OK: %s\n' "$*"; }
fail() { printf '    VIGA: %s\n' "$*" >&2; }

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    fail "käsku '$1' ei leitud. $2"
    exit 1
  fi
}

phase_tools() {
  need_cmd curl "macOS-is on curl alati olemas. Linuxis paigalda see paketihalduriga."

  say "1/4 uv (Pythoni ja Pythoni tööriistade haldur)"
  if command -v uv >/dev/null 2>&1; then
    ok "uv on juba olemas: $(uv --version)"
  else
    curl -LsSf https://astral.sh/uv/install.sh | sh || { fail "uv paigaldus ebaõnnestus"; exit 1; }
    ok "uv paigaldatud: $(uv --version)"
  fi

  say "2/4 pixi (programmide paigaldaja ilma admin-õigusteta)"
  if command -v pixi >/dev/null 2>&1; then
    ok "pixi on juba olemas: $(pixi --version)"
  else
    curl -fsSL https://pixi.sh/install.sh | bash || { fail "pixi paigaldus ebaõnnestus. Kas github.com on võrgus blokeeritud?"; exit 1; }
    ok "pixi paigaldatud: $(pixi --version)"
  fi

  say "3/4 ffmpeg, Node.js 22, Deno ja Git"
  pixi global install "$FFMPEG_SPEC" "$NODE_SPEC" "$DENO_SPEC" "$GIT_SPEC" || { fail "pixi global install ebaõnnestus"; exit 1; }
  ok "$(ffmpeg -version | head -1)"
  ok "$(git --version)"
  ok "node $(node --version)"
  ok "$(deno --version | head -1)"

  say "4/4 yt-dlp"
  uv tool install --upgrade --python "$PYTHON_VERSION" "$YTDLP_SPEC" || { fail "yt-dlp paigaldus ebaõnnestus"; exit 1; }
  ok "yt-dlp $(yt-dlp --version)"
}

phase_skills() {
  mkdir -p "$SKILLS_DIR"
  # Varasem versioon paigaldas kursuse skillid. Koolitusel teeb osaleja need sammud ise,
  # seega eemaldame vanad koopiad, et Claude neid automaatselt ei kasutaks.
  for name in video-transkriptsioon video-loikamine; do
    if [ -d "$SKILLS_DIR/$name" ]; then
      rm -rf "${SKILLS_DIR:?}/$name"
      ok "eemaldasin vana skilli $name"
    fi
  done

  say "HyperFramesi skillid (HeyGeni ametlikud)"
  need_cmd npx "Käivita enne: bash setup/install.sh tools"
  if npx --yes skills add heygen-com/hyperframes -g -a claude-code -y; then
    ok "HyperFramesi skillid paigaldatud"
  else
    fail "HyperFramesi skillide paigaldus ebaõnnestus. See ei takista mooduleid 1-3."
    fail "Skillid paigalduvad ka hiljem käsuga 'npx hyperframes init' moodulis 4."
  fi

  say "HyperFramesi CLI ja renderdamise Chrome"
  hf="hyperframes@$HYPERFRAMES_VERSION"
  if npx --yes "$hf" browser ensure; then
    ok "Chrome renderdamiseks on olemas"
  else
    fail "HyperFrames ei leidnud ega saanud alla laadida Chrome'i"
  fi
}

phase_model() {
  need_cmd uv "Käivita enne: bash setup/install.sh tools"
  say "Whisperi mudel (valitakse arvuti mälu järgi; võib võtta mitu minutit)"
  uv run --python "$PYTHON_VERSION" "$REPO_DIR/setup/whisper.py" --download-only \
    || { fail "mudeli allalaadimine ebaõnnestus. Käivita sama käsk uuesti, allalaadimine jätkub."; exit 1; }
}

phase_check() {
  need_cmd uv "Käivita enne: bash setup/install.sh tools"
  uv run --python "$PYTHON_VERSION" --no-project "$REPO_DIR/setup/check.py"
}

case "${1:-all}" in
  tools)  phase_tools ;;
  skills) phase_skills ;;
  model)  phase_model ;;
  check)  phase_check ;;
  all)    phase_tools && phase_skills && phase_model && phase_check ;;
  *) echo "Kasutus: bash setup/install.sh [tools|skills|model|check|all]"; exit 2 ;;
esac
