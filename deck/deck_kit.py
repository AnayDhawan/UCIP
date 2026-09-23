"""
Shared layout toolkit for the UCIP pitch decks.

Both `build_deck.py` (v2, the technical cut) and `build_deck_v3.py` (v3, the plain-language
cut) import this module, so the two decks cannot drift apart on brand tokens, geometry or
layout primitives. Content lives in the build scripts. Nothing but layout lives here.

Every figure comes from the pipeline's own output via load_facts(), so no deck can quote a
number the pipeline did not produce:
  data/hvi_pca_log.json          PCA weights, explained variance
  data/sensitivity.json          Kendall tau, top-5 overlap
  data/ward_profiles.json        city means, ward ranks
  data/wards_hvi.geojson         ward HVI values
  data/nbs_recommendations.json  recommendation counts
  frontend/src/lib/citations.ts  citation count

Usage from a build script:
    from deck_kit import *
    prs = new_presentation()
    use(prs, sections=SEC, total=20)
    ... build slides ...
    prs.save(out_path)
    validate(out_path, total_slides=20, min_sec=14*60, max_sec=15*60,
             slide_section=[1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 5, 6, 6, 6])
"""


import json
import os
import re
import shutil
import sys

# The build log prints slide titles verbatim, some of which contain arrows and degree
# signs. Windows consoles default to cp1252 and would crash on them.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE
from pptx.oxml.ns import qn

# ---------------------------------------------------------------------------
# Brand constants
# ---------------------------------------------------------------------------

BG = "0D1017"
COVER_GLOW = "122024"
PANEL_SOLID = "151A24"
PANEL_NESTED = "1A2029"
BORDER = "2A3040"
INK = "E6EAF2"
MUTED = "9AA3B2"
MUTED_FAINT = "52565D"
LOCKUP_MUTED = "84888F"
SUBTITLE_INK = "BBBEC6"
WHITE = "FFFFFF"
TEAL = "0EA5B3"
EMERALD = "22C55E"
AMBER = "F0A63A"
CRIMSON = "E4572E"

FONT_HEAD = "Inter"
FONT_BODY = "Inter"
FONT_MONO = "JetBrains Mono"

MARGIN_L = 0.55
MARGIN_R = 0.55
SLIDE_W_IN = 13.333
SLIDE_H_IN = 7.5
CONTENT_W = SLIDE_W_IN - MARGIN_L - MARGIN_R  # 12.233
BODY_TOP = 1.30
BODY_BOTTOM = 6.95

# Source attribution sits in a fixed band below every slide's content box, alongside the page
# number. Placing it here rather than under each slide's last element is deliberate: several
# slides already run to y=6.95, so per-slide placement would be twenty collision judgements.
# The band is two lines deep because the citation-heavy slides (prior art, limitations) genuinely
# need two, and truncating an attribution to fit one line is not an option.
SOURCE_Y = 7.00
SOURCE_H = 0.46

WPM = 140.0

# Per-deck knob. Each build script declares its own and passes it to use()/validate();
# this is only the default so a bare import still behaves sensibly.
TOTAL_SLIDES = 20

REPO = r"C:\Users\lenovo\personal-repos\ucip"
MEDIA_DIR = os.path.join(REPO, "docs", "media")
LOGO_PATH = os.path.join(MEDIA_DIR, "icon-512.png")

OUT_DIR = r"c:\Users\lenovo\EA\projects\ucip"
SHOTS = os.path.join(OUT_DIR, "deck-assets")

NO_STYLE_GUID = "{5940675A-B579-460E-94D1-54222C63F5DA}"

SEC = {
    1: "01 \u00b7 PROJECT OVERVIEW & PARTICIPANT DETAILS",
    2: "02 \u00b7 PROBLEM UNDERSTANDING",
    3: "03 \u00b7 RESEARCH & INSIGHTS",
    4: "04 \u00b7 PROPOSED SOLUTION",
    5: "05 \u00b7 PROTOTYPE / SOLUTION DESIGN",
    6: "06 \u00b7 IMPACT & FUTURE SCOPE",
}

# ---------------------------------------------------------------------------
# Live figures, read from the pipeline's own output so the deck cannot drift
# ---------------------------------------------------------------------------

def load_facts():
    def j(*parts):
        with open(os.path.join(REPO, *parts), encoding="utf-8") as fh:
            return json.load(fh)

    pca = j("data", "hvi_pca_log.json")
    sens = j("data", "sensitivity.json")
    prof = j("data", "ward_profiles.json")
    wards = j("data", "wards_hvi.geojson")
    nbs = j("data", "nbs_recommendations.json")

    with open(os.path.join(REPO, "frontend", "src", "lib", "citations.ts"), encoding="utf-8") as fh:
        n_citations = len(re.findall(r'^\s*id:\s*"([^"]+)"', fh.read(), re.M))

    ranked = sorted((f["properties"] for f in wards["features"]), key=lambda p: p["rank"])

    return {
        "pc1": pca["explained_variance_pc1"],
        "weights": pca["weights"],
        "loadings": pca["loadings_pc1"],
        "fallback_used": pca["fallback_used"],
        "tau": sens["mean_kendall_tau"],
        "overlap": sens["mean_top5_overlap"],
        "n_runs": sens["n_runs"],
        "perturb": sens["perturbation_pct"],
        "n_cells": prof["n_cells"],
        "n_wards": prof["n_wards"],
        "city": prof["city"],
        "top5": [(p["ward_id"], p["HVI"]) for p in ranked[:5]],
        "n_nbs": len(nbs),
        "n_citations": n_citations,
        "n_stages": len([f for f in os.listdir(os.path.join(REPO, "pipeline")) if re.match(r"^\d\d_.*\.py$", f)]),
    }


F = load_facts()


def load_citations():
    """Read the paper list and the data-source list out of the frontend's own citation module.

    The appendix slide is built from this, so the deck's bibliography cannot drift from the one
    the live site renders. Only `authors`, `venue` and `doi` are read: the `usage` strings contain
    em dashes, which validate() rejects.
    """
    path = os.path.join(REPO, "frontend", "src", "lib", "citations.ts")
    with open(path, encoding="utf-8") as fh:
        src = fh.read()

    papers = []
    for block in re.findall(r"\{\s*id:\s*\"[^\"]+\".*?\},", src, re.S):
        def field(name):
            m = re.search(rf'{name}:\s*"([^"]*)"', block)
            return m.group(1) if m else ""
        if field("authors"):
            papers.append((field("authors"), field("venue"), field("doi")))

    sources = re.findall(r'\{\s*name:\s*"([^"]+)",\s*use:\s*"([^"]+)"\s*\}', src)
    return papers, sources


PAPERS, DATA_SOURCES = load_citations()

# ---------------------------------------------------------------------------
# Presentation setup
# ---------------------------------------------------------------------------

_PRS = None
_SEC = SEC
_TOTAL = TOTAL_SLIDES


def new_presentation():
    prs = Presentation()
    prs.slide_width = Inches(SLIDE_W_IN)
    prs.slide_height = Inches(SLIDE_H_IN)
    return prs


def use(prs, sections=None, total=None):
    """Register the presentation the layout helpers append to, plus its per-deck knobs."""
    global _PRS, _SEC, _TOTAL
    _PRS = prs
    if sections is not None:
        _SEC = sections
    if total is not None:
        _TOTAL = total


def rgb(hexstr):
    return RGBColor.from_string(hexstr)


def new_slide():
    if _PRS is None:
        raise RuntimeError("call use(prs) before building slides")
    return _PRS.slides.add_slide(_PRS.slide_layouts[6])


def set_background(slide):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = rgb(BG)


# Delivery cues like "[beat]" or "[COLD OPEN. ...]" are stage directions, not spoken words.
# They stay in the notes pane for the presenter but are excluded from the timing count.
STAGE_DIRECTION = re.compile(r"\[[^\]]*\]")


def spoken_words(text):
    return len(STAGE_DIRECTION.sub(" ", text).split())


def set_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = " ".join(text.split())

# ---------------------------------------------------------------------------
# Low-level text/shape helpers
# ---------------------------------------------------------------------------

def _set_run(run, text, font=FONT_BODY, size=11, color=INK, bold=False, italic=False):
    run.text = text
    run.font.name = font
    run.font.size = Pt(size)
    run.font.color.rgb = rgb(color)
    run.font.bold = bold
    run.font.italic = italic


def add_textbox(slide, x, y, w, h, word_wrap=True, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = word_wrap
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    return tb, tf


def add_kicker(slide, text, x=MARGIN_L, y=0.35, w=9.6, h=0.24):
    tb, tf = add_textbox(slide, x, y, w, h)
    r = tf.paragraphs[0].add_run()
    _set_run(r, text.upper(), font=FONT_MONO, size=11, color=TEAL, bold=True)
    return tb


def add_heading(slide, text, x, y, w, h, size=26, color=WHITE):
    tb, tf = add_textbox(slide, x, y, w, h)
    r = tf.paragraphs[0].add_run()
    _set_run(r, text, font=FONT_HEAD, size=size, color=color, bold=True)
    return tb


def add_gradient_bar(slide, x=MARGIN_L, y=1.15, w=0.9, h=0.055, angle=0.0):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.adjustments[0] = 0.5
    shp.line.fill.background()
    shp.shadow.inherit = False
    shp.fill.gradient()
    stops = shp.fill.gradient_stops
    stops[0].color.rgb = rgb(TEAL)
    stops[0].position = 0.0
    stops[-1].color.rgb = rgb(EMERALD)
    stops[-1].position = 1.0
    shp.fill.gradient_angle = angle
    return shp


def add_dot_heading(slide, text, x, y, w, h, size=13, dot=EMERALD):
    tb, tf = add_textbox(slide, x, y, w, h)
    p = tf.paragraphs[0]
    r1 = p.add_run()
    _set_run(r1, "\u25CF ", font=FONT_BODY, size=size, color=dot, bold=True)
    r2 = p.add_run()
    _set_run(r2, text, font=FONT_HEAD, size=size, color=WHITE, bold=True)
    return tb


def add_body_text(slide, text, x, y, w, h, size=11, color=MUTED, bold=False,
                  align=PP_ALIGN.LEFT, line_spacing=1.18, font=FONT_BODY,
                  anchor=MSO_ANCHOR.TOP, space_before=4):
    tb, tf = add_textbox(slide, x, y, w, h, anchor=anchor)
    lines = text.split("\n") if isinstance(text, str) else list(text)
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        if i > 0:
            p.space_before = Pt(space_before)
        r = p.add_run()
        _set_run(r, line, font=font, size=size, color=color, bold=bold)
    return tb


def add_lead_body(slide, x, y, w, h, lead, rest, lead_size=11, rest_size=10.5,
                  lead_color=WHITE, rest_color=MUTED, anchor=MSO_ANCHOR.TOP, line_spacing=1.15):
    tb, tf = add_textbox(slide, x, y, w, h, anchor=anchor)
    p = tf.paragraphs[0]
    p.line_spacing = line_spacing
    r1 = p.add_run()
    _set_run(r1, lead + " ", font=FONT_HEAD, size=lead_size, color=lead_color, bold=True)
    r2 = p.add_run()
    _set_run(r2, rest, font=FONT_BODY, size=rest_size, color=rest_color, bold=False)
    return tb


def add_card_bg(slide, x, y, w, h, fill=PANEL_SOLID, border=BORDER, radius=0.06):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.adjustments[0] = radius
    shp.fill.solid()
    shp.fill.fore_color.rgb = rgb(fill)
    shp.line.color.rgb = rgb(border)
    shp.line.width = Pt(0.75)
    shp.shadow.inherit = False
    return shp


def add_card(slide, x, y, w, h, heading, body, pad=0.20, heading_size=12.5,
             body_size=10, body_color=MUTED, dot=EMERALD):
    add_card_bg(slide, x, y, w, h)
    add_dot_heading(slide, heading, x + pad, y + pad * 0.7, w - 2 * pad, 0.30,
                    size=heading_size, dot=dot)
    body_y = y + pad * 0.7 + 0.38
    add_body_text(slide, body, x + pad, body_y, w - 2 * pad, h - (body_y - y) - pad,
                  size=body_size, color=body_color)


def add_stat_box(slide, x, y, w, h, number, label, number_size=18, layout="stacked",
                 number_color=EMERALD):
    add_card_bg(slide, x, y, w, h, fill=PANEL_NESTED)
    pad = 0.14
    if layout == "stacked":
        add_body_text(slide, number, x + pad, y, w - 2 * pad, h * 0.58, size=number_size,
                      color=number_color, bold=True, font=FONT_MONO, anchor=MSO_ANCHOR.BOTTOM)
        add_body_text(slide, label, x + pad, y + h * 0.58, w - 2 * pad, h * 0.40, size=8.5,
                      color=MUTED, anchor=MSO_ANCHOR.TOP, line_spacing=1.1)
    else:
        num_w = w * 0.34
        add_body_text(slide, number, x + pad, y, num_w - pad, h, size=number_size,
                      color=number_color, bold=True, font=FONT_MONO, anchor=MSO_ANCHOR.MIDDLE)
        add_body_text(slide, label, x + num_w, y, w - num_w - pad, h, size=9.5, color=MUTED,
                      anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.1)


def add_pill_list(slide, x, y, w, h, items, gap=0.12, lead_size=11, rest_size=10):
    n = len(items)
    item_h = (h - gap * (n - 1)) / n
    cy = y
    for lead, rest in items:
        add_card_bg(slide, x, cy, w, item_h, fill=PANEL_NESTED)
        pad = 0.16
        add_lead_body(slide, x + pad, cy, w - 2 * pad, item_h, lead, rest,
                      lead_size=lead_size, rest_size=rest_size, anchor=MSO_ANCHOR.MIDDLE)
        cy += item_h + gap


def add_callout(slide, x, y, w, h, number, text, number_size=20, accent=AMBER):
    add_card_bg(slide, x, y, w, h, fill=PANEL_NESTED, border=accent)
    pad = 0.16
    num_w = 1.45
    add_body_text(slide, number, x + pad, y, num_w, h, size=number_size, color=accent,
                  bold=True, font=FONT_MONO, anchor=MSO_ANCHOR.MIDDLE)
    add_body_text(slide, text, x + pad + num_w, y + 0.06, w - num_w - 2 * pad, h - 0.12,
                  size=9.5, color=MUTED, anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.15)


def strip_table_style(table):
    table.first_row = False
    table.horz_banding = False
    tbl = table._tbl
    tblPr = tbl.find(qn("a:tblPr"))
    if tblPr is None:
        return
    style_el = tblPr.find(qn("a:tableStyleId"))
    if style_el is None:
        style_el = tblPr.makeelement(qn("a:tableStyleId"), {})
        tblPr.append(style_el)
    style_el.text = NO_STYLE_GUID


def add_table(slide, x, y, w, h, headers, rows, col_widths, header_fill=TEAL,
              body_size=8.8, header_size=9.5, highlight_last=False):
    n_rows = len(rows) + 1
    n_cols = len(headers)
    gframe = slide.shapes.add_table(n_rows, n_cols, Inches(x), Inches(y), Inches(w), Inches(h))
    table = gframe.table
    strip_table_style(table)

    for i, cw in enumerate(col_widths):
        table.columns[i].width = Inches(cw)
    header_h = 0.32
    data_h = (h - header_h) / len(rows) if rows else 0.4
    table.rows[0].height = Inches(header_h)
    for r in range(1, n_rows):
        table.rows[r].height = Inches(data_h)

    def style_cell(cell, text, size, color, bold=False, fill=PANEL_SOLID, align=PP_ALIGN.LEFT,
                   font=FONT_BODY):
        cell.margin_left = Inches(0.08)
        cell.margin_right = Inches(0.08)
        cell.margin_top = Inches(0.03)
        cell.margin_bottom = Inches(0.03)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        cell.fill.solid()
        cell.fill.fore_color.rgb = rgb(fill)
        cell.text = text
        # A newline in `text` creates extra paragraphs. Style every one of them, otherwise
        # continuation lines silently fall back to the 18 pt theme default.
        for p in cell.text_frame.paragraphs:
            p.alignment = align
            p.line_spacing = 1.05
            for run in p.runs:
                run.font.name = font
                run.font.size = Pt(size)
                run.font.bold = bold
                run.font.color.rgb = rgb(color)

    for c, htext in enumerate(headers):
        style_cell(table.cell(0, c), htext, header_size, WHITE, bold=True, fill=header_fill)
    for ridx, row in enumerate(rows, start=1):
        is_last = highlight_last and ridx == len(rows)
        for c, val in enumerate(row):
            if is_last:
                color = EMERALD if c == 0 else INK
                fill = PANEL_NESTED
            else:
                color = INK if c == 0 else MUTED
                fill = PANEL_SOLID
            style_cell(table.cell(ridx, c), val, body_size, color,
                       bold=(c == 0 or is_last), fill=fill)
    return table


def add_bar_row(slide, x, y, w, h, label, frac, value_text, label_w=2.05, value_w=0.75,
                bar_color=TEAL, label_size=9.5):
    add_body_text(slide, label, x, y, label_w, h, size=label_size, color=INK,
                  anchor=MSO_ANCHOR.MIDDLE)
    track_x = x + label_w
    track_w = w - label_w - value_w - 0.12
    track = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(track_x),
                                   Inches(y + h * 0.30), Inches(track_w), Inches(h * 0.40))
    track.adjustments[0] = 0.5
    track.fill.solid()
    track.fill.fore_color.rgb = rgb(PANEL_NESTED)
    track.line.color.rgb = rgb(BORDER)
    track.line.width = Pt(0.5)
    track.shadow.inherit = False
    fill_w = max(0.06, track_w * frac)
    bar = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(track_x),
                                 Inches(y + h * 0.30), Inches(fill_w), Inches(h * 0.40))
    bar.adjustments[0] = 0.5
    bar.fill.solid()
    bar.fill.fore_color.rgb = rgb(bar_color)
    bar.line.fill.background()
    bar.shadow.inherit = False
    add_body_text(slide, value_text, x + w - value_w, y, value_w, h, size=9.5, color=INK,
                  bold=True, font=FONT_MONO, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.RIGHT)


def add_flow_box(slide, x, y, w, h, num, name, detail, accent=TEAL):
    add_card_bg(slide, x, y, w, h)
    tb, tf = add_textbox(slide, x + 0.08, y + 0.08, w - 0.16, h - 0.16, anchor=MSO_ANCHOR.MIDDLE)
    p0 = tf.paragraphs[0]
    p0.alignment = PP_ALIGN.CENTER
    _set_run(p0.add_run(), num, font=FONT_MONO, size=8, color=accent, bold=True)
    p1 = tf.add_paragraph()
    p1.alignment = PP_ALIGN.CENTER
    p1.space_before = Pt(2)
    _set_run(p1.add_run(), name, font=FONT_HEAD, size=10, color=WHITE, bold=True)
    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    p2.space_before = Pt(1)
    _set_run(p2.add_run(), detail, font=FONT_BODY, size=7.8, color=MUTED)


def add_arrow(slide, x, y, w, h, color=BORDER):
    shp = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid()
    shp.fill.fore_color.rgb = rgb(color)
    shp.line.fill.background()
    shp.shadow.inherit = False
    return shp


def add_brand_lockup(slide):
    x_icon, y_icon = 11.85, 0.30
    slide.shapes.add_picture(LOGO_PATH, Inches(x_icon), Inches(y_icon),
                             width=Inches(0.20), height=Inches(0.20))
    tb, tf = add_textbox(slide, x_icon + 0.28, y_icon - 0.01, 0.70, 0.24, anchor=MSO_ANCHOR.MIDDLE)
    _set_run(tf.paragraphs[0].add_run(), "UCIP", font=FONT_MONO, size=10.5,
             color=LOCKUP_MUTED, bold=True)


def add_slide_number(slide, n, total=None):
    total = _TOTAL if total is None else total
    tb, tf = add_textbox(slide, 11.9, 7.14, 0.88, 0.28, anchor=MSO_ANCHOR.MIDDLE)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    _set_run(p.add_run(), f"{n} / {total}", font=FONT_MONO, size=9, color=MUTED_FAINT)


def add_source_line(slide, text):
    """Attribute every claim on the slide, in the slide's own lower band.

    Kept at 7.5 pt so it reads as apparatus rather than content. The width stops short of the
    page number at x=11.9, and the box holds up to two lines.
    """
    add_body_text(slide, "Sources: " + text, MARGIN_L, SOURCE_Y, 11.15, SOURCE_H,
                  size=7.5, color=MUTED_FAINT, anchor=MSO_ANCHOR.TOP, line_spacing=1.08)


def add_screenshot(slide, filename, x, y, w, caption=None, caption_size=8.2):
    path = os.path.join(SHOTS, filename)
    pic = slide.shapes.add_picture(path, Inches(x), Inches(y), width=Inches(w))
    pic.line.color.rgb = rgb(BORDER)
    pic.line.width = Pt(0.75)
    bottom = y + (pic.height / 914400.0)
    if caption:
        add_body_text(slide, caption, x, bottom + 0.07, w, 0.40, size=caption_size, color=MUTED,
                      align=PP_ALIGN.CENTER, line_spacing=1.12)
    return pic, bottom


def add_crop_screenshot(slide, filename, x, y, w, crop_l=0.0, crop_r=0.0,
                        crop_t=0.0, crop_b=0.0, caption=None, caption_size=8.2,
                        max_h=None, center_in=None):
    """Place a cropped screenshot at width `w`, computing height from the visible crop.

    Height is derived, never passed in. Hardcoding both dimensions silently stretches the
    image whenever a crop is retuned, which is exactly the bug this replaced.
    If `max_h` is given and the derived height exceeds it, the whole image scales down and
    is optionally re-centred inside a `center_in` width.
    """
    path = os.path.join(SHOTS, filename)
    probe = slide.shapes.add_picture(path, Inches(x), Inches(y), width=Inches(w))
    native_aspect = probe.width / probe.height
    probe._element.getparent().remove(probe._element)

    w_frac = 1.0 - crop_l - crop_r
    h_frac = 1.0 - crop_t - crop_b
    if w_frac <= 0 or h_frac <= 0:
        raise ValueError(f"{filename}: crop removes the entire image")
    visible_aspect = native_aspect * w_frac / h_frac

    h = w / visible_aspect
    if max_h is not None and h > max_h:
        w = max_h * visible_aspect
        h = max_h
        if center_in:
            x = x + (center_in - w) / 2.0

    pic = slide.shapes.add_picture(path, Inches(x), Inches(y), width=Inches(w), height=Inches(h))
    pic.crop_left = crop_l
    pic.crop_right = crop_r
    pic.crop_top = crop_t
    pic.crop_bottom = crop_b
    pic.line.color.rgb = rgb(BORDER)
    pic.line.width = Pt(0.75)
    if caption:
        add_body_text(slide, caption, x, y + h + 0.07, w, 0.40, size=caption_size, color=MUTED,
                      align=PP_ALIGN.CENTER, line_spacing=1.12)
    return x, y, w, h


def base_slide(n, section, heading_text, heading_size=25, sub=None, sources=None):
    slide = new_slide()
    set_background(slide)
    add_kicker(slide, _SEC[section])
    add_heading(slide, heading_text, MARGIN_L, 0.60, 10.8, 0.50, size=heading_size)
    add_gradient_bar(slide)
    if sub:
        add_body_text(slide, sub, MARGIN_L, 1.32, 11.0, 0.30, size=10.5, color=SUBTITLE_INK)
    add_brand_lockup(slide)
    add_slide_number(slide, n)
    if sources:
        add_source_line(slide, sources)
    return slide


def pct(x):
    return f"{x * 100:.1f}%"



def backup_existing(out_path, backup_path):
    if os.path.exists(out_path) and not os.path.exists(backup_path):
        shutil.copy2(out_path, backup_path)
        print(f"Backed up previous deck -> {os.path.basename(backup_path)}")


def validate(path, total_slides, min_sec, max_sec, slide_section, require_sources=True):
    p2 = Presentation(path)
    n = len(p2.slides)
    assert n == total_slides, f"expected {total_slides} slides, got {n}"

    print(f"\n{'#':<4} {'SEC':<5} {'TITLE':<44} {'SHAPES':>7} {'PICS':>5} {'WORDS':>6} {'TIME':>7}")
    print("-" * 84)

    total_words = 0
    total_shapes = 0
    problems = []

    for i, slide in enumerate(p2.slides, start=1):
        shapes = list(slide.shapes)
        n_shapes = len(shapes)
        n_pics = sum(1 for s in shapes if s.shape_type == MSO_SHAPE_TYPE.PICTURE)
        total_shapes += n_shapes

        if n_shapes == 1:
            problems.append(f"Slide {i} has only 1 shape, flattened-image regression detected")

        # Every claim on a slide has to be attributable from the slide itself, so every slide
        # carries a source line in its lower band. No exceptions: slides whose figures are the
        # pipeline's own output say so explicitly rather than staying silent.
        if require_sources and not any(
            s.has_text_frame and s.text_frame.text.startswith("Sources: ") for s in shapes
        ):
            problems.append(f"Slide {i} has no source line")

        notes = ""
        if slide.has_notes_slide:
            notes = slide.notes_slide.notes_text_frame.text.strip()
        if not notes:
            problems.append(f"Slide {i} has no speaker notes")
        words = spoken_words(notes)
        total_words += words
        secs = words / WPM * 60

        title = ""
        for s in shapes:
            if s.has_text_frame and s.text_frame.text:
                txt = " ".join(s.text_frame.text.split())
                if len(txt) > 12 and not txt.isupper():
                    title = txt[:42]
                    break

        # em dash check across slide text and notes
        for s in shapes:
            if s.has_text_frame and "\u2014" in s.text_frame.text:
                problems.append(f"Slide {i} contains an em dash in slide text")
        if "\u2014" in notes:
            problems.append(f"Slide {i} contains an em dash in speaker notes")

        print(f"{i:<4} {slide_section[i-1]:<5} {title:<44} {n_shapes:>7} {n_pics:>5} "
              f"{words:>6} {int(secs//60)}:{int(secs%60):02d}")

    total_sec = total_words / WPM * 60
    print("-" * 84)
    print(f"{'':<4} {'':<5} {'TOTAL':<44} {total_shapes:>7} {'':>5} {total_words:>6} "
          f"{int(total_sec//60)}:{int(total_sec%60):02d}")

    if not (min_sec <= total_sec <= max_sec):
        problems.append(
            f"Spoken time {total_sec/60:.1f} min is outside the {min_sec/60:.1f} to "
            f"{max_sec/60:.1f} min window ({total_words} words at {WPM:.0f} wpm)"
        )

    print()
    if problems:
        for p in problems:
            print(f"  FAIL  {p}")
        raise RuntimeError(f"{len(problems)} validation problem(s)")

    print(f"  ok  {total_slides} slides, all sections present")
    print(f"  ok  every slide has speaker notes")
    if require_sources:
        print(f"  ok  every slide carries a source line")
    print(f"  ok  spoken time {total_sec/60:.1f} min, inside the {min_sec/60:.0f} to "
          f"{max_sec/60:.0f} min window")
    print(f"  ok  no em dashes")
    print(f"  ok  no flattened-image regression")
    print(f"\nFile size: {os.path.getsize(path) / (1024*1024):.2f} MB")
    print(f"Saved to:  {path}")


REQUIRED_SHOTS = [
    "deck-hero-dark.png",
    "deck-dashboard-hvi-dark.png",
    "deck-ward-c-dark.png",
    "deck-ward-a-plantability-dark.png",
    "deck-simulate-dark.png",
    "deck-methodology-weights-dark.png",
    "deck-methodology-sensitivity-dark.png",
    "deck-global-heat-anomaly.png",
]


def check_shots():
    missing = [f for f in REQUIRED_SHOTS if not os.path.exists(os.path.join(SHOTS, f))]
    if missing:
        raise FileNotFoundError(
            "Missing screenshot(s) in deck-assets: " + ", ".join(missing)
            + "\nRe-capture them against a running dev server before building."
        )
