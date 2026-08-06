"""Generate the lightweight 30-second README product-flow GIF."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "assets" / "sentinelops-nexus-30-second-flow.gif"
WIDTH, HEIGHT, FPS = 960, 540, 4

STAGES = (
    ("FORECAST", "+30 MIN SAFE-CAPACITY CROSSING", "Bounded deterministic Redis forecast", (34, 211, 238)),
    ("DIGITAL TWIN", "VERSION-LOCKED + CONTENT-HASHED", "Fixed seed and disabled network", (45, 212, 191)),
    ("SIMULATION", "12 COUNTERFACTUAL SCENARIOS", "Same Twin manifest, repeatable outcomes", (96, 165, 250)),
    ("GEMINI REASONING", "EVIDENCE-GROUNDED SYNTHESIS", "Contradictions, scenarios and executive narrative", (139, 92, 246)),
    ("GEMMA REVIEW", "ADVISORY POLICY CRITIQUE", "Gate consistency and evidence completeness", (245, 158, 11)),
    ("HUMAN APPROVAL", "SENIOR ROLE + RATIONALE", "Backend-authoritative decision boundary", (52, 211, 153)),
    ("EVIDENCE ZIP", "AUDIT CHAIN + MANIFEST.SHA256", "Governed evidence export", (20, 184, 166)),
)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = ("seguisb.ttf", "segoeuib.ttf") if bold else ("segoeui.ttf",)
    for name in names:
        path = Path("C:/Windows/Fonts") / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


TITLE = font(21, True)
SUBTITLE = font(10, True)
NODE = font(13, True)
NODE_SMALL = font(8, True)
PANEL_TITLE = font(25, True)
PANEL_KPI = font(17, True)
BODY = font(13)
SAFETY = font(10, True)


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: tuple[int, ...], outline: tuple[int, ...], width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=12, fill=fill, outline=outline, width=width)


def base_frame() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), (4, 11, 22))
    draw = ImageDraw.Draw(image)
    for x in range(0, WIDTH, 48):
        draw.line((x, 0, x, HEIGHT), fill=(8, 25, 39), width=1)
    for y in range(0, HEIGHT, 48):
        draw.line((0, y, WIDTH, y), fill=(8, 25, 39), width=1)
    draw.rectangle((0, 0, WIDTH, 68), fill=(5, 17, 31))
    draw.text((30, 17), "SENTINELOPS NEXUS", font=TITLE, fill=(226, 245, 255))
    draw.text((246, 25), "30-SECOND PRODUCT FLOW", font=SUBTITLE, fill=(45, 212, 191))
    draw.text((735, 25), "HUMAN-GOVERNED", font=SUBTITLE, fill=(52, 211, 153))
    return image


def draw_stage(frame: Image.Image, active: int, tick: int, complete: bool = False) -> None:
    draw = ImageDraw.Draw(frame)
    node_x1, node_x2, node_h, gap, start_y = 30, 342, 48, 9, 82
    for index, (name, metric, _detail, accent) in enumerate(STAGES):
        y1 = start_y + index * (node_h + gap)
        y2 = y1 + node_h
        is_done = complete or index < active
        is_active = not complete and index == active
        border = accent if is_active else ((33, 158, 139) if is_done else (30, 61, 82))
        fill = (8, 38, 48) if is_active else ((6, 31, 35) if is_done else (7, 21, 35))
        width = 3 if is_active else 1
        rounded(draw, (node_x1, y1, node_x2, y2), fill, border, width)
        pulse = 3 + int(2 * (1 + math.sin(tick * math.pi / 4))) if is_active else 0
        circle = (46, y1 + 10, 74, y1 + 38)
        if is_active:
            draw.ellipse((circle[0] - pulse, circle[1] - pulse, circle[2] + pulse, circle[3] + pulse), outline=accent, width=2)
        draw.ellipse(circle, fill=accent if (is_done or is_active) else (19, 48, 66))
        draw.text((55 if index < 9 else 51, y1 + 16), "OK" if is_done else str(index + 1), font=NODE_SMALL, fill=(3, 15, 23) if (is_done or is_active) else (123, 151, 171))
        draw.text((88, y1 + 8), name, font=NODE, fill=(230, 245, 255) if (is_done or is_active) else (118, 145, 165))
        draw.text((88, y1 + 28), metric, font=NODE_SMALL, fill=accent if (is_done or is_active) else (72, 101, 122))
        if index < len(STAGES) - 1:
            arrow_y = y2 + 2
            draw.line((186, arrow_y, 186, arrow_y + gap - 3), fill=(32, 91, 108), width=2)
            draw.polygon(((181, arrow_y + gap - 5), (191, arrow_y + gap - 5), (186, arrow_y + gap)), fill=(32, 91, 108))

    if complete:
        panel_title = "EVIDENCE-GROUNDED FLOW COMPLETE"
        panel_metric = "PREDICT  |  TEST  |  REVIEW  |  DECIDE"
        panel_detail = "The governed evidence package is ready for verification."
        accent = (52, 211, 153)
    else:
        panel_title, panel_metric, panel_detail, accent = STAGES[active]

    panel = (374, 82, 930, 480)
    rounded(draw, panel, (7, 22, 36), (*accent, 255), 2)
    sweep = 390 + ((tick * 34) % 500)
    draw.rectangle((sweep, 84, min(sweep + 70, 928), 86), fill=accent)
    draw.text((406, 118), f"STEP {active + 1 if not complete else 7} OF 7", font=SUBTITLE, fill=accent)
    draw.text((406, 151), panel_title, font=PANEL_TITLE, fill=(235, 247, 255))
    draw.line((406, 192, 884, 192), fill=(26, 65, 84), width=1)
    draw.text((406, 222), panel_metric, font=PANEL_KPI, fill=accent)
    draw.text((406, 263), panel_detail, font=BODY, fill=(156, 183, 201))
    rounded(draw, (406, 318, 884, 382), (5, 31, 38), (31, 100, 104))
    draw.text((430, 335), "AUTHORITATIVE STATE", font=NODE_SMALL, fill=(84, 219, 203))
    draw.text((430, 354), "BACKEND CALCULATED  |  AUDITED  |  TRACEABLE", font=SUBTITLE, fill=(214, 238, 244))
    draw.text((406, 416), "Models explain. Deterministic gates decide. Humans approve.", font=BODY, fill=(132, 159, 178))

    draw.rectangle((0, 502, WIDTH, HEIGHT), fill=(4, 27, 28))
    draw.text((30, 514), "PRODUCTION ACTION: NOT EXECUTED", font=SAFETY, fill=(52, 211, 153))
    draw.text((705, 514), "sentinelops nexus / cloud run", font=SAFETY, fill=(75, 117, 137))
    elapsed = 30 if complete else active * 4 + tick / FPS
    draw.rectangle((0, 498, int(WIDTH * elapsed / 30), 502), fill=accent)


def generate() -> None:
    frames: list[Image.Image] = []
    for active in range(len(STAGES)):
        for tick in range(4 * FPS):
            frame = base_frame()
            draw_stage(frame, active, tick)
            frames.append(frame.quantize(colors=64, method=Image.Quantize.FASTOCTREE))
    for tick in range(2 * FPS):
        frame = base_frame()
        draw_stage(frame, len(STAGES) - 1, tick, complete=True)
        frames.append(frame.quantize(colors=64, method=Image.Quantize.FASTOCTREE))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(OUTPUT, save_all=True, append_images=frames[1:], duration=250, loop=0, optimize=True, disposal=2)
    print(f"Generated {OUTPUT.relative_to(ROOT)} ({OUTPUT.stat().st_size / 1024 / 1024:.2f} MiB, 30 seconds)")


if __name__ == "__main__":
    generate()
