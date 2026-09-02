# Personvernmodell

**Språk:** Norsk | [English](PRIVACY.md)

Skrivi er utviklet for å utføre talegjenkjenning lokalt.

## Data som lagres

- Nedlastede modellfiler.
- Innstillinger brukeren har valgt.
- Programversjon og diagnostisk informasjon som ikke inneholder diktert
  innhold, dersom diagnostikk innføres i en fremtidig versjon.

## Data som ikke lagres

- Mikrofonopptak.
- Transkripsjoner.
- Kopier av diktert tekst på utklippsbordet.
- Forespørsler til skybaserte talegjenkjenningstjenester.

Lydopptak oppbevares i programmets arbeidsminne. Programmet gjør et best mulig
forsøk på å overskrive endringsbare lydbuffere etter behandlingen. Python kan
ikke garantere forensisk sletting av uforanderlige tekststrenger fra minnet.

Programmet teksten settes inn i, kan beholde teksten gjennom angrehistorikk,
automatisk lagring, nettleserlagring, synkronisering eller egen telemetri. Denne
behandlingen er utenfor Skrivis kontroll.

Den anbefalte Small-modellen lastes ned fra distribusjonsverten på Hugging Face
under førstegangsoppsettet dersom den ikke allerede er mellomlagret. Andre
modeller lastes bare ned etter at brukeren velger Last ned. Distribusjonsverten
kan se vanlig tilkoblingsinformasjon, som IP-adressen forespørselen kommer fra,
under nedlastingen. Skrivi sender ingen opptak, transkripsjoner, konto-ID-er
eller brukstelemetri.

Etter at en kontrollert nedlasting er fullført, laster Skrivi modellen fra en
lokal filbane. Transkripsjon, valg av installert modell, kontroll og fjerning
fungerer uten nett og henter ikke en ekstern modellkatalog.
