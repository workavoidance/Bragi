from __future__ import annotations

# Translation keys deliberately retain complete English source sentences so a
# missing translation falls back safely and remains understandable.
# ruff: noqa: E501
import ctypes
import locale
import os
from enum import StrEnum


class InterfaceLanguage(StrEnum):
    AUTOMATIC = "auto"
    ENGLISH = "en"
    NORWEGIAN_BOKMAL = "nb"


NORWEGIAN_BOKMAL = {
    "Automatic (Windows display language)": "Automatisk (Windows-språk)",
    "English": "Engelsk",
    "Norwegian Bokmål": "Norsk bokmål",
    "Interface language": "Grensesnittspråk",
    "Interface language changes after Bragi restarts.": (
        "Grensesnittspråket endres etter at Bragi er startet på nytt."
    ),
    "Configure Bragi and review its local privacy behaviour.": (
        "Konfigurer Bragi og les om hvordan personvernet ivaretas lokalt."
    ),
    "Windows Default": "Windows-standard",
    "Right Ctrl": "Høyre Ctrl",
    "Settings": "Innstillinger",
    "{title} Settings": "Innstillinger for {title}",
    "Bragi settings": "Bragi-innstillinger",
    "Bragi settings heading": "Overskrift for Bragi-innstillinger",
    "Settings warning": "Advarsel om innstillinger",
    "Settings sections": "Deler av innstillingene",
    "General": "Generelt",
    "Models": "Modeller",
    "Privacy": "Personvern",
    "About": "Om Bragi",
    "Save": "Lagre",
    "Cancel": "Avbryt",
    "Save settings": "Lagre innstillinger",
    "Cancel changes": "Avbryt endringer",
    "Settings actions": "Handlinger for innstillinger",
    "Current status": "Gjeldende status",
    "Starting": "Starter",
    "Current dictation status": "Gjeldende status for diktering",
    "Dictation setup": "Oppsett for diktering",
    "Dictation language": "Dikteringsspråk",
    "Language": "Språk",
    "Automatic": "Automatisk",
    "Norwegian": "Norsk",
    "Multilingual": "Flerspråklig",
    "Automatic detects one language per recording and works best with a complete phrase. Multilingual can detect language again within a recording.": (
        "Automatisk oppdager ett språk per opptak og fungerer best med en hel "
        "setning. Flerspråklig kan oppdage språket på nytt i samme opptak."
    ),
    "Speech model": "Talemodell",
    "Speech model value": "Verdi for talemodell",
    "Microphone": "Mikrofon",
    "Refresh": "Oppdater",
    "Refresh microphones": "Oppdater mikrofoner",
    "Microphone availability": "Mikrofontilgjengelighet",
    "Push-to-talk key": "Dikteringstast",
    "Push-to-talk key value": "Verdi for dikteringstast",
    "Change…": "Endre …",
    "Change push-to-talk key": "Endre dikteringstast",
    "Press this button, then press Right Ctrl or F6 through F12.": (
        "Trykk på denne knappen, og trykk deretter Høyre Ctrl eller F6 til F12."
    ),
    "Finish the current recording before changing the push-to-talk key.": (
        "Fullfør det gjeldende opptaket før du endrer dikteringstasten."
    ),
    "Press a key…": "Trykk på en tast …",
    "Waiting for a push-to-talk key": "Venter på en dikteringstast",
    "Use Right Ctrl or F6 through F12. Letters, Windows keys, and common editing keys are not safe choices.": (
        "Bruk Høyre Ctrl eller F6 til F12. Bokstaver, Windows-taster og vanlige "
        "redigeringstaster er ikke trygge valg."
    ),
    "Release key…": "Slipp tasten …",
    "Release the selected push-to-talk key": "Slipp den valgte dikteringstasten",
    "Restore Default": "Gjenopprett standard",
    "Restore default push-to-talk key": "Gjenopprett standard dikteringstast",
    "Safe choices are Right Ctrl and F6 through F12. Press Escape to cancel key capture.": (
        "Trygge valg er Høyre Ctrl og F6 til F12. Trykk Escape for å avbryte "
        "tastregistreringen."
    ),
    "Push-to-talk key guidance": "Veiledning for dikteringstast",
    "Appearance": "Utseende",
    "Show the compact status overlay while dictating": (
        "Vis det kompakte statusfeltet under diktering"
    ),
    "Show dictation status overlay": "Vis statusfelt for diktering",
    "Show a non-activating message while Bragi loads, listens and transcribes.": (
        "Vis en melding uten å ta fokus mens Bragi laster, lytter og transkriberer."
    ),
    "Speech is processed locally on this PC. Bragi does not save your recordings or transcripts, does not use the clipboard for dictated text, and needs no account. After the selected speech model has been downloaded, normal dictation does not require internet access.": (
        "Tale behandles lokalt på denne PC-en. Bragi lagrer ikke opptak eller "
        "transkripsjoner, bruker ikke utklippstavlen for diktert tekst og krever "
        "ingen konto. Etter at den valgte talemodellen er lastet ned, krever "
        "vanlig diktering ingen internettilgang."
    ),
    "Bragi privacy summary": "Sammendrag av personvernet i Bragi",
    "Bragi is free and open-source local speech-to-text software.\n\nThe interface uses PySide6 and Qt under their open-source licences. See THIRD_PARTY_NOTICES.md included with Bragi for copyright and licence information.": (
        "Bragi er gratis lokal tale-til-tekst-programvare med åpen kildekode.\n\n"
        "Grensesnittet bruker PySide6 og Qt under deres åpne lisenser. Se "
        "THIRD_PARTY_NOTICES.md som følger med Bragi, for informasjon om "
        "opphavsrett og lisenser."
    ),
    "About Bragi": "Om Bragi",
    "Microphones could not be listed. Check Windows Sound settings or use Windows Default.": (
        "Mikrofonene kunne ikke vises. Kontroller lydinnstillingene i Windows, "
        "eller bruk Windows-standard."
    ),
    "Unavailable: {name}": "Ikke tilgjengelig: {name}",
    "The saved microphone is disconnected. Choose another microphone or Windows Default before saving.": (
        "Den lagrede mikrofonen er frakoblet. Velg en annen mikrofon eller "
        "Windows-standard før du lagrer."
    ),
    "Settings could not be applied": "Innstillingene kunne ikke tas i bruk",
    "Bragi could not apply settings safely. Previous settings remain active.": (
        "Bragi kunne ikke bruke innstillingene på en trygg måte. De forrige "
        "innstillingene er fortsatt aktive."
    ),
    "Bragi tray menu": "Bragi-meny i systemstatusfeltet",
    "Status: {text}": "Status: {text}",
    "Open Bragi settings": "Åpne Bragi-innstillingene",
    "Retry speech model": "Prøv talemodellen på nytt",
    "Try loading the selected local speech model again": (
        "Prøv å laste den valgte lokale talemodellen på nytt"
    ),
    "Preview state": "Forhåndsvis status",
    "Exit": "Avslutt",
    "Preparing local speech model…": "Klargjør lokal talemodell …",
    "Ready. Hold Right Ctrl to dictate": "Klar. Hold Høyre Ctrl for å diktere",
    "Listening. Release your dictation key, or press Esc to cancel": (
        "Lytter. Slipp dikteringstasten, eller trykk Esc for å avbryte"
    ),
    "Transcribing locally…": "Transkriberer lokalt …",
    "Dictation cancelled": "Diktering avbrutt",
    "No speech detected": "Ingen tale oppdaget",
    "Speech model unavailable": "Talemodellen er ikke tilgjengelig",
    "Something went wrong": "Noe gikk galt",
    "Bragi dictation status": "Status for Bragi-diktering",
    "Shows whether Bragi is loading, listening, or transcribing.": (
        "Viser om Bragi laster, lytter eller transkriberer."
    ),
    "Status symbol": "Statussymbol",
    "Dictation status message": "Statusmelding for diktering",
    "Speech model unavailable. Choose Retry speech model from the tray, or open Settings → Models.": (
        "Talemodellen er ikke tilgjengelig. Velg Prøv talemodellen på nytt i "
        "systemstatusfeltet, eller åpne Innstillinger → Modeller."
    ),
    "Retrying local speech model…": "Prøver lokal talemodell på nytt …",
    "The microphone could not start. Check Bragi Settings.": (
        "Mikrofonen kunne ikke starte. Kontroller Bragi-innstillingene."
    ),
    "Selected microphone unavailable. Using Windows Default temporarily. Release your dictation key, or press Esc to cancel.": (
        "Den valgte mikrofonen er ikke tilgjengelig. Bruker Windows-standard "
        "midlertidig. Slipp dikteringstasten, eller trykk Esc for å avbryte."
    ),
    "Recording cancelled after 5 minutes. Hold the key again to start over.": (
        "Opptaket ble avbrutt etter 5 minutter. Hold tasten igjen for å starte på nytt."
    ),
    "Could not cancel microphone recording": "Kunne ikke avbryte mikrofonopptaket",
    "Could not finish microphone recording": "Kunne ikke fullføre mikrofonopptaket",
    "Phrase too short. Automatic language detection works better with a longer phrase.": (
        "Uttrykket er for kort. Automatisk språkgjenkjenning fungerer bedre med "
        "en lengre setning."
    ),
    "Transcription failed. Audio was discarded; hold the key to try again.": (
        "Transkriberingen mislyktes. Lyden ble forkastet. Hold tasten for å prøve igjen."
    ),
    "Settings are damaged; safe defaults are in use.": (
        "Innstillingene er skadet. Trygge standardverdier brukes."
    ),
    "Settings could not be read; safe defaults are in use.": (
        "Innstillingene kunne ikke leses. Trygge standardverdier brukes."
    ),
    "Settings contain unsupported values; safe defaults are in use.": (
        "Innstillingene inneholder verdier som ikke støttes. Trygge standardverdier brukes."
    ),
    "Settings were written by a newer Bragi version; safe defaults are in use.": (
        "Innstillingene ble skrevet av en nyere Bragi-versjon. Trygge standardverdier brukes."
    ),
    "Bragi could not save settings safely": "Bragi kunne ikke lagre innstillingene trygt",
    "Bragi is already running.": "Bragi kjører allerede.",
    "Bragi runs on Windows 11.": "Bragi kjører på Windows 11.",
    "Local speech models": "Lokale talemodeller",
    "Speech models are installed on this PC. Downloading a new model uses the internet only when you request it. Installed models work without an internet connection.": (
        "Talemodeller installeres på denne PC-en. Internett brukes bare når du "
        "ber om å laste ned en ny modell. Installerte modeller fungerer uten "
        "internettforbindelse."
    ),
    "Model privacy and download explanation": (
        "Forklaring av personvern og nedlasting for modeller"
    ),
    "{name} (recommended)": "{name} (anbefalt)",
    "Selected model details": "Detaljer om valgt modell",
    "Selected model status": "Status for valgt modell",
    "Model operation progress": "Fremdrift for modellhandling",
    "Download": "Last ned",
    "Download selected model": "Last ned valgt modell",
    "Use model": "Bruk modell",
    "Use selected speech model": "Bruk valgt talemodell",
    "Remove": "Fjern",
    "Remove selected model": "Fjern valgt modell",
    "Import folder…": "Importer mappe …",
    "Import a Bragi model folder": "Importer en Bragi-modellmappe",
    "Cancel download": "Avbryt nedlasting",
    "Cancel model download": "Avbryt modellnedlasting",
    "Model actions are disabled in interface preview mode.": (
        "Modellhandlinger er deaktivert i forhåndsvisningen av grensesnittet."
    ),
    " Detected RAM: {memory:.1f} GB.": " Oppdaget minne: {memory:.1f} GB.",
    "Fastest response, with the lowest transcription accuracy.": (
        "Raskest respons, men lavest transkripsjonsnøyaktighet."
    ),
    "Faster on a CPU, with lower accuracy than Small.": (
        "Raskere på en prosessor, men mindre nøyaktig enn Small."
    ),
    "Recommended balance of Norwegian accuracy and CPU speed.": (
        "Anbefalt balanse mellom nøyaktighet på norsk og prosessorhastighet."
    ),
    "Potentially more accurate, but often impractical on a CPU.": (
        "Kan være mer nøyaktig, men er ofte upraktisk på en prosessor."
    ),
    "Download: {size}.": "Nedlasting: {size}.",
    "RAM guidance: {memory} GB or more.": "Anbefalt minne: {memory} GB eller mer.",
    "CPU suitability: {suitability}.{ram}": (
        "Egnethet for prosessor: {suitability}.{ram}"
    ),
    "fastest": "raskest",
    "faster": "raskere",
    "recommended": "anbefalt",
    "slow": "treg",
    "Installed and active": "Installert og aktiv",
    "Installed": "Installert",
    "Not installed. Download requires an internet connection.": (
        "Ikke installert. Nedlasting krever internettforbindelse."
    ),
    "This model may be slow": "Denne modellen kan være treg",
    "Do you want to continue?": "Vil du fortsette?",
    "Yes": "Ja",
    "No": "Nei",
    "Working locally…": "Arbeider lokalt …",
    "The model operation failed safely. The previous model remains active.": (
        "Modellhandlingen mislyktes på en trygg måte. Den forrige modellen er "
        "fortsatt aktiv."
    ),
    "Verifying": "Kontrollerer",
    "Downloading": "Laster ned",
    "Loading {name} locally…": "Laster {name} lokalt …",
    "{stage} {name}: {completed:.0f} MB of {total:.0f} MB ({percent}%)": (
        "{stage} {name}: {completed:.0f} MB av {total:.0f} MB ({percent} %)"
    ),
    "{stage} {name}…": "{stage} {name} …",
    "Model operation failed": "Modellhandlingen mislyktes",
    "Model download cancelled.": "Modellnedlastingen ble avbrutt.",
    "Cancelling model download…": "Avbryter modellnedlastingen …",
    "Cancelling…": "Avbryter …",
    "Remove local speech model": "Fjern lokal talemodell",
    "Remove {name} from this PC? It can be downloaded again later.": (
        "Vil du fjerne {name} fra denne PC-en? Den kan lastes ned igjen senere."
    ),
    "Choose a Bragi model folder": "Velg en Bragi-modellmappe",
    "{name} is intended for PCs with at least {minimum} GB of RAM. This PC reports {actual:.1f} GB.": (
        "{name} er beregnet for PC-er med minst {minimum} GB minne. Denne PC-en "
        "rapporterer {actual:.1f} GB."
    ),
    "{name} is likely to transcribe slowly on a CPU. Small is the recommended model for typical PCs.": (
        "{name} vil sannsynligvis transkribere sakte på en prosessor. Small er "
        "den anbefalte modellen for vanlige PC-er."
    ),
    "That model is not in Bragi's catalogue.": (
        "Denne modellen finnes ikke i Bragis katalog."
    ),
    "{name} is incomplete. Download or import it again.": (
        "{name} er ufullstendig. Last ned eller importer modellen på nytt."
    ),
    "{name} did not pass integrity verification. Download or import it again.": (
        "{name} bestod ikke integritetskontrollen. Last ned eller importer "
        "modellen på nytt."
    ),
    "{name} is not completely installed on this PC.": (
        "{name} er ikke fullstendig installert på denne PC-en."
    ),
    "Bragi is shutting down. No new model operation can start.": (
        "Bragi avsluttes. Ingen ny modellhandling kan startes."
    ),
    "Finish the current model operation before starting another.": (
        "Fullfør den gjeldende modellhandlingen før du starter en ny."
    ),
    "Downloading {name} from the internet…": "Laster ned {name} fra internett …",
    "Downloading {name}…": "Laster ned {name} …",
    "Verifying {name}…": "Kontrollerer {name} …",
    "{name} is installed.": "{name} er installert.",
    "{name} download cancelled. No model files were installed.": (
        "Nedlastingen av {name} ble avbrutt. Ingen modellfiler ble installert."
    ),
    "{name} could not be installed safely.": (
        "{name} kunne ikke installeres på en trygg måte."
    ),
    "{name} could not be downloaded. Check the internet connection and try again.": (
        "{name} kunne ikke lastes ned. Kontroller internettforbindelsen og prøv igjen."
    ),
    "That folder is not a complete Bragi model export.": (
        "Denne mappen er ikke en fullstendig Bragi-modelleksport."
    ),
    "That model does not match Bragi's trusted catalogue.": (
        "Denne modellen samsvarer ikke med Bragis godkjente katalog."
    ),
    "Checking imported {name} files…": "Kontrollerer importerte {name}-filer …",
    "Model import cancelled.": "Modellimporten ble avbrutt.",
    "{name} was imported.": "{name} ble importert.",
    "{name} import cancelled. No model files were installed.": (
        "Importen av {name} ble avbrutt. Ingen modellfiler ble installert."
    ),
    "{name} could not be imported safely.": (
        "{name} kunne ikke importeres på en trygg måte."
    ),
    "The imported model is incomplete or damaged.": (
        "Den importerte modellen er ufullstendig eller skadet."
    ),
    "{name} is currently active. Select another model first.": (
        "{name} er aktiv nå. Velg en annen modell først."
    ),
    "{name} was removed.": "{name} ble fjernet.",
    "Unknown microphone": "Ukjent mikrofon",
    "Windows Default microphone is unavailable. Check Windows Sound settings.": (
        "Windows-standardmikrofonen er ikke tilgjengelig. Kontroller "
        "lydinnstillingene i Windows."
    ),
    "Microphones could not be checked. Try Windows Default or reconnect the device.": (
        "Mikrofonene kunne ikke kontrolleres. Prøv Windows-standard, eller koble "
        "til enheten på nytt."
    ),
    "The selected microphone is unavailable. Open Settings and choose another microphone or Windows Default.": (
        "Den valgte mikrofonen er ikke tilgjengelig. Åpne Innstillinger og velg "
        "en annen mikrofon eller Windows-standard."
    ),
    "The selected microphone reported an invalid sample rate. Choose another microphone in Settings.": (
        "Den valgte mikrofonen rapporterte en ugyldig samplingsfrekvens. Velg en "
        "annen mikrofon i Innstillinger."
    ),
    "The microphone could not start. Check Windows Sound settings.": (
        "Mikrofonen kunne ikke starte. Kontroller lydinnstillingene i Windows."
    ),
    "The microphone was disconnected. This recording was discarded; try dictating again.": (
        "Mikrofonen ble koblet fra. Opptaket ble forkastet. Prøv å diktere på nytt."
    ),
    "Finish the current recording before changing the microphone or push-to-talk key.": (
        "Fullfør det gjeldende opptaket før du endrer mikrofon eller dikteringstast."
    ),
    "Wait until Bragi is ready before changing the speech model.": (
        "Vent til Bragi er klar før du endrer talemodellen."
    ),
    "{name} could not be loaded. The previous model is still active.": (
        "{name} kunne ikke lastes. Den forrige modellen er fortsatt aktiv."
    ),
    "{name} is active.": "{name} er aktiv.",
    "Loading": "Laster",
    "Ready": "Klar",
    "Recording": "Tar opp",
    "Transcribing": "Transkriberer",
    "No speech": "Ingen tale",
    "Error": "Feil",
    "Preview error: no user data was involved": (
        "Forhåndsvisningsfeil: ingen brukerdata var involvert"
    ),
    "Preview ready — choose a state from the tray icon": (
        "Forhåndsvisningen er klar. Velg en status fra ikonet i systemstatusfeltet"
    ),
    "Use Right Ctrl or F6 through F12. Letters, Windows keys, and common editing keys are not safe push-to-talk choices.": (
        "Bruk Høyre Ctrl eller F6 til F12. Bokstaver, Windows-taster og vanlige "
        "redigeringstaster er ikke trygge valg som dikteringstast."
    ),
    "Unsupported key": "Tasten støttes ikke",
    "That push-to-talk key could not be activated. The previous key has been restored where possible.": (
        "Dikteringstasten kunne ikke aktiveres. Den forrige tasten er "
        "gjenopprettet der det var mulig."
    ),
}


_active_language = InterfaceLanguage.ENGLISH


def interface_language_from_locale(language_name: str) -> InterfaceLanguage:
    prefix = language_name.replace("-", "_").lower().split("_", 1)[0]
    if prefix in {"nb", "nn", "no"}:
        return InterfaceLanguage.NORWEGIAN_BOKMAL
    return InterfaceLanguage.ENGLISH


def detect_windows_interface_language() -> InterfaceLanguage:
    """Return the supported language closest to the Windows display language."""
    language_name = ""
    if os.name == "nt":
        try:
            language_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            language_name = locale.windows_locale.get(language_id, "")
        except AttributeError:
            language_name = ""
        except OSError:
            language_name = ""
    if not language_name:
        language_name = locale.getlocale()[0] or ""
    return interface_language_from_locale(language_name)


def resolve_interface_language(
    choice: InterfaceLanguage,
) -> InterfaceLanguage:
    if choice is InterfaceLanguage.AUTOMATIC:
        return detect_windows_interface_language()
    return choice


def set_interface_language(choice: InterfaceLanguage) -> InterfaceLanguage:
    global _active_language
    _active_language = resolve_interface_language(choice)
    return _active_language


def current_interface_language() -> InterfaceLanguage:
    return _active_language


def tr(text: str, /, **values: object) -> str:
    template = (
        NORWEGIAN_BOKMAL.get(text, text)
        if _active_language is InterfaceLanguage.NORWEGIAN_BOKMAL
        else text
    )
    return template.format(**values) if values else template
