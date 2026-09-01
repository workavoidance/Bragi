# Local speech models

Bragi uses a small curated catalogue of multilingual faster-whisper models. The
catalogue is packaged with the application, so listing or selecting an already
installed model never requires an internet connection.

## Curated catalogue

| Model | Download | RAM guidance | CPU guidance | Purpose |
| --- | ---: | ---: | --- | --- |
| Tiny | 78 MB | 4 GB | Fastest | Lowest latency, lowest accuracy |
| Base | 148 MB | 4 GB | Faster | Faster alternative for slower PCs |
| Small | 486 MB | 8 GB | Recommended | Default balance for Norwegian and English |
| Medium | 1.53 GB | 16 GB | Slow | Potential accuracy gain on powerful PCs |

All four entries are multilingual. Bragi does not currently offer English-only
models because Norwegian is a first-class requirement. Small remains the
initial and recommended CPU model.

The model files come from the official Systran faster-whisper repositories on
Hugging Face: [Tiny](https://huggingface.co/Systran/faster-whisper-tiny),
[Base](https://huggingface.co/Systran/faster-whisper-base),
[Small](https://huggingface.co/Systran/faster-whisper-small), and
[Medium](https://huggingface.co/Systran/faster-whisper-medium).

## Installation and integrity

Every catalogue entry pins an immutable upstream revision and the expected size
and checksum of every runtime file. Bragi downloads into a temporary staging
directory, verifies the complete set, writes a local manifest, and only then
makes the model available. A failed, interrupted, incomplete, or corrupt
download is never shown as installed.

The Models panel shows the model name, bytes downloaded, total size, percentage,
and a separate verification stage. **Cancel download** interrupts either stage,
removes incomplete staging and cache files, and does not alter any installed or
active model. When Bragi closes, it requests cancellation and waits briefly for
the download worker to remove incomplete staging files. Any remnants from a
non-cooperative network operation are removed at the next startup and are never
treated as installed.

The prototype's existing Hugging Face cache is checked locally before Bragi
uses the internet. This allows an existing Small download to be reused when
upgrading. Stale temporary downloads are removed safely at the next start.

Installed models live under:

```text
%LOCALAPPDATA%\Bragi\models\installed
```

Model files remain separate from `%APPDATA%\Bragi\settings.json`.

## Offline operation

The first Small installation and each explicit Download action may use the
internet. Once a model is installed, Bragi passes its local directory directly
to faster-whisper. Normal transcription, model selection, integrity checks, and
removal do not fetch a remote catalogue or contact the model host.

## Import by folder or USB drive

An installed model folder contains `bragi-model.json` alongside its model
files. Copy the complete folder from another Bragi PC onto a USB drive, select
**Models**, choose **Import folder**, and select that folder. Bragi verifies the
files against its packaged catalogue before installing them. Altered or
unsupported folders are rejected.

## Loading and recovery

Model loading occurs in a worker thread. Bragi fully loads a candidate before
replacing the working model. If loading or settings persistence fails, the
previous loaded model remains active. An active model cannot be removed until
another installed model has been selected.
