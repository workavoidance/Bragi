from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "whisper-dictate.ico"


def main() -> None:
    image = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 248, 248), fill="#1d4ed8")
    draw.rounded_rectangle((96, 50, 160, 158), radius=32, fill="white")
    draw.arc((70, 106, 186, 198), 0, 180, fill="white", width=16)
    draw.line((128, 190, 128, 218), fill="white", width=16)
    draw.line((94, 218, 162, 218), fill="white", width=16)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (256, 256)])


if __name__ == "__main__":
    main()
