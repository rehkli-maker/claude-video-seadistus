# Claude AI videomonteerija: töökoha seadistus

See repo seadistab osaleja arvuti koolituseks "Claude AI videomonteerija". Pärast seadistust on arvutis olemas ffmpeg, Whisper (faster-whisper), yt-dlp, Node.js 22, Deno, HyperFrames ja kursuse skillid.

**Räägi kasutajaga alati eesti keeles, lühidalt ja lihtsalt.** Kasutaja on algaja, mitte arendaja. Ära selgita tehnilisi detaile, kui ta neid ei küsi.

## Reeglid

- **Ära kunagi kasuta `sudo`-t ega paigalda Homebrew'd.** Kõik paigaldub kasutaja kodukausta ilma admin-õigusteta. Kui mõni samm küsib admin-parooli, on midagi valesti: peatu ja ütle kasutajale.
- **Ära muuda süsteemi Pythonit** ega paigalda midagi `pip install`-iga. Pythoni asjad käivad `uv` kaudu.
- Kasuta ainult selle repo skripte. Ära improviseeri paigalduskäske.
- Skripte võib julgelt uuesti käivitada: olemasolev jääb alles, puuduv lisatakse.

## Seadistus samm-sammult

### 1. Tuvasta operatsioonisüsteem

- macOS või Linux: käsud on `bash setup/install.sh <faas>`.
- Windows (Claude Code kasutab seal Git Bashi): käsud on `powershell.exe -ExecutionPolicy Bypass -File setup/install.ps1 <faas>`.

### 2. Ütle kasutajale, mis juhtub, ja küsi OK

Umbes nii:

> Paigaldan su arvutisse videomonteerimise tööriistad: ffmpeg, Whisper, yt-dlp, Node.js ja HyperFrames. Admin-parooli pole vaja, kõik läheb sinu kodukausta. Selleks on vaja umbes 6 GB vaba ruumi ja 10-20 minutit, millest suurema osa võtab Whisperi mudeli allalaadimine. Kas võin alustada?

Oota kasutaja vastust.

### 3. Käivita faasid ükshaaval

Käivita iga faas eraldi käsuna, ajapiiranguga 600000 ms. Pärast iga faasi ütle kasutajale ühe lausega, mis valmis sai.

1. `tools`: uv, pixi, ffmpeg, Node.js 22, Deno, yt-dlp (umbes 2-5 min)
2. `skills`: kursuse skillid ja HyperFramesi skillid kausta `~/.claude/skills`, Chrome renderdamiseks (umbes 1-3 min)
3. `model`: Whisperi mudel, mis valitakse mälu järgi (small 0,5 GB, medium 1,5 GB, large-v3 3 GB). Kui see ületab ajapiirangu, käivita sama käsk uuesti: allalaadimine jätkub sealt, kus pooleli jäi.
4. `check`: kontroll, kus iga tööriist teeb väikese päris testi

Kui `check` ütleb **KÕIK VALMIS**, mine sammu 5 juurde. Kui midagi on puudu, loe väljundist rida "Lahendus", tee see ja käivita `check` uuesti. Vaata ka allpool olevat jaotist "Tuntud probleemid".

### 4. YouTube'i test (valikuline)

Kui kasutaja tahab eeskujuvideoid alla laadida, käivita:

```
uv run --python 3.12 --no-project setup/check.py --online --skip-slow
```

### 5. Lõpeta

Ütle kasutajale:

1. Töökoht on valmis.
2. **Sulge Claude'i rakendus täielikult ja ava uuesti**, et uued tööriistad ja skillid laeksid.
3. Saada koolitajale kuvatõmmis kontrolli tulemusest. Fail on ka kaustas `~/.claude-video/kontroll.txt`.
4. Videod tee eraldi projektikausta, mitte selle repo sisse, näiteks `~/Videod/minu-esimene-video/` ning selle alla kaustad `raw/` ja `work/`.

## Kursuse skillid

- `video-transkriptsioon`: video tekstiks sõnaaegadega (`work/words.json`, `work/transcript.txt`, `work/kahtlased-sonad.txt`)
- `video-loikamine`: pauside analüüs, kordusvõtete leidmine, cut list, `work/cut.mp4` ja sünkroonikontroll
- HyperFramesi skillid (`/hyperframes` jt): graafika ja animatsioonid HTML-ina, renderdamine videoks

## Tuntud probleemid

| Sümptom | Põhjus ja lahendus |
|---|---|
| pixi paigaldus ebaõnnestub, viga github.com-iga | Asutuse võrk blokeerib GitHubi allalaadimisi. Proovi kodus või telefoni levialaga. |
| Windows: "running scripts is disabled on this system" | Käivita täpselt nii, nagu ülal: `powershell.exe -ExecutionPolicy Bypass -File ...` |
| Windows: viirusetõrje või SmartScreen blokeerib `.pixi\bin` faili | pixi kasutab väikeseid käivitusfaile. Luba need või lisa `%USERPROFILE%\.pixi` erandiks. |
| Mac: `xcrun: error: invalid active developer path` | Git puudub. Kasutaja peab käivitama `xcode-select --install` ja vajutama Install. Admin-parooli see tavaliselt ei vaja. |
| `uv`, `pixi`, `ffmpeg` "command not found" pärast paigaldust | PATH uueneb alles uues aknas. Skriptid lisavad PATH-i ise, aga Claude'i rakendus tuleb lõpuks uuesti käivitada. Seniks kasuta täisteid `~/.local/bin/uv` ja `~/.pixi/bin/ffmpeg`. |
| Whisper on väga aeglane või mälu saab otsa | Kasuta väiksemat mudelit: `WHISPER_MODEL=small`, seejärel käivita `model` ja `check` uuesti. |
| Vähe kettaruumi | Vaja on umbes 6 GB. Ütle kasutajale, kui palju puudu on. |
| Asutuse proxy | Küsi kasutajalt proxy aadress ja sea `HTTPS_PROXY` ning `HTTP_PROXY` keskkonnamuutujad. |
| Windows ARM arvuti (Snapdragon, Surface Pro X) | Pole testitud. Kõik paketid ei pruugi olla saadaval. Ütle seda kasutajale ausalt ja soovita teist arvutit. |

## Mida kuhu paigaldatakse

| Asukoht | Sisu |
|---|---|
| `~/.local/bin` | `uv`, `yt-dlp` |
| `~/.pixi/bin` | `ffmpeg`, `ffprobe`, `ffplay`, `node`, `npm`, `npx`, `deno` |
| `~/.claude/skills` | kursuse skillid ja HyperFramesi skillid |
| `~/.cache/huggingface` (Windowsis `%USERPROFILE%\.cache\huggingface`) | Whisperi mudel |
| `~/.claude-video/kontroll.txt` | viimase kontrolli tulemus |

Versioonid on failis `setup/versions.env`.
