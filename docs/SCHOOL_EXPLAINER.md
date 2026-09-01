# Skrivi: Offline Speech-to-Text Support for Pupils with Reading and Writing Difficulties

> **Draft for discussion with schools.** Skrivi is currently alpha software. This document explains its intended design and use as an accessibility tool; it does not claim that Skrivi is formally approved by Udir, Oslo kommune, or any school.

## What is Skrivi?

Skrivi is a simple Windows accessibility tool designed to help pupils who find typing and written production difficult.

The pupil holds a keyboard shortcut, speaks naturally, and Skrivi converts the pupil’s speech into text at the current cursor position. It can therefore be used with ordinary applications such as Word and browser-based school systems.

Skrivi uses a locally installed speech-recognition model based on Whisper. Although this technology uses artificial intelligence for speech recognition, **Skrivi does not generate answers, ideas, or written content for the pupil**. Its purpose is to provide an alternative method of entering the pupil’s own words.

In simple terms:

**Pupil speaks → Skrivi transcribes the speech → the pupil’s own words appear as text.**

This is intended to compensate for difficulties with written input, rather than to provide academic competence that the pupil would otherwise be required to demonstrate.

## Privacy and data protection

Skrivi has deliberately been designed to minimise privacy and information-security concerns.

Speech recognition takes place **locally on the pupil’s computer**. After the speech model has been downloaded, speech-to-text does not require an internet connection.

Skrivi is designed so that:

- recorded speech is not sent to an external server or cloud service;
- transcription is performed locally on the computer;
- Skrivi does not require a pupil account or login;
- Skrivi does not need the pupil’s name, school, class, or other identifying information;
- dictated audio is not written to disk by Skrivi;
- Skrivi does not maintain a history of dictated text; and
- Skrivi does not require an internet connection to perform speech-to-text after the model is installed.

Audio is held in memory while it is being transcribed. Skrivi releases the audio and transcription data after processing and makes a best-effort attempt to overwrite audio arrays in memory. As with any desktop application, the destination application may retain the text through its own undo history, autosave, cloud synchronisation, or similar features.

This architecture is intentional. Norwegian education authorities require school owners to consider privacy, information security, data minimisation, risk, deletion, and data-processing arrangements when adopting digital technology.

Udir describes the school owner’s responsibilities here:

- [Udir: Barnehage- og skoleeiers ansvar for personvern](https://www.udir.no/regelverk-og-tilsyn/personvern-for-barnehage-og-skole/barnehage--og-skoleeiers-ansvar/)

Datatilsynet explains the requirement for a data-processing agreement where a supplier processes personal information on behalf of a school owner:

- [Datatilsynet: Databehandleravtale for skoler](https://www.datatilsynet.no/regelverk-og-verktoy/sporsmal-svar/Skole-og-barnehage/databehandleravtale-for-skoler/)

Skrivi is specifically being designed to avoid transferring pupils’ speech or written content to the developer or to third parties. This allows the school to assess Skrivi on the basis of a local/offline architecture rather than as a conventional cloud-based educational service.

## Accessibility

Skrivi is itself intended as an accessibility aid.

Its user interface is being designed to be simple, keyboard-operable, and compatible with normal Windows accessibility features. Accessibility and universal design will continue to be considered as the application is developed.

Norwegian guidance on universal design of digital learning environments is available here:

- [Tilsynet for universell utforming av ikt: Universell utforming av det digitale læringsmiljøet i skolen](https://www.uutilsynet.no/veiledning/universell-utforming-av-det-digitale-laeringsmiljoet-i-skolen/2676)

## Use during lessons and assessments

The intended use of Skrivi is as a **speech-to-text writing aid** for a pupil who has an established need for support with reading and/or writing.

Skrivi should ideally become a familiar tool that the pupil uses during ordinary schoolwork and, where appropriate, classroom assessments.

The important distinction is that Skrivi changes the **method by which the pupil enters text**, rather than providing the knowledge or competence being assessed.

For example, if the pupil says:

> The main character leaves because he feels trapped.

Skrivi types those words. It does not independently answer a question, rewrite the pupil’s work, or generate an improved response.

## Use during examinations

Norwegian examination regulations recognise speech-to-text as a possible form of special examination accommodation.

The relevant regulation is **Opplæringsforskrifta § 9-34, Særskild tilrettelegging av eksamen**. Accommodation must allow the pupil to demonstrate their competence without removing the competence that the examination is intended to assess.

Udir guidance:

- [Udir: Særskilt tilrettelegging av eksamen](https://www.udir.no/eksamen-og-prover/eksamen/sarskilt-tilrettelegging-av-eksamen/)
- [Udir: § 9-34 Særskild tilrettelegging av eksamen](https://www.udir.no/regelverkstolkninger/opplaring/forskrift-om-grunnskoleopplaringa-og-den-vidaregaande-opplaringa-opplaringsforskrifta/tredje-delen--fellesreglar-for-grunnskoleopplaringa-og-den-vidaregaande-opplaringa-for-barn-og-unge/kapittel-9-individuell-vurdering/v.-eksamen/-9-34-sarskild-tilrettelegging-av-eksamen/)

For centrally set examinations, Udir is introducing Secure Exam Browser more widely. Udir explains that candidates who require external reading and writing support programs can apply for special accommodation and, where appropriate, be exempted from the Secure Exam Browser requirement. Udir gives IntoWords and Lingdys as examples of such programs rather than presenting them as an exhaustive list of permitted products.

Current Udir guidance is available here:

- [Udir: Eksamensfag med sikker nettleser](https://www.udir.no/eksamen-og-prover/eksamen/slik-endrer-vi-eksamen/eksamensfag-med-sikker-nettleser/)
- [Udir: Administrere eksamen](https://www.udir.no/eksamen-og-prover/eksamen/administrere-eksamen/)

Any use of Skrivi during a formal examination would therefore be subject to the school or municipality approving the pupil’s individual examination accommodation and confirming that Skrivi is appropriate for that purpose.

## Skrivi Exam Mode

Skrivi is intended to include an especially restricted **Exam Mode**.

The aim is that Exam Mode provides only the functionality required for speech-to-text:

**Microphone → local speech recognition → literal transcription → text at the cursor.**

Exam Mode is intended not to provide:

- generative AI;
- answer generation;
- internet searches;
- summarisation;
- rewriting;
- translation;
- AI-assisted improvement of the pupil’s answer; or
- access to cloud-based language models.

The objective is to make it technically and pedagogically clear that Skrivi is an **input accessibility tool**, rather than an AI assistant.

## What we are asking the school to consider

At this stage, we would like the school to consider allowing the pupil to use Skrivi as an offline speech-to-text accessibility tool during appropriate everyday schoolwork.

This would allow the pupil, teachers, and school IT staff to evaluate whether it is useful and appropriate in practice.

If it becomes an established part of the pupil’s normal writing support, we would then like to discuss its use during appropriate assessments and, separately, its inclusion in any application for special accommodation during the pupil’s final examinations.

We are happy to provide the school with technical information about Skrivi, demonstrate that it operates without an internet connection, explain exactly what information it processes, and work with the school to address any privacy, security, or examination requirements before it is used.
