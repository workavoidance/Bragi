# Code signing policy

## Current status

Skrivi is applying to the SignPath Foundation open-source code-signing
programme. Current Windows releases are not Authenticode-signed. After the
application is approved and the signing workflow is configured, this policy
will govern every Windows release signed through SignPath.

Free code signing provided by SignPath.io, certificate by SignPath Foundation.

## Project

- **Project:** Skrivi
- **Repository:** <https://github.com/workavoidance/Skrivi>
- **Licence:** [MIT](LICENSE)
- **Official releases:** <https://github.com/workavoidance/Skrivi/releases>

Skrivi's application source, build scripts, installer definition, and GitHub
Actions workflows are maintained in the public repository. Third-party
components included in packaged builds retain their own licences and are listed
in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Team roles

Skrivi is currently maintained by one person, who holds the following roles:

- **Authors and committers:**
  [@workavoidance](https://github.com/workavoidance), who maintains the source
  code and build configuration.
- **Reviewers:** [@workavoidance](https://github.com/workavoidance), who reviews
  changes proposed by contributors without direct commit access before merge.
- **Approvers:** [@workavoidance](https://github.com/workavoidance), who will
  manually approve each SignPath signing request.

Anyone assigned to one of these roles must use multi-factor authentication for
both GitHub and SignPath access. Changes to the role assignments must be
recorded in this policy.

## Eligible artifacts

Only official Windows release artifacts produced by the repository's
`.github/workflows/release.yml` workflow are eligible for signing:

- the `Skrivi.exe` application executable included in the portable ZIP; and
- the `Skrivi-<version>-windows-x64-setup.exe` per-user installer.

The ZIP archive itself is not an Authenticode-signable file. A SHA-256 checksum
is published alongside each release archive and installer.

Pull-request previews, local builds, manually uploaded replacement binaries,
and artifacts built from forks or self-hosted runners are not eligible for
signing. Third-party binaries bundled with Skrivi may retain their upstream
signatures or remain unsigned; they must not be presented to SignPath as
project-owned binaries.

## Trusted build and release process

For a release covered by this policy:

1. The release source and build configuration must come from the official
   repository and a commit on `main`.
2. The source-controlled release workflow must build the application and
   installer on a GitHub-hosted `windows-latest` runner.
3. The quality checks in `.github/workflows/ci.yml` must pass for the release
   commit.
4. SignPath origin verification must connect the signing request to the
   repository, commit, workflow run, and artifacts produced by that run.
5. An approver listed above must review and manually approve every signing
   request. Signing must never be approved automatically.
6. The signed artifacts must be verified before their checksums are generated
   and they are published to GitHub Releases. They must not be replaced with
   locally built files.

The SignPath artifact configuration must restrict the product identity to
`Skrivi` and require file and product versions that correspond to the version
declared in `release/VERSION`. Only files explicitly covered by the approved
artifact configuration may be signed.

## Privacy and network access

Skrivi processes speech locally. It does not send recordings or transcripts to
a cloud transcription service and does not collect usage telemetry. The app
uses the network only to download a selected speech model from its published
Hugging Face source when that model is not already installed. The download host
can observe normal connection metadata such as the requesting IP address.

The complete data-handling description is in the
[privacy policy](docs/PRIVACY.md), and the model sources and integrity checks are
documented in the [local model guide](docs/MODELS.md).

## Installation and system changes

The installer installs Skrivi for the current Windows user, creates Start menu
and uninstall entries, and does not request administrator rights. An optional
desktop shortcut can be selected during installation. Automatic start at sign-in
is off by default and can be enabled or disabled in Skrivi's settings. Skrivi
can be removed through the standard Windows installed-apps interface.

## Verification and incident response

For releases covered by this policy, users can inspect an executable's Windows
signature with `Get-AuthenticodeSignature` in PowerShell. A valid SignPath-backed
release should report a valid signature whose signer is SignPath Foundation.
The separately published SHA-256 checksum confirms that downloaded bytes match
the release asset, but a checksum alone is not a code signature.

Suspected certificate misuse, an unexpected signed artifact, or a compromised
release should be reported privately as described in [SECURITY.md](SECURITY.md).
The maintainer will stop the affected signing or publication process, preserve
available build evidence, notify SignPath, and request certificate revocation
when appropriate.
