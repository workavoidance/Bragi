(() => {
  const button = document.querySelector('.language-switch');
  if (!button) return;

  const screenshotStyles = document.createElement('link');
  screenshotStyles.rel = 'stylesheet';
  screenshotStyles.href = 'screenshots.css';
  document.head.appendChild(screenshotStyles);

  const playSection = document.querySelector('#play');
  const settingsGrid = playSection?.querySelector('.settings-grid');
  if (playSection && settingsGrid) {
    const walkthrough = document.createElement('div');
    walkthrough.className = 'walkthrough-grid';
    walkthrough.setAttribute('aria-label', 'Slik finner og åpner du Skrivi-innstillinger');
    walkthrough.dataset.ariaNb = 'Slik finner og åpner du Skrivi-innstillinger';
    walkthrough.dataset.ariaEn = 'How to find and open Skrivi settings';
    walkthrough.innerHTML = `
      <figure class="walkthrough-card walkthrough-card-tray">
        <div class="walkthrough-image-frame walkthrough-image-frame-tray">
          <img
            src="assets/tray-settings.webp"
            alt="Skrivi-menyen i systemstatusfeltet med Innstillinger markert"
            data-alt-nb="Skrivi-menyen i systemstatusfeltet med Innstillinger markert"
            data-alt-en="Skrivi tray menu with Settings highlighted"
            width="418"
            height="331"
            loading="lazy"
          >
        </div>
        <figcaption>
          <span class="walkthrough-step">01</span>
          <div>
            <strong data-nb="Finn Skrivi og åpne Innstillinger" data-en="Find Skrivi and open Settings">Finn Skrivi og åpne Innstillinger</strong>
            <p data-nb="Finn Skrivi-ikonet ved klokken. Klikk på det og velg «Innstillinger …»." data-en="Find the Skrivi icon by the clock. Click it and choose “Settings…”.">Finn Skrivi-ikonet ved klokken. Klikk på det og velg «Innstillinger …».</p>
          </div>
        </figcaption>
      </figure>

      <figure class="walkthrough-card walkthrough-card-settings">
        <div class="walkthrough-image-frame walkthrough-image-frame-settings">
          <img
            src="assets/settings-window.webp"
            alt="Skrivi-innstillinger med språk, talemodell, mikrofon og dikteringstast"
            data-alt-nb="Skrivi-innstillinger med språk, talemodell, mikrofon og dikteringstast"
            data-alt-en="Skrivi settings showing language, speech model, microphone and dictation key"
            width="520"
            height="639"
            loading="lazy"
          >
        </div>
        <figcaption>
          <span class="walkthrough-step">02</span>
          <div>
            <strong data-nb="Prøv språk og modell" data-en="Try languages and models">Prøv språk og modell</strong>
            <p data-nb="Start med Automatisk og Small. Hvis språket velges feil, prøv fast Norsk eller English. Hvis Skrivi føles tregt, åpne «Modeller …» og prøv Base." data-en="Start with Automatic and Small. If the wrong language is chosen, try fixed Norwegian or English. If Skrivi feels slow, open “Models…” and try Base.">Start med Automatisk og Small. Hvis språket velges feil, prøv fast Norsk eller English. Hvis Skrivi føles tregt, åpne «Modeller …» og prøv Base.</p>
          </div>
        </figcaption>
      </figure>
    `;
    settingsGrid.before(walkthrough);
  }

  const setLanguage = (language) => {
    const norwegian = language === 'nb';
    document.documentElement.lang = norwegian ? 'nb' : 'en';

    document.querySelectorAll('[data-nb][data-en]').forEach((element) => {
      element.textContent = norwegian ? element.dataset.nb : element.dataset.en;
    });

    document.querySelectorAll('[data-aria-nb][data-aria-en]').forEach((element) => {
      element.setAttribute(
        'aria-label',
        norwegian ? element.dataset.ariaNb : element.dataset.ariaEn,
      );
    });

    document.querySelectorAll('[data-alt-nb][data-alt-en]').forEach((element) => {
      element.setAttribute('alt', norwegian ? element.dataset.altNb : element.dataset.altEn);
    });

    document.querySelectorAll('[data-href-nb][data-href-en]').forEach((element) => {
      element.href = norwegian ? element.dataset.hrefNb : element.dataset.hrefEn;
    });

    const description = document.querySelector('meta[name="description"]');
    if (description) {
      description.content = norwegian
        ? 'Hjelp oss å teste Skrivi. En enkel guide til installasjon, utprøving og tilbakemelding for tidlige testfamilier.'
        : 'Help us test Skrivi. A simple guide to installing, trying and giving feedback for early test families.';
    }

    button.textContent = norwegian ? 'EN' : 'NO';
    button.setAttribute('aria-label', norwegian ? 'Switch to English' : 'Bytt til norsk');
    button.setAttribute('aria-pressed', norwegian ? 'false' : 'true');
    document.title = 'Test Skrivi — alpha';
  };

  button.addEventListener('click', () => {
    setLanguage(document.documentElement.lang === 'nb' ? 'en' : 'nb');
  });

  setLanguage('nb');
})();
