---
name: video-loikamine
description: Lõikab kõnelevast videost välja pikad pausid, kordusvõtted ja pooleli jäänud laused ning teeb puhta work/cut.mp4 koos pildi ja heli sünkroonikontrolliga. Kasuta, kui kasutaja palub videot lõigata, pause eemaldada, kordusi leida, teha cut list või kontrollida sünkrooni. Eeldab work/words.json faili (skill video-transkriptsioon).
---

# Video lõikamine

Lõikamine toimub transkriptsiooni põhjal. Kõigepealt tehakse plaan (cut list), kasutaja kinnitab selle ja alles siis lõigatakse.

## Põhimõtted

- **Algset faili ei muudeta kunagi.** Tulemus on `work/cut.mp4`.
- **Kõigepealt plaan, siis lõige.** Ära lõika enne, kui kasutaja on cut listi heaks kiitnud.
- Vasta eesti keeles, lühidalt ja selgelt.

Eeldus: olemas on `work/words.json`. Kui seda pole, kasuta enne skilli `video-transkriptsioon`.

Skriptid asuvad selle skilli kaustas `~/.claude/skills/video-loikamine/scripts/`.

## 1. Pauside analüüs

```bash
uv run --python 3.12 ~/.claude/skills/video-loikamine/scripts/pauses.py work/words.json --make-cutlist
```

- Leiab pausid üle 0,6 s ja arvutab, kui palju lühendamine 0,25 s peale säästab. Need on vaikeväärtused, neid saab muuta valikutega `--threshold` ja `--target`.
- Kirjutab `work/pausid.txt` (raport) ja `work/cutlist.json` (mustand: kogu kõne alles, pausid lühendatud).
- Näita kasutajale raporti kokkuvõtet: mitu pausi, kui palju säästab, uus pikkus.

## 2. Kordusvõtted ja pooleli jäänud laused

Loe `work/transcript.txt` ja `work/words.json` läbi ning leia:

- **Kordused:** sama lause või lause algus öeldud mitu korda. Hoia alles **viimane täielik versioon**, sest tavaliselt on see parim.
- **Katkestused:** lause, mis jääb poole pealt pooleli ja algab uuesti.
- **Täitesõnad**, kui kasutaja soovib, näiteks "ee", "nagu", "noh". Neid eemalda ainult kasutaja loal.

Koosta nimekiri ajakoodidega:
```
01:12.40-01:15.80  KORDUS (eemaldada): "Selles videos räägin..."  -> alles jääb 01:16.20 versioon
02:03.10-02:04.90  KATKESTUS (eemaldada): "Ja kolmas asi on"
```
Märgi eraldi juhtumid, milles sa pole kindel. Lase kasutajal need otsustada.

## 3. Cut list ja kinnitus

Võta `work/cutlist.json` mustandist eemaldatavad lõigud välja. Lõikekoht pane alati sõnade vahele, kasutades `words.json` aegu: eelmise alles jääva sõna `end` + 0,12 s ja järgmise alles jääva sõna `start` - 0,12 s. Ära lõika sõna keskelt.

Formaat:
```json
{"source": "../raw/VIDEO.mp4",
 "segments": [{"start": 0.20, "end": 12.35, "note": "sissejuhatus"},
              {"start": 16.08, "end": 41.70}]}
```
Lõigud pannakse kokku antud järjekorras.

Näita kasutajale lühikokkuvõtet: mitu lõiku, mis eemaldatakse, uus pikkus. **Oota kasutaja OK-d.**

## 4. Lõikamine ja sünkroonikontroll

```bash
uv run --python 3.12 ~/.claude/skills/video-loikamine/scripts/cut.py work/cutlist.json
```

- Lõikekohad joondatakse kaadripiirile ja heli saab lõikekohtadele 10 ms sujuvuse, et ei tekiks klõpse.
- Lõpus võrreldakse pildi ja heli pikkust. Erinevus alla 0,1 s on korras.
- Kui skript annab sünkroonihoiatuse (väljumiskood 3), ütle seda kasutajale ja paku, et vaatate üle videos hilisemad lõikekohad.

Palu kasutajal `work/cut.mp4` läbi vaadata. Paranduste korral muuda `cutlist.json` ja lõika uuesti. Algne video jääb kogu aeg puutumata.

## Kui midagi ei tööta

- `ffmpeg puudub`: töökoht pole seadistatud. Kasutaja peab käivitama kursuse paigalduse.
- Telefonivideo kaadrisagedus kõigub: `cut.py` teeb väljundi ühtlase kaadrisagedusega, nii et see on lahendatud.
