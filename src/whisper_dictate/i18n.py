from __future__ import annotations

# Translation keys deliberately retain complete English source sentences so a
# missing translation falls back safely and remains understandable.
# ruff: noqa: E501
import ctypes
import locale
import os
import weakref
from collections.abc import Callable
from enum import StrEnum


class InterfaceLanguage(StrEnum):
    AUTOMATIC = "auto"
    ENGLISH = "en"
    NORWEGIAN_BOKMAL = "nb"


NORWEGIAN_BOKMAL = {
    "Automatic (Windows display language)": "Automatisk (Windows-språk)",
    # Language choices identify themselves in every interface language.
    "English": "English",
    "Norwegian Bokmål": "Norsk bokmål",
    "Interface language": "Grensesnittspråk",
    "Interface language updates immediately.": (
        "Grensesnittspråket oppdateres umiddelbart."
    ),
    "Configure Skrivi and review its local privacy behaviour.": (
        "Konfigurer Skrivi og les om hvordan personvernet ivaretas lokalt."
    ),
    "Windows Default": "Windows-standard",
    "Right Ctrl": "Høyre Ctrl",
    "Left Ctrl + Windows": "Venstre Ctrl + Windows",
    "Left Ctrl + Left Alt": "Venstre Ctrl + Venstre Alt",
    "Settings": "Innstillinger",
    "Choose how Skrivi listens, looks and starts.": (
        "Velg hvordan Skrivi lytter, ser ut og starter."
    ),
    "Skrivi logo": "Skrivi-logo",
    "Ctrl+S saves changes": "Ctrl+S lagrer endringene",
    "{title} Settings": "Innstillinger for {title}",
    "Skrivi settings": "Skrivi-innstillinger",
    "Skrivi settings heading": "Overskrift for Skrivi-innstillinger",
    "Settings warning": "Advarsel om innstillinger",
    "Settings sections": "Deler av innstillingene",
    "General": "Generelt",
    "Models": "Modeller",
    "Privacy": "Personvern",
    "About": "Om Skrivi",
    "Save": "Lagre",
    "Cancel": "Avbryt",
    "Save settings": "Lagre innstillinger",
    "Cancel changes": "Avbryt endringer",
    "Settings actions": "Handlinger for innstillinger",
    "Current status": "Gjeldende status",
    "Starting": "Starter",
    "Current dictation status": "Gjeldende status for diktering",
    "Dictation": "Diktering",
    "Choose what Skrivi listens for and how you start speaking.": (
        "Velg hva Skrivi skal lytte etter, og hvordan du starter dikteringen."
    ),
    "Dictation setup": "Oppsett for diktering",
    "Dictation language": "Dikteringsspråk",
    "Language": "Språk",
    "Detects Norwegian or English for each dictation. Best for most people.": (
        "Oppdager norsk eller engelsk for hver diktering. Passer best for de fleste."
    ),
    "Always listens for English.": "Lytter alltid etter engelsk.",
    "Always listens for Norwegian.": "Lytter alltid etter norsk.",
    "Dictation language guidance": "Veiledning for dikteringsspråk",
    "Automatic": "Automatisk",
    "Norwegian": "Norsk",
    "Speech model": "Talemodell",
    "Speech model value": "Verdi for talemodell",
    "Models…": "Modeller …",
    "Manage speech models": "Administrer talemodeller",
    "Microphone": "Mikrofon",
    "Refresh": "Oppdater",
    "Refresh microphones": "Oppdater mikrofoner",
    "Microphone availability": "Mikrofontilgjengelighet",
    "Push-to-talk key": "Dikteringstast",
    "Push-to-talk key value": "Verdi for dikteringstast",
    "Change…": "Endre …",
    "Change push-to-talk key": "Endre dikteringstast",
    "Press this button, then press Right Ctrl, a supported two-key combination, or F6 through F12.": (
        "Trykk på denne knappen, og trykk deretter Høyre Ctrl, en støttet "
        "kombinasjon med to taster eller F6 til F12."
    ),
    "Finish the current recording before changing the push-to-talk key.": (
        "Fullfør det gjeldende opptaket før du endrer dikteringstasten."
    ),
    "Press a key or combination…": "Trykk på en tast eller kombinasjon …",
    "Press the second key…": "Trykk på den andre tasten …",
    "Waiting for a push-to-talk key": "Venter på en dikteringstast",
    "Use Right Ctrl, Left Ctrl + Windows, Left Ctrl + Left Alt, or F6 through F12.": (
        "Bruk Høyre Ctrl, Venstre Ctrl + Windows, Venstre Ctrl + Venstre Alt "
        "eller F6 til F12."
    ),
    "Release key…": "Slipp tasten …",
    "Release the selected push-to-talk key": "Slipp den valgte dikteringstasten",
    "Restore Default": "Gjenopprett standard",
    "Restore default push-to-talk key": "Gjenopprett standard dikteringstast",
    "Recommended for laptops: Left Ctrl + Windows. Right Ctrl and Left Ctrl + Left Alt also work. F6 through F12 can conflict with shortcuts in other apps.": (
        "Anbefalt på bærbare PC-er: Venstre Ctrl + Windows. Høyre Ctrl og "
        "Venstre Ctrl + Venstre Alt fungerer også. F6 til F12 kan komme i "
        "konflikt med snarveier i andre programmer."
    ),
    "Push-to-talk key guidance": "Veiledning for dikteringstast",
    "Appearance": "Utseende",
    "Application": "Programmet",
    "Choose how Skrivi looks and behaves when Windows starts.": (
        "Velg hvordan Skrivi ser ut og oppfører seg når Windows starter."
    ),
    "Show the compact status overlay while dictating": (
        "Vis det kompakte statusfeltet under diktering"
    ),
    "Show dictation status overlay": "Vis statusfelt for diktering",
    "Show a non-activating message while Skrivi loads, listens and transcribes.": (
        "Vis en melding uten å ta fokus mens Skrivi laster, lytter og transkriberer."
    ),
    "Startup": "Oppstart",
    "Start Skrivi automatically when I sign in": (
        "Start Skrivi automatisk når jeg logger på"
    ),
    "Start Skrivi automatically": "Start Skrivi automatisk",
    "Automatic startup guidance": "Veiledning for automatisk oppstart",
    "Skrivi starts quietly in the system tray. Keep a portable copy in a permanent folder while this is enabled.": (
        "Skrivi starter stille i systemstatusfeltet. Oppbevar en portabel kopi i "
        "en permanent mappe mens dette er aktivert."
    ),
    "Automatic startup is available in packaged Skrivi builds.": (
        "Automatisk oppstart er tilgjengelig i pakkede Skrivi-versjoner."
    ),
    "Automatic startup is unavailable in this Skrivi build.": (
        "Automatisk oppstart er ikke tilgjengelig i denne Skrivi-versjonen."
    ),
    "Skrivi could not read Windows startup settings.": (
        "Skrivi kunne ikke lese oppstartsinnstillingene i Windows."
    ),
    "Skrivi could not change Windows startup settings.": (
        "Skrivi kunne ikke endre oppstartsinnstillingene i Windows."
    ),
    "Speech is processed locally on this PC. Skrivi does not save your recordings or transcripts, does not use the clipboard for dictated text, and needs no account. After the selected speech model has been downloaded, normal dictation does not require internet access.": (
        "Tale behandles lokalt på denne PC-en. Skrivi lagrer ikke opptak eller "
        "transkripsjoner, bruker ikke utklippstavlen for diktert tekst og krever "
        "ingen konto. Etter at den valgte talemodellen er lastet ned, krever "
        "vanlig diktering ingen internettilgang."
    ),
    "Skrivi privacy summary": "Sammendrag av personvernet i Skrivi",
    "Your words stay yours.": "Ordene dine forblir dine.",
    "Skrivi is designed to turn your speech into text without creating an account or sending your dictation to us.": (
        "Skrivi er laget for å gjøre tale om til tekst uten konto og uten å sende dikteringen til oss."
    ),
    "Processed on this PC": "Behandles på denne PC-en",
    "Your recording is transcribed locally by the speech model installed on this computer.": (
        "Opptaket transkriberes lokalt av talemodellen som er installert på denne datamaskinen."
    ),
    "Nothing saved by Skrivi": "Ingenting lagres av Skrivi",
    "Skrivi does not keep a history of recordings or dictated text.": (
        "Skrivi lagrer ingen historikk over opptak eller diktert tekst."
    ),
    "No account or clipboard": "Ingen konto eller utklippstavle",
    "You do not sign in, and dictated text is inserted without using the Windows clipboard.": (
        "Du logger ikke inn, og diktert tekst settes inn uten å bruke utklippstavlen i Windows."
    ),
    "Works offline after setup": "Fungerer uten nett etter oppsett",
    "Internet is needed to download a speech model. Installed models work without it.": (
        "Internett trengs for å laste ned en talemodell. Installerte modeller fungerer uten nett."
    ),
    "One important boundary": "Én viktig avgrensning",
    "The app receiving your text, such as Word, a browser or a school platform, may save or sync it according to that app's own settings.": (
        "Programmet som mottar teksten, for eksempel Word, en nettleser eller en skoleplattform, kan lagre eller synkronisere den etter sine egne innstillinger."
    ),
    "Read full privacy details": "Les alle personverndetaljene",
    "Open privacy documentation": "Åpne personverndokumentasjonen",
    "Skrivi is free and open-source local speech-to-text software.\n\nThe interface uses PySide6 and Qt under their open-source licences. See THIRD_PARTY_NOTICES.md included with Skrivi for copyright and licence information.": (
        "Skrivi er gratis lokal tale-til-tekst-programvare med åpen kildekode.\n\n"
        "Grensesnittet bruker PySide6 og Qt under deres åpne lisenser. Se "
        "THIRD_PARTY_NOTICES.md som følger med Skrivi, for informasjon om "
        "opphavsrett og lisenser."
    ),
    "About Skrivi": "Om Skrivi",
    "Get your thoughts onto the page.": "Få tankene dine ned på siden.",
    "Skrivi version": "Skrivi-versjon",
    "Free, local and open source": "Gratis, lokal og med åpen kildekode",
    "Skrivi is a small speech-to-text tool. It transcribes your own words locally and does not generate answers or rewrite what you say.": (
        "Skrivi er et lite tale-til-tekst-verktøy. Det transkriberer ordene dine lokalt og verken lager svar eller omskriver det du sier."
    ),
    "Learn more": "Finn ut mer",
    "Open documentation in your web browser.": "Åpne dokumentasjon i nettleseren.",
    "Website": "Nettsted",
    "Open Skrivi website": "Åpne Skrivi-nettstedet",
    "Source code": "Kildekode",
    "Open Skrivi source code": "Åpne kildekoden til Skrivi",
    "Third-party licences": "Tredjepartslisenser",
    "Open third-party licence notices": "Åpne lisensmerknader for tredjeparter",
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
    "Skrivi could not apply settings safely. Previous settings remain active.": (
        "Skrivi kunne ikke bruke innstillingene på en trygg måte. De forrige "
        "innstillingene er fortsatt aktive."
    ),
    "Skrivi tray menu": "Skrivi-meny i systemstatusfeltet",
    "Status: {text}": "Status: {text}",
    "Open Skrivi settings": "Åpne Skrivi-innstillingene",
    "Retry speech model": "Prøv talemodellen på nytt",
    "Try loading the selected local speech model again": (
        "Prøv å laste den valgte lokale talemodellen på nytt"
    ),
    "Preview state": "Forhåndsvis status",
    "Exit": "Avslutt",
    "Preparing local speech model…": "Klargjør lokal talemodell …",
    "Ready. Hold {hotkey} to dictate": "Klar. Hold {hotkey} for å diktere",
    "Listening. Release your dictation key, or press Esc to cancel": (
        "Lytter. Slipp dikteringstasten, eller trykk Esc for å avbryte"
    ),
    "Transcribing locally…": "Transkriberer lokalt …",
    "Dictation cancelled": "Diktering avbrutt",
    "No speech detected": "Ingen tale oppdaget",
    "Speech model unavailable": "Talemodellen er ikke tilgjengelig",
    "Something went wrong": "Noe gikk galt",
    "Skrivi dictation status": "Status for Skrivi-diktering",
    "Shows whether Skrivi is loading, listening, or transcribing.": (
        "Viser om Skrivi laster, lytter eller transkriberer."
    ),
    "Status symbol": "Statussymbol",
    "Dictation status message": "Statusmelding for diktering",
    "Speech model unavailable. Choose Retry speech model from the tray, or open Settings → Models.": (
        "Talemodellen er ikke tilgjengelig. Velg Prøv talemodellen på nytt i "
        "systemstatusfeltet, eller åpne Innstillinger → Modeller."
    ),
    "Retrying local speech model…": "Prøver lokal talemodell på nytt …",
    "The microphone could not start. Check Skrivi Settings.": (
        "Mikrofonen kunne ikke starte. Kontroller Skrivi-innstillingene."
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
    "Settings were written by a newer Skrivi version; safe defaults are in use.": (
        "Innstillingene ble skrevet av en nyere Skrivi-versjon. Trygge standardverdier brukes."
    ),
    "Skrivi could not save settings safely": "Skrivi kunne ikke lagre innstillingene trygt",
    "Skrivi is already running.": "Skrivi kjører allerede.",
    "Skrivi runs on Windows 11.": "Skrivi kjører på Windows 11.",
    "Local speech models": "Lokale talemodeller",
    "Speech models": "Talemodeller",
    "Choose the balance between speed and accuracy. Models are stored on this PC and work offline after download.": (
        "Velg balansen mellom hastighet og nøyaktighet. Modellene lagres på denne PC-en og fungerer uten nett etter nedlasting."
    ),
    "Choose a model": "Velg en modell",
    "Model": "Modell",
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
    "Download model": "Last ned modell",
    "Download selected model": "Last ned valgt modell",
    "Use model": "Bruk modell",
    "Use this model": "Bruk denne modellen",
    "Use selected speech model": "Bruk valgt talemodell",
    "Remove": "Fjern",
    "Remove from this PC": "Fjern fra denne PC-en",
    "Remove selected model": "Fjern valgt modell",
    "Import folder…": "Importer mappe …",
    "Already have a model?": "Har du allerede en modell?",
    "Import a verified Skrivi model folder copied from another computer.": (
        "Importer en verifisert Skrivi-modellmappe som er kopiert fra en annen datamaskin."
    ),
    "Choose model folder…": "Velg modellmappe …",
    "Import a Skrivi model folder": "Importer en Skrivi-modellmappe",
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
    "Choose a Skrivi model folder": "Velg en Skrivi-modellmappe",
    "{name} is intended for PCs with at least {minimum} GB of RAM. This PC reports {actual:.1f} GB.": (
        "{name} er beregnet for PC-er med minst {minimum} GB minne. Denne PC-en "
        "rapporterer {actual:.1f} GB."
    ),
    "{name} is likely to transcribe slowly on a CPU. Small is the recommended model for typical PCs.": (
        "{name} vil sannsynligvis transkribere sakte på en prosessor. Small er "
        "den anbefalte modellen for vanlige PC-er."
    ),
    "That model is not in Skrivi's catalogue.": (
        "Denne modellen finnes ikke i Skrivis katalog."
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
    "Skrivi is shutting down. No new model operation can start.": (
        "Skrivi avsluttes. Ingen ny modellhandling kan startes."
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
    "That folder is not a complete Skrivi model export.": (
        "Denne mappen er ikke en fullstendig Skrivi-modelleksport."
    ),
    "That model does not match Skrivi's trusted catalogue.": (
        "Denne modellen samsvarer ikke med Skrivis godkjente katalog."
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
    "Wait until Skrivi is ready before changing the speech model.": (
        "Vent til Skrivi er klar før du endrer talemodellen."
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
    "Unsupported key": "Tasten støttes ikke",
    "That push-to-talk key could not be activated. The previous key has been restored where possible.": (
        "Dikteringstasten kunne ikke aktiveres. Den forrige tasten er "
        "gjenopprettet der det var mulig."
    ),
}


_active_language = InterfaceLanguage.ENGLISH
_language_listeners: list[weakref.ReferenceType] = []


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
    resolved = resolve_interface_language(choice)
    if resolved is _active_language:
        return _active_language
    _active_language = resolved
    live_listeners = []
    for listener_reference in _language_listeners:
        listener = listener_reference()
        if listener is None:
            continue
        live_listeners.append(listener_reference)
        listener()
    _language_listeners[:] = live_listeners
    return _active_language


def add_interface_language_listener(listener: Callable[[], None]) -> None:
    try:
        reference = weakref.WeakMethod(listener)
    except TypeError:
        reference = weakref.ref(listener)
    _language_listeners.append(reference)


def current_interface_language() -> InterfaceLanguage:
    return _active_language


def tr(text: str, /, **values: object) -> str:
    template = (
        NORWEGIAN_BOKMAL.get(text, text)
        if _active_language is InterfaceLanguage.NORWEGIAN_BOKMAL
        else text
    )
    return template.format(**values) if values else template
