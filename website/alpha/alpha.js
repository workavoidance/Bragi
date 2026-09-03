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
        <div class="walkthrough-settings-map">
          <div class="settings-map-title" data-nb="Innstillinger" data-en="Settings">Innstillinger</div>
          <div class="settings-map-section">
            <span data-nb="Språk" data-en="Language">Språk</span>
            <strong data-nb="Automatisk ▾" data-en="Automatic ▾">Automatisk ▾</strong>
          </div>
          <p data-nb="Hvis automatisk velger feil, prøv fast Norsk eller English." data-en="If automatic chooses the wrong language, try fixed Norwegian or English.">Hvis automatisk velger feil, prøv fast Norsk eller English.</p>
          <div class="settings-map-section settings-map-model">
            <span data-nb="Talemodell" data-en="Speech model">Talemodell</span>
            <strong>small</strong>
            <span class="settings-map-button" data-nb="Modeller …" data-en="Models…">Modeller …</span>
          </div>
          <p data-nb="Small er standard. Hvis det føles tregt, åpne Modeller og prøv Base." data-en="Small is the default. If it feels slow, open Models and try Base.">Small er standard. Hvis det føles tregt, åpne Modeller og prøv Base.</p>
        </div>
        <figcaption>
          <span class="walkthrough-step">02</span>
          <div>
            <strong data-nb="Prøv språk og modell" data-en="Try languages and models">Prøv språk og modell</strong>
            <p data-nb="Du finner begge valgene under Generelt. Start med Automatisk og Small, og endre bare hvis du har en grunn." data-en="Both controls are under General. Start with Automatic and Small, and only change them if you have a reason.">Du finner begge valgene under Generelt. Start med Automatisk og Small, og endre bare hvis du har en grunn.</p>
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
