# Claude AI videomonteerija: tööriistade paigaldus (Windows)
#
# Admin-õigusi pole vaja. Kõik läheb kasutaja kodukausta:
#   %USERPROFILE%\.local\bin     uv ja yt-dlp
#   %USERPROFILE%\.pixi\bin      ffmpeg, ffprobe, node, npm, npx, deno, git
#   %USERPROFILE%\.claude\skills HyperFramesi skillid
#
# Git for Windowsit pole vaja: git paigaldatakse koos teiste tööriistadega.
#
# Kasutamine repo kaustas (töötab nii PowerShellis kui Git Bashis):
#   powershell.exe -ExecutionPolicy Bypass -File setup/install.ps1 tools
#   powershell.exe -ExecutionPolicy Bypass -File setup/install.ps1 skills
#   powershell.exe -ExecutionPolicy Bypass -File setup/install.ps1 model
#   powershell.exe -ExecutionPolicy Bypass -File setup/install.ps1 check
#   powershell.exe -ExecutionPolicy Bypass -File setup/install.ps1 all
#
# Skripti võib julgelt uuesti käivitada.

param([string]$Phase = "all")

# Väliste käskude vigu kontrollitakse $LASTEXITCODE kaudu
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$RepoDir = Split-Path -Parent $PSScriptRoot
$SkillsDir = Join-Path $env:USERPROFILE ".claude\skills"
$sep = [IO.Path]::PathSeparator
$env:Path = (Join-Path $env:USERPROFILE ".local\bin") + $sep + (Join-Path $env:USERPROFILE ".pixi\bin") + $sep + $env:Path
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"

# versions.env lugemine
$V = @{}
Get-Content (Join-Path $RepoDir "setup\versions.env") | ForEach-Object {
    if ($_ -match '^\s*([A-Z_]+)\s*=\s*"?([^"]*)"?\s*$') { $V[$Matches[1]] = $Matches[2] }
}

function Say($m)  { Write-Host ""; Write-Host "==> $m" }
function Ok($m)   { Write-Host "    OK: $m" }
function Fail($m) { Write-Host "    VIGA: $m" -ForegroundColor Red }
function Has($c)  { [bool](Get-Command $c -ErrorAction SilentlyContinue) }

# Käivitab käsu, näitab väljundit ja tagastab ainult $true/$false.
# (Out-Host on vajalik: muidu läheks käsu väljund funktsiooni tagastusväärtusse.)
function Run($exe, [string[]]$argList) {
    & $exe @argList | Out-Host
    return ($LASTEXITCODE -eq 0)
}

function Phase-Tools {
    Say "1/4 uv (Pythoni ja Pythoni tööriistade haldur)"
    if (Has "uv") { Ok "uv on juba olemas: $(uv --version)" }
    else {
        powershell -ExecutionPolicy Bypass -NoProfile -Command "irm https://astral.sh/uv/install.ps1 | iex"
        if (-not (Has "uv")) { Fail "uv paigaldus ebaõnnestus"; exit 1 }
        Ok "uv paigaldatud: $(uv --version)"
    }

    Say "2/4 pixi (programmide paigaldaja ilma admin-õigusteta)"
    if (Has "pixi") { Ok "pixi on juba olemas: $(pixi --version)" }
    else {
        powershell -ExecutionPolicy Bypass -NoProfile -Command "irm -useb https://pixi.sh/install.ps1 | iex"
        if (-not (Has "pixi")) { Fail "pixi paigaldus ebaõnnestus. Kas github.com on võrgus blokeeritud?"; exit 1 }
        Ok "pixi paigaldatud: $(pixi --version)"
    }

    Say "3/4 ffmpeg, Node.js 22, Deno ja Git"
    if (-not (Run "pixi" @("global", "install", $V.FFMPEG_SPEC, $V.NODE_SPEC, $V.DENO_SPEC, $V.GIT_SPEC))) {
        Fail "pixi global install ebaõnnestus"; exit 1
    }
    Ok "$((ffmpeg -version | Select-Object -First 1))"
    Ok "$(git --version)"
    Ok "node $(node --version)"
    Ok "$((deno --version | Select-Object -First 1))"

    Say "4/4 yt-dlp"
    if (-not (Run "uv" @("tool", "install", "--upgrade", "--python", $V.PYTHON_VERSION, $V.YTDLP_SPEC))) {
        Fail "yt-dlp paigaldus ebaõnnestus"; exit 1
    }
    Ok "yt-dlp $(yt-dlp --version)"
}

function Phase-Skills {
    New-Item -ItemType Directory -Force -Path $SkillsDir | Out-Null
    # Varasem versioon paigaldas kursuse skillid. Koolitusel teeb osaleja need sammud ise,
    # seega eemaldame vanad koopiad, et Claude neid automaatselt ei kasutaks.
    foreach ($name in @("video-transkriptsioon", "video-loikamine")) {
        $old = Join-Path $SkillsDir $name
        if (Test-Path $old) { Remove-Item -Recurse -Force $old; Ok "eemaldasin vana skilli $name" }
    }

    if (-not (Has "npx")) { Fail "npx puudub. Käivita enne: install.ps1 tools"; exit 1 }

    Say "HyperFramesi skillid (HeyGeni ametlikud)"
    if (Run "npx" @("--yes", "skills", "add", "heygen-com/hyperframes", "-g", "-a", "claude-code", "-y")) {
        Ok "HyperFramesi skillid paigaldatud"
    } else {
        Fail "HyperFramesi skillide paigaldus ebaõnnestus. See ei takista mooduleid 1-3."
        Fail "Skillid paigalduvad ka hiljem käsuga 'npx hyperframes init' moodulis 4."
    }

    Say "HyperFramesi CLI ja renderdamise Chrome"
    $hf = "hyperframes@$($V.HYPERFRAMES_VERSION)"
    if (Run "npx" @("--yes", $hf, "browser", "ensure")) { Ok "Chrome renderdamiseks on olemas" }
    else { Fail "HyperFrames ei leidnud ega saanud alla laadida Chrome'i" }
}

function Phase-Model {
    if (-not (Has "uv")) { Fail "uv puudub. Käivita enne: install.ps1 tools"; exit 1 }
    Say "Whisperi mudel (valitakse arvuti mälu järgi; võib võtta mitu minutit)"
    $script = Join-Path $RepoDir "setup\whisper.py"
    if (-not (Run "uv" @("run", "--python", $V.PYTHON_VERSION, $script, "--download-only"))) {
        Fail "Mudeli allalaadimine ebaõnnestus. Käivita sama käsk uuesti, allalaadimine jätkub."; exit 1
    }
}

function Phase-Check {
    if (-not (Has "uv")) { Fail "uv puudub. Käivita enne: install.ps1 tools"; exit 1 }
    & uv run --python $V.PYTHON_VERSION --no-project (Join-Path $RepoDir "setup\check.py")
    exit $LASTEXITCODE
}

switch ($Phase) {
    "tools"  { Phase-Tools }
    "skills" { Phase-Skills }
    "model"  { Phase-Model }
    "check"  { Phase-Check }
    "all"    { Phase-Tools; Phase-Skills; Phase-Model; Phase-Check }
    default  { Write-Host "Kasutus: install.ps1 [tools|skills|model|check|all]"; exit 2 }
}
