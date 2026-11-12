"""Helpers for slide-ready SVG diagrams (PowerPoint-safe).

Copy this file next to your figure script, or import it from the skill folder.
Edit PALETTE and FONT to match the deck. Usage:

    from svgkit import Svg, PALETTE as C
    s = Svg(600, 400)
    s.box(40, 40, 260, 110, "Client", fill="white", stroke=C["primary"])
    s.arrow(150, 110, 150, 200, C["primary"])
    s.label(150, 155, "HTTPS", C["primary"])
    s.save("flow.svg")          # lints, then writes
    render("flow.svg", "flow.png")
"""
import math
import re
import shutil
import subprocess
import sys

FONT = "Roboto, Arial, sans-serif"
PALETTE = {
    "primary": "#24418F",   # main text, outlines
    "secondary": "#5A78C8",
    "accent": "#10739E",
    "highlight": "#D9712B",  # reserve for "our contribution" / the point of the slide
    "muted": "#8A93A8",
    "light": "#E8EDF8",
}


class Svg:
    def __init__(self, w, h):
        self.w, self.h, self.parts = w, h, []

    def text(self, x, y, t, size=20, color=None, bold=False, italic=False, anchor="middle"):
        # PowerPoint garbles regular-weight italic, so italic is always bold.
        bold = bold or italic
        st = " font-style='italic'" if italic else ""
        self.parts.append(
            f"<text x='{x}' y='{y}' text-anchor='{anchor}' font-size='{size}' "
            f"font-weight='{'bold' if bold else 'normal'}' fill='{color or PALETTE['primary']}'{st}>{t}</text>")

    def rich(self, x, y, runs, size=22, color=None):
        """Inline runs with subscripts, e.g. [("T", 0), ("deploy", 1), (" = t", 0), ("ready", 1)].
        Each run is its own <text> at an estimated x: <tspan> flow is placed differently by each renderer."""
        for t, sub in runs:
            fs = size * 0.62 if sub else size
            # Leading/trailing spaces become x offsets: PowerPoint drops edge spaces inside <text>.
            core = t.strip()
            x += (len(t) - len(t.lstrip())) * 0.27 * fs
            self.text(round(x, 1), y + (size * 0.28 if sub else 0), core, round(fs), color, anchor="start")
            x += text_width(core, fs) + (len(t) - len(t.rstrip())) * 0.27 * fs

    def rect(self, x1, y1, x2, y2, fill="white", stroke=None, rx=10, width=2.5, dash=""):
        d = f" stroke-dasharray='{dash}'" if dash else ""
        self.parts.append(
            f"<rect x='{x1}' y='{y1}' width='{x2-x1}' height='{y2-y1}' rx='{rx}' fill='{fill}' "
            f"stroke='{stroke or fill}' stroke-width='{width}'{d}/>")

    def box(self, x1, y1, x2, y2, lines, fill="white", stroke=None, color=None, size=20):
        """Rounded box with one or more centered lines ('a|b' or a list)."""
        lines = lines.split("|") if isinstance(lines, str) else lines
        self.rect(x1, y1, x2, y2, fill, stroke)
        cy = (y1 + y2) / 2 - (len(lines) - 1) * size * 0.6
        for i, ln in enumerate(lines):
            self.text((x1 + x2) / 2, cy + i * size * 1.2 + size * 0.35, ln, size, color, bold=i == 0)

    def line(self, pts, color, dash="", width=3):
        d = f" stroke-dasharray='{dash}'" if dash else ""
        p = " ".join(f"{x},{y}" for x, y in pts)
        self.parts.append(f"<polyline points='{p}' fill='none' stroke='{color}' stroke-width='{width}'{d}/>")

    def arrow(self, x1, y1, x2, y2, color, dash=""):
        """Straight arrow; the head is a drawn triangle (SVG <marker> disappears in converters)."""
        a = math.atan2(y2 - y1, x2 - x1)
        bx, by = x2 - 14 * math.cos(a), y2 - 14 * math.sin(a)
        self.line([(x1, y1), (bx, by)], color, dash)
        p1 = (bx + 8 * math.sin(a), by - 8 * math.cos(a))
        p2 = (bx - 8 * math.sin(a), by + 8 * math.cos(a))
        self.parts.append(f"<path d='M{x2},{y2} L{p1[0]:.1f},{p1[1]:.1f} L{p2[0]:.1f},{p2[1]:.1f} Z' fill='{color}'/>")

    def label(self, x, y, t, color, bg="white", size=17):
        """Text on an opaque background so lines passing behind it stay readable."""
        w = len(t) * size * 0.55 + 12
        self.parts.append(f"<rect x='{x-w/2}' y='{y-size}' width='{w}' height='{size*1.45}' fill='{bg}'/>")
        self.text(x, y, t, size, color)

    def mark(self, cx, cy, kind, r=15):
        """Table icons drawn as shapes, not glyphs: 'y' yes, 'p' partial, 'n' no."""
        acc, mut = PALETTE["accent"], PALETTE["muted"]
        if kind == "y":
            self.parts.append(f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='{acc}'/>")
            self.parts.append(f"<path d='M{cx-7},{cy} l5,6 l10,-12' fill='none' stroke='white' stroke-width='3.5' stroke-linecap='round'/>")
        elif kind == "p":
            self.parts.append(f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='none' stroke='{acc}' stroke-width='2.5'/>")
            self.parts.append(f"<path d='M{cx},{cy-r} A{r},{r} 0 0 0 {cx},{cy+r} Z' fill='{acc}'/>")
        else:
            self.parts.append(f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='none' stroke='{mut}' stroke-width='2.5'/>")
            self.parts.append(f"<path d='M{cx-6},{cy-6} l12,12 M{cx+6},{cy-6} l-12,12' stroke='{mut}' stroke-width='3' stroke-linecap='round'/>")

    def svg(self):
        return (f"<svg xmlns='http://www.w3.org/2000/svg' width='{self.w}' height='{self.h}' "
                f"viewBox='0 0 {self.w} {self.h}' font-family='{FONT}'>\n" + "\n".join(self.parts) + "\n</svg>")

    def save(self, path):
        doc = self.svg()
        problems = lint(doc)
        if problems:
            raise ValueError("Not PowerPoint-safe:\n- " + "\n- ".join(problems))
        open(path, "w", encoding="utf-8").write(doc)


def text_width(t, size):
    """Rough width of regular sans text (Roboto/Arial metrics), good enough for placing runs."""
    w = 0
    for ch in t:
        if ch in "iljtI.,:;|!' ":
            w += 0.27
        elif ch in "rf()[]-":
            w += 0.36
        elif ch in "mwMW":
            w += 0.85
        elif ch.isupper():
            w += 0.65
        else:
            w += 0.56
    return w * size


def lint(doc):
    """Flag constructs that break in PowerPoint or in SVG-to-PNG converters."""
    out = []
    for m in re.finditer(r"<text[^>]*>", doc):
        tag = m.group(0)
        if re.search(r"font-style=['\"]italic", tag) and not re.search(r"font-weight=['\"](bold|700)", tag):
            out.append("regular-weight italic (PowerPoint garbles it): make it bold or drop italic")
        w = re.search(r"font-weight=['\"]([^'\"]+)", tag)
        if w and w.group(1) not in ("normal", "bold", "400", "700"):
            out.append(f"font-weight {w.group(1)}: use normal or bold only")
        if "rotate(" in tag or "writing-mode" in tag:
            out.append("rotated text: renderers place it inconsistently; use horizontal text")
    if "<tspan" in doc:
        out.append("<tspan> runs collapse onto one x in some renderers: use Svg.rich() (one <text> per run)")
    if "<marker" in doc:
        out.append("<marker> arrowheads vanish in converters: draw triangles")
    if "<style" in doc:
        out.append("CSS <style>: PowerPoint ignores it; use attributes")
    return sorted(set(out))


def render(svg_path, png_path, density=192):
    """SVG -> transparent PNG with whatever converter exists."""
    if shutil.which("rsvg-convert"):
        cmd = ["rsvg-convert", "-z", str(density / 96), "-b", "none", "-o", png_path, svg_path]
    elif shutil.which("convert") or shutil.which("magick"):
        cmd = [shutil.which("magick") or "convert", "-background", "none", "-density", str(density), svg_path, png_path]
    else:
        sys.exit("No converter: install librsvg2-bin or imagemagick, or screenshot the SVG with a headless browser.")
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    # Self-check: the lint catches the known PowerPoint breakers and passes clean output.
    bad = "<svg><text font-style='italic'>x</text><text font-weight='500'>y</text><marker/></svg>"
    assert len(lint(bad)) == 3, lint(bad)
    s = Svg(300, 120)
    s.box(20, 20, 140, 80, "A", stroke=PALETTE["primary"])
    s.arrow(140, 50, 260, 50, PALETTE["primary"])
    s.text(150, 110, "caption", italic=True)
    assert lint(s.svg()) == [], lint(s.svg())
    print("svgkit ok")
