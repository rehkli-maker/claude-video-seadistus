# Näidisvideo ja varufailid

Siia käib 1-2-minutiline näidisvideo, millega osalejad saavad harjutada, kui nende oma salvestus pole valmis. Sama kausta käivad ka valmis varufailid juhuks, kui osaleja transkriptsioon ebaõnnestub.

## Koolitajale: kuidas see kaust täita

1. Salvesta 1-2-minutiline video, kus räägid kaamerasse. Ütle üks lause meelega kaks korda ja jäta üks lause pooleli, nagu kursuse ülesandes 1.1.
2. Pane see faili `naidis/raw/naidisvideo.mp4`. Hoia fail alla 50 MB, sest GitHub hoiatab suuremate failide puhul ja keelab üle 100 MB faile.
3. Transkribeeri see Claude Code'iga samamoodi, nagu osalejad koolitusel teevad (Whisper, mudel large-v3, sõnaajad), nii et tekiksid failid `naidis/work/words.json` ja `naidis/work/transcript.txt`.
4. Paranda vead nendes failides.
5. Nimeta kaust `naidis/work` ümber kaustaks `naidis/varu`, et `.gitignore` seda vahele ei jätaks.

## Osalejale: kuidas varufaile kasutada

Kui sinu transkriptsioon ebaõnnestus, kopeeri `naidis/raw/naidisvideo.mp4` oma projekti kausta `raw/` ning `naidis/varu/` sisu oma projekti kausta `work/`. Siis saad jätkata korduste leidmise ja lõikamisega.
