---
name: video-transkriptsioon
description: Transkribeerib kõnelevast videost teksti sõnaaegadega (work/words.json, work/transcript.txt, work/kahtlased-sonad.txt) kohaliku Whisperiga. Kasuta, kui kasutaja palub videot transkribeerida, teha subtiitrite või montaaži jaoks sõnaajad või leida, mida videos öeldakse.
---

# Video transkriptsioon sõnaaegadega

Kohalik Whisper (faster-whisper) teeb videost teksti, kus igal sõnal on algus- ja lõpuaeg. See on kogu montaaži alus: kui tekstil on ajad, saab videot monteerida nagu teksti.

## Põhimõtted

- **Algset faili ei muudeta kunagi.** Algne video on kaustas `raw/`, kogu töö käib kaustas `work/`.
- **Claude teeb ettepaneku, kasutaja otsustab.** Enne pikka tööd ütle, mida teed ja kui kaua see umbes võtab.
- Vasta kasutajale eesti keeles ja lihtsalt. Ära kirjuta pikki tehnilisi selgitusi, kui kasutaja neid ei küsi.

## Sammud

1. **Leia video.** Vaata projektikausta. Kui videol pole oma kausta, paku struktuur:
   ```
   minu-video/
     raw/     algne video (ainult loetakse)
     work/    kõik vahefailid ja tulemused
   ```
   Video teisaldamiseks või kopeerimiseks `raw/` kausta küsi kasutajalt luba.

2. **Küsi nimed ja terminid.** Küsi kasutajalt ühe lausega, kas videos on nimesid, asutusi või erialaterminid. Kui on, anna need `--prompt` kaudu edasi. See parandab tuvastust eesti keeles märgatavalt.

3. **Käivita transkriptsioon.** Skript asub selle skilli kaustas:
   ```bash
   uv run --python 3.12 ~/.claude/skills/video-transkriptsioon/scripts/transcribe.py raw/VIDEO.mp4 --prompt "Nimi Perekonnanimi, Tartu Ülikool"
   ```
   - Mudel valitakse arvuti mälu järgi: vähemalt 15 GB mälu korral `large-v3`, vähemalt 7 GB korral `medium`, muidu `small`. Teise mudeli saab valida `--model medium` jne.
   - Keel on vaikimisi eesti (`--language et`). Inglise keele jaoks kasuta `--language en`.
   - Arvutil võtab töö umbes 1-3 korda video pikkuse. Ütle seda kasutajale enne käivitamist.
   - Pikema video puhul kasuta käsu tööriista pikka ajapiirangut (kuni 10 minutit) või käivita taustal.

4. **Näita tulemust.** Ütle, mitu sõna ja lõiku tuli ning kui kaua see võttis. Näita `work/kahtlased-sonad.txt` sisu. Seal on sõnad, milles Whisper polnud kindel, näiteks nimed, terminid ja võõrsõnad.

5. **Paranda koos kasutajaga.** Küsi kahtlaste sõnade kohta, mis on õige. Parandused tee `work/words.json` failis ainult välja `word` sees. Aegu (`start`, `end`) ära muuda. Seejärel uuenda `work/transcript.txt` samade parandustega.

## Failid

- `work/words.json`: `words[]` igas kirjes `word`, `start`, `end` (sekundites), `prob` (kindlus 0-1), `segment`. `segments[]` sisaldab lõikude teksti ja aegu.
- `work/transcript.txt`: loetav tekst, iga lõik oma real ajatempliga.
- `work/kahtlased-sonad.txt`: sõnad kindlusega alla 0,6 koos ümbritseva tekstiga.

## Kui midagi ei tööta

- `uv` puudub: töökoht pole seadistatud. Kasutaja peab käivitama kursuse paigalduse (vaata kursuse repo `README.md`).
- Mudel laeb esimest korda: allalaadimine võtab aega, `large-v3` on umbes 3 GB.
- Mälu saab otsa või töö on väga aeglane: proovi `--model medium` või `--model small`.
