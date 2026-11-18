# Claude AI videomonteerija: töökoha seadistus

See repo valmistab sinu arvuti ette koolituseks "Claude AI videomonteerija". Sa ei pea ise midagi paigaldama: annad Claude Code'ile lingi ja tema teeb ülejäänu.

**Tee see enne koolitust ära.** Kõige parem on seda teha kodus, sest kogu paigaldus võtab 10-20 minutit ja laadib alla mitu gigabaiti.

## Mida sul enne vaja on

1. **Claude'i tasuline konto** (Pro, Max, Team või Enterprise).
2. **Claude'i töölauarakendus.** Laadi see alla aadressilt [claude.com/download](https://claude.com/download), paigalda ja logi sisse.
3. Umbes **6 GB vaba kettaruumi**.

Rohkem pole midagi vaja. Sa ei pea ise midagi muud paigaldama ja admin-parooli ei küsita. Ka Windowsis pole vaja eraldi programme.

## Seadistus

1. **Ava Claude'i rakendus** ja vali üleval **Code**.
2. **Kui rakendus küsib kausta**, vali oma kodukaust. See on kaust, mis kannab sinu kasutajanime.
3. **Kopeeri see lause ja kleebi Claude'i vestlusesse:**

```
Laadi alla https://github.com/rehkli-maker/claude-video-seadistus/archive/refs/heads/main.zip, paki see lahti minu kodukausta, ava lahtipakitud kaust ja seadista mu arvuti videokoolituseks, järgides selle kausta CLAUDE.md juhiseid.
```

4. **Anna luba.** Claude ütleb, mida ta teha kavatseb, ja küsib, kas võib alustada. Vasta **jah**. Töö käigus küsib ta luba ka üksikute sammude jaoks. Siis vajuta **Allow**. See on normaalne ja nii peabki olema.
5. **Oota 10-20 minutit.** Vahepeal võib tunduda, et midagi ei toimu. Tavaliselt laadib Claude siis Whisperi mudelit alla. Ära sulge rakendust.
6. **Vaata tulemust.** Lõpus näed kontrolli kokkuvõtet. Kui seal on **KÕIK VALMIS**, tee sellest kuvatõmmis ja saada koolitajale. Kui seal on midagi punast, saada samuti kuvatõmmis.
7. **Sulge Claude'i rakendus täielikult ja ava uuesti.** Alles siis on uued tööriistad kasutusel.
   - Macis vajuta rakenduses **Cmd + Q**.
   - Windowsis sulge aken. Kui ekraani paremas alanurgas on veel Claude'i ikoon, tee sellel paremklõps ja vali **Quit**.

## Mida paigaldatakse

| Tööriist | Milleks |
|---|---|
| **ffmpeg** | video lõikamine, liitmine ja eksport |
| **Whisper** (faster-whisper) | kõne tekstiks, igal sõnal oma ajatempel |
| **yt-dlp** ja **Deno** | eeskujuvideote allalaadimine |
| **Git** | HyperFramesi skillide paigaldus (Windowsis pole Git for Windowsit vaja) |
| **Node.js 22** | HyperFramesi jaoks |
| **HyperFrames** ja Chrome | graafika ja animatsioonid, renderdamine videoks |
| **Kursuse skillid** | `video-transkriptsioon` ja `video-loikamine` |

Whisperi mudel valitakse sinu arvuti mälu järgi:

| Mälu | Mudel | Suurus | Eesti keel |
|---|---|---|---|
| 16 GB või rohkem | large-v3 | umbes 3 GB | parim |
| 8 GB | medium | umbes 1,5 GB | hea |
| alla 8 GB | small | umbes 0,5 GB | rohkem vigu |

## Kui midagi läheb valesti

Kopeeri veateade Claude'ile ja küsi, mis valesti läks. `CLAUDE.md` failis on Claude'il olemas tuntud probleemide nimekiri.

Kontrolli saad igal ajal uuesti käivitada. Ütle Claude'ile repo kaustas:

```
Kontrolli mu videotöökohta.
```

Kui jääd kinni, saada koolitajale fail `kontroll.txt`. See asub kodukaustas, kaustas `.claude-video`.

## Käsitsi paigaldus (edasijõudnutele)

macOS ja Linux:
```bash
bash setup/install.sh all
```

Windows (PowerShell):
```powershell
powershell.exe -ExecutionPolicy Bypass -File setup/install.ps1 all
```

Faasid on `tools`, `skills`, `model` ja `check`. Neid saab käivitada ka ükshaaval.

## Eemaldamine

Kui tahad kõik hiljem ära kustutada:

- kaust `~/.pixi` (ffmpeg, Node, Deno, Git)
- käsk `uv tool uninstall yt-dlp`, seejärel kaust `~/.local/bin/uv` ja uv vahemälu
- kaustad `~/.claude/skills/video-transkriptsioon` ja `~/.claude/skills/video-loikamine` ning HyperFramesi skillid samas kaustas
- Whisperi mudel kaustas `~/.cache/huggingface/hub`
- kaust `~/.claude-video`

## Koolitajale

- Versioonid on failis `setup/versions.env`.
- `faster-whisper`, `ctranslate2` ja `av` on lukustatud failis `skills/video-transkriptsioon/scripts/transcribe.py`. Uusim `av` (19.x) ei tööta `faster-whisper` 1.2.1-ga. Enne lukustuse muutmist testi.
- Näidisvideo ja varufailid käivad kausta `naidis/`. Vaata `naidis/README.md`.
