(() => {
  const button = document.querySelector('.language-switch');
  if (!button) return;

  const makeAlphaLink = () => {
    const link = document.createElement('a');
    link.href = 'alpha/';
    link.dataset.nb = 'Test Skrivi';
    link.dataset.en = 'Test Skrivi';
    link.textContent = 'Test Skrivi';
    return link;
  };

  const header = document.querySelector('.header-actions');
  if (header) {
    header.insertBefore(makeAlphaLink(), button);
  }

  const footer = document.querySelector('.footer-links');
  if (footer) {
    footer.insertBefore(makeAlphaLink(), footer.firstChild);
  }

  const heroCopy = document.querySelector('.hero-copy');
  if (heroCopy) {
    heroCopy.dataset.nb = 'Nøyaktig, lokal tale-til-tekst. Gratis for alle.';
    heroCopy.dataset.en = 'Accurate, local speech-to-text. Free for everyone.';
  }

  const setLanguage = (language) => {
    const norwegian = language === 'nb';
    document.documentElement.lang = norwegian ? 'nb' : 'en';

    document.querySelectorAll('[data-nb][data-en]').forEach((element) => {
      element.textContent = norwegian ? element.dataset.nb : element.dataset.en;
    });

    document.querySelectorAll('[data-aria-nb][data-aria-en]').forEach((element) => {
      element.setAttribute('aria-label', norwegian ? element.dataset.ariaNb : element.dataset.ariaEn);
    });

    document.querySelectorAll('[data-href-nb][data-href-en]').forEach((element) => {
      element.href = norwegian ? element.dataset.hrefNb : element.dataset.hrefEn;
    });

    const description = document.querySelector('meta[name="description"]');
    if (description) {
      description.content = norwegian
        ? 'Skrivi er nøyaktig, lokal tale-til-tekst. Gratis for alle.'
        : 'Skrivi is accurate, local speech-to-text. Free for everyone.';
    }

    button.textContent = norwegian ? 'EN' : 'NO';
    button.setAttribute('aria-label', norwegian ? 'Switch to English' : 'Bytt til norsk');
    button.setAttribute('aria-pressed', norwegian ? 'false' : 'true');
    document.title = norwegian
      ? 'Skrivi — lokal tale-til-tekst'
      : 'Skrivi — local speech-to-text';
  };

  button.addEventListener('click', () => {
    setLanguage(document.documentElement.lang === 'nb' ? 'en' : 'nb');
  });

  setLanguage('nb');
})();
