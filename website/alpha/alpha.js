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
      element.setAttribute(
        'aria-label',
        norwegian ? element.dataset.ariaNb : element.dataset.ariaEn,
      );
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
    document.title = norwegian ? 'Test Skrivi — alpha' : 'Test Skrivi — alpha';
  };

  button.addEventListener('click', () => {
    setLanguage(document.documentElement.lang === 'nb' ? 'en' : 'nb');
  });

  setLanguage('nb');
})();
