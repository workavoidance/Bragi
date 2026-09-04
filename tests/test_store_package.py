from __future__ import annotations

import struct
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOUNDATION = "http://schemas.microsoft.com/appx/manifest/foundation/windows10"
UAP = "http://schemas.microsoft.com/appx/manifest/uap/windows10"
UAP5 = "http://schemas.microsoft.com/appx/manifest/uap/windows10/5"
RESCAP = (
    "http://schemas.microsoft.com/appx/manifest/"
    "foundation/windows10/restrictedcapabilities"
)


def test_store_manifest_uses_reserved_product_identity() -> None:
    root = ET.parse(ROOT / "store" / "AppxManifest.xml").getroot()
    identity = root.find(f"{{{FOUNDATION}}}Identity")
    properties = root.find(f"{{{FOUNDATION}}}Properties")

    assert identity is not None
    assert identity.attrib == {
        "Name": "Skrivi.Skrivi",
        "Publisher": "CN=EF3D997F-87B2-4AD0-B65B-877EE1632E65",
        "Version": "__PACKAGE_VERSION__",
        "ProcessorArchitecture": "x64",
    }
    assert properties is not None
    assert properties.findtext(f"{{{FOUNDATION}}}PublisherDisplayName") == "Skrivi"


def test_store_manifest_declares_full_trust_desktop_app() -> None:
    root = ET.parse(ROOT / "store" / "AppxManifest.xml").getroot()
    application = root.find(f"{{{FOUNDATION}}}Applications/{{{FOUNDATION}}}Application")
    capability = root.find(f"{{{FOUNDATION}}}Capabilities/{{{RESCAP}}}Capability")
    visual_elements = application.find(f"{{{UAP}}}VisualElements")

    assert application is not None
    assert application.attrib["Executable"] == "Skrivi.exe"
    assert capability is not None
    assert capability.attrib["Name"] == "runFullTrust"
    assert visual_elements is not None


def test_store_manifest_declares_opt_in_startup_task() -> None:
    root = ET.parse(ROOT / "store" / "AppxManifest.xml").getroot()
    application = root.find(f"{{{FOUNDATION}}}Applications/{{{FOUNDATION}}}Application")
    extension = application.find(f"{{{FOUNDATION}}}Extensions/{{{UAP5}}}Extension")
    startup_task = extension.find(f"{{{UAP5}}}StartupTask")

    assert extension.attrib == {
        "Category": "windows.startupTask",
        "Executable": "Skrivi.exe",
        "EntryPoint": "Windows.FullTrustApplication",
    }
    assert startup_task.attrib == {
        "TaskId": "SkriviStartup",
        "Enabled": "false",
        "DisplayName": "Skrivi",
    }


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", data[16:24])


def test_store_assets_have_manifest_sizes() -> None:
    assets = ROOT / "store" / "assets"

    assert _png_size(assets / "StoreLogo.png") == (50, 50)
    assert _png_size(assets / "Square44x44Logo.png") == (44, 44)
    assert _png_size(assets / "Square150x150Logo.png") == (150, 150)


def test_store_build_is_parallel_and_documented_as_unsigned() -> None:
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(
        encoding="utf-8"
    )
    guide = (ROOT / "docs" / "MICROSOFT_STORE.md").read_text(encoding="utf-8")

    assert "store-package:" in workflow
    assert "continue-on-error: true" in workflow
    assert "build_store_msix.ps1" in workflow
    assert "9P42NBXD8W36" in guide
    assert "Do not publish the unsigned" in guide
