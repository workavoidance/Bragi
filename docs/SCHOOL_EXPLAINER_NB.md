# Skrivi: Lokal tale-til-tekst for elever med lese- og skrivevansker

**Språk:** Norsk | [English](SCHOOL_EXPLAINER.md)

> **Utkast til samtale med skoler.** Skrivi er foreløpig alfa-programvare.
> Dette dokumentet forklarer den tiltenkte utformingen og bruken som et
> tilgjengelighetsverktøy. Det hevder ikke at Skrivi er formelt godkjent av
> Udir, Oslo kommune eller noen skole.

## Hva er Skrivi?

Skrivi er et enkelt tilgjengelighetsverktøy for Windows. Det er utviklet for å
hjelpe elever som synes skriving med tastatur og skriftlig produksjon er
vanskelig.

Eleven holder inne en hurtigtast, snakker naturlig, og Skrivi gjør talen om til
tekst ved markøren. Det kan derfor brukes sammen med vanlige programmer som
Word og nettbaserte skolesystemer.

Skrivi bruker en lokalt installert talegjenkjenningsmodell basert på Whisper.
Selv om denne teknologien bruker kunstig intelligens til talegjenkjenning,
**lager ikke Skrivi svar, ideer eller skriftlig innhold for eleven**. Formålet
er å gi eleven en alternativ måte å skrive inn sine egne ord på.

Enkelt forklart:

**Eleven snakker → Skrivi transkriberer talen → elevens egne ord vises som tekst.**

Dette er ment å kompensere for vansker med skriftlig innskriving, ikke å gi
eleven en faglig kompetanse hen ellers ville vært forventet å vise.

## Personvern og behandling av personopplysninger

Skrivi er bevisst utviklet for å begrense utfordringer knyttet til personvern
og informasjonssikkerhet.

Talegjenkjenningen skjer **lokalt på elevens datamaskin**. Når talemodellen er
lastet ned, krever ikke tale-til-tekst en internettilkobling.

Skrivi er utformet slik at:

- taleopptak ikke sendes til en ekstern server eller skytjeneste;
- transkripsjonen utføres lokalt på datamaskinen;
- Skrivi ikke krever elevkonto eller innlogging;
- Skrivi ikke trenger elevens navn, skole, klasse eller andre identifiserende
  opplysninger;
- diktert lyd ikke skrives til disk av Skrivi;
- Skrivi ikke fører historikk over diktert tekst; og
- Skrivi ikke krever internettilkobling for å utføre tale-til-tekst etter at
  modellen er installert.

Lyden oppbevares i minnet mens den transkriberes. Skrivi frigir lyd- og
transkripsjonsdata etter behandlingen og gjør et best mulig forsøk på å
overskrive lydtabeller i minnet. Som med alle skrivebordsprogrammer kan
programmet teksten settes inn i, beholde teksten gjennom angrehistorikk,
automatisk lagring, skysynkronisering eller lignende funksjoner.

Denne arkitekturen er bevisst. Norske utdanningsmyndigheter krever at
skoleeiere vurderer personvern, informasjonssikkerhet, dataminimering, risiko,
sletting og databehandlerforhold ved innføring av digital teknologi.

Udir beskriver skoleeierens ansvar her:

- [Udir: Barnehage- og skoleeiers ansvar for personvern](https://www.udir.no/regelverk-og-tilsyn/personvern-for-barnehage-og-skole/barnehage--og-skoleeiers-ansvar/)

Datatilsynet forklarer kravet til databehandleravtale når en leverandør
behandler personopplysninger på vegne av en skoleeier:

- [Datatilsynet: Databehandleravtale for skoler](https://www.datatilsynet.no/regelverk-og-verktoy/sporsmal-svar/Skole-og-barnehage/databehandleravtale-for-skoler/)

Skrivi er uttrykkelig utviklet for å unngå at elevens tale eller skriftlige
innhold overføres til utvikleren eller tredjeparter. Dermed kan skolen vurdere
Skrivi ut fra en lokal og frakoblet arkitektur, i stedet for som en vanlig
skybasert tjeneste for skolen.

## Tilgjengelighet

Skrivi er selv ment som et tilgjengelighetsverktøy.

Brukergrensesnittet utvikles for å være enkelt, kunne betjenes med tastaturet og
fungere sammen med vanlige tilgjengelighetsfunksjoner i Windows. Tilgjengelighet
og universell utforming vil fortsatt bli vurdert etter hvert som programmet
utvikles.

Norsk veiledning om universell utforming av digitale læringsmiljøer finnes her:

- [Tilsynet for universell utforming av ikt: Universell utforming av det digitale læringsmiljøet i skolen](https://www.uutilsynet.no/veiledning/universell-utforming-av-det-digitale-laeringsmiljoet-i-skolen/2676)

## Bruk i undervisning og vurderingssituasjoner

Skrivi er ment som et **tale-til-tekst-verktøy for skriving** for elever som har
et etablert behov for støtte ved lesing og/eller skriving.

Skrivi bør helst bli et kjent verktøy som eleven bruker i vanlig skolearbeid og,
der det passer, i vurderingssituasjoner i klasserommet.

Det viktige skillet er at Skrivi endrer **måten eleven skriver inn tekst på**,
ikke kunnskapen eller kompetansen som vurderes.

Hvis eleven for eksempel sier:

> Hovedpersonen drar fordi han føler seg fanget.

skriver Skrivi inn disse ordene. Programmet svarer ikke på en oppgave på egen
hånd, skriver ikke om elevens arbeid og lager ikke et forbedret svar.

## Bruk under eksamen

Det norske eksamensregelverket anerkjenner tale-til-tekst som en mulig form for
særskilt tilrettelegging av eksamen.

Den relevante bestemmelsen er **opplæringsforskrifta § 9-34, Særskild
tilrettelegging av eksamen**. Tilretteleggingen skal la eleven vise kompetansen
sin uten å fjerne kompetansen som eksamenen er ment å prøve.

Veiledning fra Udir:

- [Udir: Særskilt tilrettelegging av eksamen](https://www.udir.no/eksamen-og-prover/eksamen/sarskilt-tilrettelegging-av-eksamen/)
- [Udir: § 9-34 Særskild tilrettelegging av eksamen](https://www.udir.no/regelverkstolkninger/opplaring/forskrift-om-grunnskoleopplaringa-og-den-vidaregaande-opplaringa-for-barn-og-unge/kapittel-9-individuell-vurdering/v.-eksamen/-9-34-sarskild-tilrettelegging-av-eksamen/)

Udir innfører sikker nettleser i flere sentralt gitte eksamener. Udir forklarer
at kandidater som trenger eksterne lese- og skrivestøtteprogrammer, kan søke om
særskilt tilrettelegging og, der det passer, få unntak fra kravet om sikker
nettleser. Udir nevner IntoWords og Lingdys som eksempler på slike programmer,
ikke som en uttømmende liste over tillatte produkter.

Gjeldende veiledning fra Udir finnes her:

- [Udir: Eksamensfag med sikker nettleser](https://www.udir.no/eksamen-og-prover/eksamen/slik-endrer-vi-eksamen/eksamensfag-med-sikker-nettleser/)
- [Udir: Administrere eksamen](https://www.udir.no/eksamen-og-prover/eksamen/administrere-eksamen/)

Bruk av Skrivi under en formell eksamen vil derfor være avhengig av at skolen
eller kommunen godkjenner elevens individuelle tilrettelegging og bekrefter at
Skrivi er egnet til formålet.

## Skrivi eksamensmodus

Skrivi er ment å få en særlig begrenset **eksamensmodus**.

Målet er at eksamensmodus bare skal tilby funksjonene som er nødvendige for
tale-til-tekst:

**Mikrofon → lokal talegjenkjenning → ordrett transkripsjon → tekst ved markøren.**

Eksamensmodus er ment ikke å tilby:

- generativ kunstig intelligens;
- generering av svar;
- internettsøk;
- oppsummering;
- omskriving;
- oversettelse;
- KI-assistert forbedring av elevens svar; eller
- tilgang til skybaserte språkmodeller.

Målet er å gjøre det teknisk og pedagogisk tydelig at Skrivi er et
**tilgjengelighetsverktøy for innskriving**, ikke en KI-assistent.

## Dette ber vi skolen vurdere

På dette stadiet ber vi skolen vurdere å la eleven bruke Skrivi som et lokalt
tale-til-tekst-verktøy i egnet, vanlig skolearbeid.

Da kan eleven, lærerne og skolens IT-personell vurdere om verktøyet er nyttig og
egnet i praksis.

Hvis Skrivi blir en etablert del av elevens vanlige skrivestøtte, ønsker vi
deretter å drøfte bruk i egnede vurderingssituasjoner og, separat, om Skrivi
skal tas med i en eventuell søknad om særskilt tilrettelegging ved elevens
avsluttende eksamener.

Vi gir gjerne skolen teknisk informasjon om Skrivi, viser at programmet fungerer
uten internettilkobling, forklarer nøyaktig hvilke opplysninger det behandler og
samarbeider med skolen om eventuelle krav til personvern, sikkerhet eller
eksamen før programmet tas i bruk.
