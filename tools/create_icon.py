from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "whisper-dictate.ico"
BRAGI_ORANGE = "#F05A24"


def _rounded_line(
    draw: ImageDraw.ImageDraw,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    width: int,
) -> None:
    draw.line((start, end), fill=BRAGI_ORANGE, width=width)
    radius = width / 2
    for x, y in (start, end):
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=BRAGI_ORANGE,
        )


def main() -> None:
    size = 1024
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    dot_x = size * 0.27
    dot_y = size * 0.50
    dot_radius = size * 0.115
    draw.ellipse(
        (
            dot_x - dot_radius,
            dot_y - dot_radius,
            dot_x + dot_radius,
            dot_y + dot_radius,
        ),
        fill=BRAGI_ORANGE,
    )

    width = round(size * 0.105)
    _rounded_line(
        draw,
        (size * 0.54, size * 0.39),
        (size * 0.72, size * 0.29),
        width=width,
    )
    _rounded_line(
        draw,
        (size * 0.56, size * 0.50),
        (size * 0.80, size * 0.50),
        width=width,
    )
    _rounded_line(
        draw,
        (size * 0.54, size * 0.61),
        (size * 0.72, size * 0.71),
        width=width,
    )

    icon = image.resize((256, 256), Image.Resampling.LANCZOS)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    icon.save(
        OUTPUT,
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (256, 256)],
    )


if __name__ == "__main__":
    main()
