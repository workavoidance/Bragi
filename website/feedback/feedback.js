(() => {
  const button = document.querySelector('.language-switch');
  if (!button) return;

  const setLanguage = (language) => {
    const norwegian = language === 'nb';
    document.documentElement.lang = norwegian ? 'nb' : 'en';

    document.querySelectorAll('[data-nb][data-en]').forEach((element) => {
      element.textContent = norwegian ? element.dataset.nb : element.dataset.en;
    });

    document.querySelectorAll('[data-aria-nb][data-aria-en]').forEach((element) => {
      element.setAttribute('aria-label', norwegian ? element.dataset.ariaNb : element.dataset.ariaEn);
    });

    const description = document.querySelector('meta[name="description"]');
    if (description) {
      description.content = norwegian
        ? 'Gi tilbakemelding på Skrivi: rapporter feil, transkripsjonsproblemer eller foreslå forbedringer.'
        : 'Give feedback on Skrivi: report bugs, transcription problems, or suggest improvements.';
    }

    button.textContent = norwegian ? 'EN' : 'NO';
    button.setAttribute('aria-label', norwegian ? 'Switch to English' : 'Bytt til norsk');
    button.setAttribute('aria-pressed', norwegian ? 'false' : 'true');
    document.title = norwegian ? 'Skrivi — tilbakemelding' : 'Skrivi — feedback';
  };

  button.addEventListener('click', () => {
    setLanguage(document.documentElement.lang === 'nb' ? 'en' : 'nb');
  });

  setLanguage('nb');
})();
