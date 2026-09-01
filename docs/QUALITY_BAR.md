# Software quality bar

Skrivi's long-term aim is to become credible assistive software for
people with dyslexia, including students in Norwegian schools. That ambition
does not change the immediate product scope, but it does affect the engineering
standards used from the beginning.

This document describes software gates, not claims that the project currently
meets educational, accessibility, security, or government requirements.

## Current gate: trustworthy alpha

- The core workflow remains local and understandable.
- Releases are produced from tagged source by automated Windows builds.
- Dependencies are constrained, updated deliberately and scanned.
- Tests cover the state machine, Unicode insertion and privacy-sensitive paths.
- Errors are actionable without logging audio or dictated text.
- Configuration changes cannot silently weaken the privacy defaults.
- The application clearly states its alpha status and limitations.

## Next gate: credible public beta

- Keyboard-only operation and screen-reader testing.
- Windows high-contrast, text scaling and multi-display support.
- A documented Norwegian and English accuracy benchmark using consented or
  openly licensed evaluation material.
- Hardware performance results for representative school laptops.
- Signed Windows releases and a conventional managed installer.
- Software bill of materials, vulnerability scanning and third-party notices.
- A documented threat model and independent security review.
- Norwegian and English interface text, documentation and privacy information.
- A support and maintenance policy with predictable security updates.

## Later gate: educational deployment candidate

- Structured usability testing with people who have dyslexia, including young
  users, with appropriate consent and safeguarding.
- Independent accessibility evaluation against the applicable standard.
- Administrator-controlled installation and configuration for managed devices.
- Clear behaviour in examination and locked-down environments.
- Data-protection documentation suitable for school review.
- Independent Norwegian-language accuracy and reliability evidence.
- A sustainable maintainer, release and vulnerability-response model.

## Engineering principles

1. Accessibility is a product requirement, not a final visual polish pass.
2. Local processing and data minimisation remain the default.
3. Accuracy claims require repeatable measurements and published methodology.
4. School suitability is never inferred from a successful personal test.
5. Security and privacy claims must be auditable in the source and release
   process.
6. Every institutional feature must also preserve a simple individual-user
   experience.
