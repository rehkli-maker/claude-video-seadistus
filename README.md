# Claude AI videomonteerija: töökoha seadistus

See repo valmistab sinu arvuti ette koolituseks "Claude AI videomonteerija". Sa ei pea ise midagi paigaldama: annad Claude Code'ile lingi ja tema teeb ülejäänu.

**Tee see enne koolitust ära.** Kõige parem on seda teha kodus, sest kogu paigaldus võtab 10-20 minutit ja laadib alla mitu gigabaiti.

## Mida sul enne vaja on

1. **Claude'i tasuline konto** (Pro, Max, Team või Enterprise).
2. **Claude'i töölauarakendus** Maci või Windowsi jaoks: [claude.com/download](https://claude.com/download). Rakenduses kasutame vahekaarti **Code**.
3. **Ainult Windowsis: Git for Windows**: [git-scm.com/downloads/win](https://git-scm.com/downloads/win). Claude Code vajab seda Windowsis niikuinii. Paigaldamisel võid kõik vaikevalikud jätta nii, nagu need on.
4. Umbes **6 GB vaba kettaruumi**.

Admin-parooli pole vaja. Kõik paigaldub sinu kasutaja kodukausta.

## Seadistus: üks lause

1. Ava Claude'i rakendus ja vali **Code**.
2. Vali töökaustaks oma kodukaust.
3. Kleebi vestlusesse:

```
Klooni https://github.com/rehkli-maker/claude-video-seadistus minu kodukausta, ava see kaust ja seadista mu arvuti videokoolituseks, järgides repo CLAUDE.md juhiseid.
```

4. Claude ütleb, mida ta teeb, ja küsib luba. Vasta **jah**. Iga käsu juures võib ta luba uuesti küsida, siis vajuta **Allow**.
5. Lõpus näed kontrolli tulemust. Kui seal on **KÕIK VALMIS**, tee sellest kuvatõmmis ja saada koolitajale.
6. **Sulge Claude'i rakendus täielikult ja ava uuesti.** Alles siis on uued tööriistad kasutusel.

## Mida paigaldatakse

| Tööriist | Milleks |
|---|---|
| **ffmpeg** | video lõikamine, liitmine ja eksport |
| **Whisper** (faster-whisper) | kõne tekstiks, igal sõnal oma ajatempel |
| **yt-dlp** ja **Deno** | eeskujuvideote allalaadimine |
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
powershell -ExecutionPolicy Bypass -File setup\install.ps1 all
```

Faasid on `tools`, `skills`, `model` ja `check`. Neid saab käivitada ka ükshaaval.

## Eemaldamine

Kui tahad kõik hiljem ära kustutada:

- kaust `~/.pixi` (ffmpeg, Node, Deno)
- käsk `uv tool uninstall yt-dlp`, seejärel kaust `~/.local/bin/uv` ja uv vahemälu
- kaustad `~/.claude/skills/video-transkriptsioon` ja `~/.claude/skills/video-loikamine` ning HyperFramesi skillid samas kaustas
- Whisperi mudel kaustas `~/.cache/huggingface/hub`
- kaust `~/.claude-video`

## Koolitajale

- Versioonid on failis `setup/versions.env`.
- `faster-whisper`, `ctranslate2` ja `av` on lukustatud failis `skills/video-transkriptsioon/scripts/transcribe.py`. Uusim `av` (19.x) ei tööta `faster-whisper` 1.2.1-ga. Enne lukustuse muutmist testi.
- Näidisvideo ja varufailid käivad kausta `naidis/`. Vaata `naidis/README.md`.
