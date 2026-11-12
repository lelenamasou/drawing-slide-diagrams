---
name: drawing-slide-diagrams
description: Use when someone needs a diagram, architecture figure, flow, sequence, timeline, funnel, or comparison-table image to insert into PowerPoint, Google Slides, Keynote, or a document, and there is no design tool at hand. Also use when an existing SVG shows garbled text, missing arrowheads, or misplaced labels after insertion.
---

# Drawing Slide Diagrams

## Overview

Write each figure as a small Python script that emits SVG, render it to PNG, look at the PNG, fix, repeat. The script is the source of truth: keep it next to the images so the figure can be edited later.

## Workflow

1. Read the colors and font the deck already uses. Copy `svgkit.py` (in this skill's folder) next to the figures and set `PALETTE`/`FONT` there.
2. Write `src/<figure>.py` beside the images folder. Never leave it only in a temp or scratch directory.
3. `python3 src/<figure>.py out.svg`, then `render()` to PNG (transparent background).
4. Open the PNG with the image viewer tool and check: text overlapping lines or borders, text cut at the canvas edge, labels sitting on container borders, arrowheads present, empty space to trim. Fix and re-render until clean.
5. Deliver the SVG (editable, sharp on projectors) and the PNG (fallback when fonts differ).

## PowerPoint-safe rules (enforced by `svgkit.lint`, which `save()` runs)

| Use | Not |
|---|---|
| Weights `normal` and `bold` only | 300, 500, 600 (missing font files get substituted or garbled) |
| Italic only together with bold | Regular italic: PowerPoint renders scrambled glyphs |
| Arrowheads as drawn triangles | `<marker>`: vanishes in converters |
| Horizontal text | `rotate()` or `writing-mode` on text: placed inconsistently |
| Attributes (`fill=`, `font-size=`) | CSS `<style>` blocks |
| Icons as shapes (`mark()`) | Unicode ✓ ✗ glyphs that the slide font may lack |
| Subscripts/formulas via `rich()` (one `<text>` per run, upright) | `<tspan dy>` flow: runs pile up at one x |

## Layout habits

- Labels on lines: use `label()` (opaque background) or place them beside the line, never across a lifeline or border.
- Container titles go where no line enters (often the bottom edge).
- Vertical figures for text-left/figure-right slides; wide figures for full-width slides under a title.
- Color carries meaning: one color per component type, one highlight color reserved for the slide's point. Reuse the same mapping across all figures of a deck.
- Text inside figures: short noun phrases, no sentences.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Declaring done without opening the PNG | Always view it; overlaps are invisible in code |
| Script left in a temp dir | Save under `src/`; add a README mapping script to figure |
| User says text looks garbled in PowerPoint | Regular italic or odd weight; run `lint`, or hand them the PNG |
| Changed the image file but slide still old | PowerPoint embeds a copy: Right-click, Change Picture, From File |
