from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "skrivi.ico"
STORE_ASSETS = {
    ROOT / "store" / "assets" / "StoreLogo.png": 50,
    ROOT / "store" / "assets" / "Square44x44Logo.png": 44,
    ROOT / "store" / "assets" / "Square150x150Logo.png": 150,
    ROOT
    / "store"
    / "assets"
    / "Square44x44Logo.targetsize-44_altform-unplated.png": 44,
    ROOT / "store" / "listing" / "Skrivi-300x300.png": 300,
}
SKRIVI_INK = "#181817"
SKRIVI_ICON_EDGE = "#FFFDF9"


def _rounded_line(
    draw: ImageDraw.ImageDraw,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    width: int,
    color: str,
) -> None:
    draw.line((start, end), fill=color, width=width)
    radius = width / 2
    for x, y in (start, end):
        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=color,
        )


def main() -> None:
    size = 1024
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    dot_x = size * 0.17
    dot_y = size * 0.50
    dot_radius = size * 0.14
    edge_width = size * 0.045
    draw.ellipse(
        (
            dot_x - dot_radius - edge_width,
            dot_y - dot_radius - edge_width,
            dot_x + dot_radius + edge_width,
            dot_y + dot_radius + edge_width,
        ),
        fill=SKRIVI_ICON_EDGE,
    )
    draw.ellipse(
        (
            dot_x - dot_radius,
            dot_y - dot_radius,
            dot_x + dot_radius,
            dot_y + dot_radius,
        ),
        fill=SKRIVI_INK,
    )

    lines = (
        ((size * 0.50, size * 0.38), (size * 0.78, size * 0.17)),
        ((size * 0.52, size * 0.50), (size * 0.94, size * 0.50)),
        ((size * 0.50, size * 0.62), (size * 0.78, size * 0.83)),
    )
    width = round(size * 0.13)
    outlined_width = width + round(edge_width * 2)
    for start, end in lines:
        _rounded_line(
            draw,
            start,
            end,
            width=outlined_width,
            color=SKRIVI_ICON_EDGE,
        )
    for start, end in lines:
        _rounded_line(
            draw,
            start,
            end,
            width=width,
            color=SKRIVI_INK,
        )

    icon = image.resize((256, 256), Image.Resampling.LANCZOS)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    icon.save(
        OUTPUT,
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (256, 256)],
    )
    for path, asset_size in STORE_ASSETS.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        image.resize((asset_size, asset_size), Image.Resampling.LANCZOS).save(path)


if __name__ == "__main__":
    main()
