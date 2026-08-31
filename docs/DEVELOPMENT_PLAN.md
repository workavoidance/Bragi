# Bragi development plan

This is the project's durable execution checklist and current source of truth
for development progress. Update it in the same pull request that completes or
changes an item. The [roadmap](ROADMAP.md) describes intended releases; this
file records the work, its order, and its status.

Last reviewed: 2026-08-31

## Product requirements that must remain true

- Bragi is a local push-to-talk speech-to-text application for Windows 11.
- The default workflow is hold a key, speak, release, and insert the complete
  transcription wherever Windows accepts typing.
- English and Norwegian are first-class language requirements.
- Bragi does not retain recordings or transcripts and does not use the
  clipboard for dictated text.
- Initial installation and user-requested model downloads may use the internet.
  Once setup is complete, every installed feature must keep working after the
  network is disconnected and Windows is restarted.
- Runtime use must not depend on telemetry, accounts, licence checks, update
  checks, or a remotely fetched model catalogue.
- Accessibility is an engineering requirement, while school or public-sector
  suitability must not be claimed without later independent evidence.

## Current position

**Current target:** v0.2, a configurable and accessible desktop application.

**Next engineering task:** implement the versioned settings foundation in issue
[#5](https://github.com/workavoidance/Bragi/issues/5).

The v0.2 tracking issue is
[#10](https://github.com/workavoidance/Bragi/issues/10).

## Completed foundation

- [x] Prove the core Windows 11 push-to-talk workflow.
- [x] Use Right Ctrl as the initial hold-to-talk key.
- [x] Use the Windows default microphone.
- [x] Run multilingual Whisper locally on CPU with English and Norwegian
  automatic detection.
- [x] Insert Unicode directly without using the clipboard.
- [x] Avoid writing audio, transcripts, or content logs to disk.
- [x] Show compact loading, recording, and transcription feedback.
- [x] Package a portable executable with Python 3.14 support.
- [x] Publish the source in the public Bragi GitHub repository under MIT.
- [x] Add automated Windows lint and test checks.
- [x] Add tagged-release automation and dependency update configuration.
- [x] Add contribution, security, privacy, architecture, roadmap, and quality
  documentation.
- [x] Record the PySide6 user-interface decision.
- [x] Create focused v0.2 issues and an overall tracking issue.
- [x] Rename the public README to Bragi.

## Phase 1: fast development and preview loop

Tracked by [#11](https://github.com/workavoidance/Bragi/issues/11).

- [x] Create a focused GitHub issue with acceptance criteria for the development
  workflow.
- [x] Add a `dev.bat` launcher that runs Bragi directly from an editable source
  installation.
- [x] Add automatic controlled restart when application source files change.
- [x] Add a mock transcription mode that requires neither Whisper nor a
  microphone and can simulate loading, ready, recording, transcribing, success,
  and error states.
- [x] Keep development settings separate from normal user settings.
- [x] Move downloaded models to a stable per-user location so development and
  preview builds do not download them repeatedly.
- [x] Clearly identify development builds and expose the tested commit ID.
- [x] Make each pull request produce a labelled portable Windows preview
  artifact.
- [x] Document the one-command development and preview workflow.

## Phase 2: versioned settings foundation

Tracked by [#5](https://github.com/workavoidance/Bragi/issues/5).

- [ ] Define a UI-independent settings model with a schema version.
- [ ] Store settings in the appropriate per-user Windows application-data
  directory.
- [ ] Preserve the defaults: automatic language, multilingual `small` model,
  Right Ctrl, and Windows default microphone.
- [ ] Write settings atomically so interruption cannot leave a partial file.
- [ ] Validate values and recover safely from missing or corrupt settings.
- [ ] Add migrations for future schema versions.
- [ ] Confirm that settings never contain audio or transcript content.
- [ ] Add unit tests for defaults, validation, persistence, corruption, and
  migration.

## Phase 3: accessible settings interface

Tracked by [#9](https://github.com/workavoidance/Bragi/issues/9) and
[#8](https://github.com/workavoidance/Bragi/issues/8).

- [ ] Add the PySide6 system tray and settings window without changing the
  proven dictation pipeline.
- [ ] Keep model loading and transcription away from the UI thread.
- [ ] Make every settings action operable with the keyboard.
- [ ] Add accessible names, roles, focus order, and non-colour status cues.
- [ ] Verify high-DPI, 200% text scaling, high-contrast, and multiple-display
  behaviour.
- [ ] Add UI tests using the mock transcription mode.

## Phase 4: live language, microphone, and hotkey configuration

Tracked by [#6](https://github.com/workavoidance/Bragi/issues/6).

- [ ] Offer Automatic, English, and Norwegian language modes.
- [ ] Apply language changes to the next recording without restarting Bragi.
- [ ] Enumerate microphones while keeping Windows Default as the default.
- [ ] Recover clearly when a selected microphone is disconnected.
- [ ] Add hotkey capture, validation, conflict guidance, and Restore Default.
- [ ] Replace the active global hotkey listener atomically without leaving a
  duplicate listener.
- [ ] Preserve correct insertion of Norwegian characters.

## Phase 5: local model manager

Tracked by [#7](https://github.com/workavoidance/Bragi/issues/7).

- [ ] Ship a local model catalogue containing identifiers, download sizes, CPU
  guidance, and checksums.
- [ ] Offer a small curated set of multilingual models and keep `small` as the
  recommended CPU default.
- [ ] Show which models are installed and which require a user-requested
  download.
- [ ] Download to a temporary file, verify integrity, then install atomically.
- [ ] Recover from interrupted or corrupt downloads without damaging an
  existing working model.
- [ ] Allow installed models to be selected and used while completely offline.
- [ ] Provide file or USB import for offline model installation.
- [ ] Load a newly selected model in the background and recover to the previous
  working model if loading fails.

## Phase 6: reliability and privacy hardening

Tracked by [#4](https://github.com/workavoidance/Bragi/issues/4).

- [ ] Handle microphone removal and default-device changes.
- [ ] Add cancellation and an accidental long-recording limit.
- [ ] Recover from model-load and transcription failures.
- [ ] Shut down cleanly during recording, download, and transcription.
- [ ] Test repeated start and stop cycles for leaked streams or listeners.
- [ ] If diagnostic logs are added, document every field and prove through tests
  that they contain no audio or dictated text.
- [ ] Test a completed installation after disconnecting the network and
  restarting Windows.
- [ ] Add an automated or controlled test that detects accidental required
  runtime network access.

## Phase 7: v0.2 release candidate

- [ ] Complete every acceptance criterion in tracking issue
  [#10](https://github.com/workavoidance/Bragi/issues/10).
- [ ] Rename remaining application, executable, package, mutex, tray, and window
  identifiers from the prototype name to Bragi.
- [ ] Perform clean source-install and portable-build tests on Windows 11.
- [ ] Test English, Norwegian, mixed-language speech, and `æ`, `ø`, and `å` in
  Notepad, a browser, and Microsoft Office.
- [ ] Verify first-time online setup followed by normal offline operation.
- [ ] Review third-party licences and packaged notices.
- [ ] Update the changelog, limitations, and privacy documentation.
- [ ] Tag and publish a clearly labelled alpha release.

## Later credibility gates

These are recorded now so current decisions do not undermine them. They are not
claims about the present alpha.

- [ ] Establish repeatable Norwegian and English accuracy benchmarks.
- [ ] Publish representative school-laptop performance results.
- [ ] Conduct structured usability testing with people who have dyslexia.
- [ ] Obtain an independent accessibility evaluation.
- [ ] Add signed releases, an installer suitable for managed devices, an SBOM,
  and vulnerability scanning.
- [ ] Document the threat model, support policy, and vulnerability-response
  process.
- [ ] Obtain independent security and data-protection review before pursuing
  school or public-sector recommendations.

## Definition of done for every checklist item

An item is checked only when all applicable conditions are met:

1. The implementation and acceptance criteria agree.
2. Automated tests cover the important success and failure paths.
3. Windows CI passes.
4. User-facing behaviour and limitations are documented.
5. Privacy and offline-operation requirements remain intact.
6. A real Windows test is completed when hardware or operating-system behaviour
   cannot be adequately verified in automation.
7. The change is merged into `main`, and this checklist is updated in the same
   pull request or immediately afterward.
