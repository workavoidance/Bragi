# Microsoft Store distribution

Skrivi's Microsoft Store product identity is:

- Store ID: `9P42NBXD8W36`
- Package name: `Skrivi.Skrivi`
- Publisher: `CN=EF3D997F-87B2-4AD0-B65B-877EE1632E65`
- Publisher display name: `Skrivi`

The Store package is an additional distribution channel. The existing Inno
Setup installer and portable archive remain the primary GitHub release assets.
A failure or delay in Store packaging or certification must not block their
publication.

## First submission

1. Let the release workflow build the unsigned `.msix` artifact.
2. Download the `Skrivi-<version>-Microsoft-Store` artifact from the workflow
   run.
3. In Partner Center, open Skrivi and start an MSIX submission.
4. Complete pricing, availability, properties, age ratings, Store listings and
   submission options.
5. Upload the `.msix` from the workflow artifact and submit it for
   certification.

Microsoft signs the package after certification. Do not publish the unsigned
workflow artifact as a direct download: it is intended only for Partner Center.

Before the first public submission, verify microphone capture, global
push-to-talk, text insertion, model download and settings persistence from an
installed Store package. Automatic startup is intentionally unavailable in the
first Store package because MSIX virtualizes the registry mechanism used by the
website build. Also avoid installing the Store and website editions together;
they are separate installations and may keep separate application data.

After the first submission is accepted, automate future free-app updates with
the Microsoft Store Developer CLI. Store credentials belong in GitHub Actions
secrets and must never be committed to this repository.

The public Store page will use:

`https://apps.microsoft.com/detail/9P42NBXD8W36`
