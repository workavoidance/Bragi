# Arkitektur

**Språk:** Norsk | [English](ARCHITECTURE.md)

Skrivi er et Windows-program i systemstatusfeltet med en personvernorientert,
lokal kjede for behandling av tale.

## Nåværende dataflyt

1. En konfigurerbar, global trykk-og-snakk-lytter starter mikrofonopptak i
   minnet. Høyre Ctrl-tast er standard.
2. Når den valgte tasten slippes, lukkes lydstrømmen.
3. Lyden normaliseres til én kanal med 16 kHz float32-data.
4. faster-whisper oppdager språket og transkriberer lokalt.
5. Windows `SendInput` setter inn UTF-16-tekst ved den eksisterende markøren.
6. Lydbufferne overskrives etter beste evne, og referansene frigis.

Utklippsbordet brukes ikke.

## Tiltenkte modulgrenser

- `core`: tilstandsmaskin, styring av opptak og transkripsjonsflyt.
- `models`: katalog over støttede modeller, nedlasting, kontroll og fjerning.
- `settings`: versjonsstyrt konfigurasjon, standardverdier og migrering.
- `platform`: hurtigtaster i Windows, innsetting av Unicode, oppstart og
  oppdagelse av enheter.
- `ui`: ikon i systemstatusfeltet, opptaksindikator, innstillingsvindu og
  visning av feil.

Kjernen skal ikke importere implementasjonen av brukergrensesnittet.
Hendelser i brukergrensesnittet krysser grensen gjennom små grensesnitt, slik
at oppførselen i kjernen kan testes uavhengig.

## Tråder

Tilbakekall fra lyd, modellasting og transkripsjon skal aldri blokkere
hendelsesløkken i brukergrensesnittet. Bare én transkripsjon godtas om gangen
inntil det eventuelt innføres en bevisst køpolicy.

## Eierskap til data

Modeller og konfigurasjon lagres varig. Opptak og transkripsjoner gjør det ikke.
Diagnoselogger kan inneholde tilstandsoverganger, varighet, modellnavn og
feiltyper, men aldri diktert innhold eller rå lyd.

Nedlastede modeller ligger i `%LOCALAPPDATA%\Skrivi\models` og deles mellom
vanlige versjoner, utviklingsversjoner og forhåndsvisninger. Fremtidige
utviklingsinnstillinger bruker en separat plassering i
`%APPDATA%\Skrivi\development`. Førstegangsoppsett og uttrykkelige
modellnedlastinger kan bruke internett. Transkripsjon med en installert modell
forblir lokal og skal fortsette å fungere uten nettilgang.

Navneendringen til Skrivi flytter tidligere Bragi-mapper for programdata ved
hjelp av en atomisk navneendring på samme lagringsvolum. Dersom navneendringen
mislykkes, brukes den eksisterende mappen videre, slik at innstillinger og store
modellnedlastinger ikke forlates bare fordi merkevaren er endret. Eldre
modellmanifest kan fortsatt leses og får nytt navn etter kontroll.

Modellkatalogen er bygget inn i Skrivi med låste oppstrømsrevisjoner,
filstørrelser og kontrollsummer. Nedlastinger og importer kontrolleres i en
midlertidig klargjøringsmappe før atomisk installasjon. Transkripsjonsmotoren
får en lokal, installert filbane i stedet for en ekstern modell-ID. Dette
forhindrer utilsiktede nettverksoppslag under vanlig diktering. En ny modell
lastes før den erstatter den aktive modellen, og feil ved lagring av
innstillinger gjenoppretter den forrige modellen i minnet.

Hvis modellen ikke kan lastes ved oppstart, går kontrolleren over i en
gjenopprettbar feiltilstand. Bare ett bakgrunnsforsøk kan kjøre om gangen.
Ikonet i systemstatusfeltet, dikteringstasten og vellykket aktivering av en
modell kan be om et nytt forsøk. Hvis en transkripsjon mislykkes, forkastes den
gjeldende lyden i minnet, og kontrolleren går tilbake til Klar, slik at neste
diktering kan starte uten at programmet må startes på nytt.

Programavslutning bruker én tidsavgrenset avslutningssekvens. Den skjuler ikonet
i systemstatusfeltet, blokkerer nytt arbeid i kontrolleren og modellene, stopper
den globale lytteren og mikrofonen, signaliserer avbryting av transkripsjon og
modellarbeid og venter deretter i opptil fem sekunder på at arbeidstrådene skal
tømme lyd fra minnet og fjerne ufullstendige klargjøringsfiler.
Enkeltinstanslåsen frigis sist, også dersom en oppryddingskomponent melder feil.

Den brukergrensesnittuavhengige innstillingsmodulen tar imot og avgir et
uttrykkelig versjonsstyrt skjema. Den kontrollerer en streng liste over tillatte
felt, migrerer gamle skjemaer i minnet, gir personvernsikre advarsler ved
gjenoppretting og erstatter innstillingsfiler atomisk. Ugyldige filer og filer
fra nyere versjoner bevares for feilsøking eller gjenoppretting.

Grensesnitttekst går gjennom den brukergrensesnittuavhengige `i18n`-modulen.
Engelsk kildetekst er den stabile nøkkelen, og norsk bokmål er den første
komplette oversettelseskatalogen. Ved oppstart finner Skrivi det lagrede valget
Automatisk, Engelsk eller Norsk før Qt-komponentene opprettes. Automatisk følger
visningsspråket i Windows på norske Windows-installasjoner og bruker ellers
engelsk. Oversettelse påvirker ikke transkripsjonsspråket og innfører ikke
nettverkstilgang.

Grensesnittkomponentene abonnerer på språkendringer gjennom svake tilbakekall.
Eksisterende Qt-komponenter oversettes på stedet, slik at systemstatusfeltet,
innstillinger, tilgjengelighetsetiketter, overleggstilstand og aktiv
modellfremdrift oppdateres uten å starte lyd, transkripsjon eller modellarbeid
på nytt. Forhåndsvisning av innstillinger kan reverseres frem til lagring.

Aktive innstillinger koordineres som en gjenopprettbar operasjon. Et
mikrofonvalg kontrolleres før aktivering. En ny global tastelytter ugyldiggjør
og stopper den forrige generasjonen før den nye startes, slik at sene
tilbakekall fra en gammel lytter ikke kan starte diktering. Hvis aktivering
eller lagring mislykkes, gjenopprettes den forrige kjørekonfigurasjonen der det
er mulig.

## Implementasjon av brukergrensesnittet

PySide6 Essentials leverer systemstatusfeltet, innstillingsvinduet og det
kompakte statusoverlegget. Hendelsesløkken i Qt blir på hovedtråden.
Kontrollerens arbeidstråder rapporterer tilstand gjennom signaler som legges i
Qt-køen, slik at modellasting og transkripsjon aldri oppdaterer komponenter
direkte. Selve kontrolleren importerer ingen Qt-moduler.

Overlegget er et verktøyvindu som ikke kan ta fokus eller aktivere seg selv. Det
bruker systemets fargepalett og et tekstsymbol sammen med en melding for hver
tilstand, slik at meningen ikke avhenger av farge. Qt 6 gir DPI-skalering per
skjerm. Plasseringen bruker arbeidsområdet på skjermen som inneholder
musepekeren, og støtter skjermer med negative skrivebordskoordinater.
