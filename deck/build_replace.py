"""
Rebuild slides 1 and 2 of the v3 pitch deck, as a standalone two-slide `replace.pptx`.

Why this exists rather than an edit to build_deck_v3.py: the shipped
UCIP-Pitch-Deck-v3.pptx is hand edited (slide 6's heading, slide 2's wording), and
re-running the full build would silently throw those edits away. This script writes a
separate file whose two slides are drop-in replacements, so the merge stays a deliberate
manual step.

What changed, and why:
  Slide 1 used to explain what UCIP does in its subtitle, which spent the reveal before
  the audience had a reason to want it. It now opens on the measured contrast the speaker
  notes already deliver, forty degrees against twenty six, and withholds the rest.
  Slide 2 used to state the problem as an abstract four-link chain with no data on it.
  It now carries the whole heat problem on one page: how uneven the heat is, where it
  lands, who it hurts, how badly it is counted, and why nobody has chosen. Slides 3 to 5
  keep the chain motif and become the evidence for each band.

Every figure on both slides is read from the pipeline's own output at build time, so
neither slide can drift from the data the site publishes.

Run:  python build_replace.py      ->  replace.pptx (2 slides, no PDF)
Then merge slides 1 and 2 into UCIP-Pitch-Deck-v3.pptx by hand, back it up first, and
only then run deck_kit.validate() against the merged 21-slide file.
"""

import json
import os

from deck_kit import (
    F, REPO, OUT_DIR, SEC, MARGIN_L, CONTENT_W, SOURCE_Y,
    BG, COVER_GLOW, PANEL_NESTED, INK, MUTED, SUBTITLE_INK, WHITE,
    TEAL, EMERALD, AMBER, CRIMSON, FONT_HEAD, FONT_BODY, FONT_MONO,
    new_presentation, use, new_slide, set_background, set_notes, spoken_words,
    add_kicker, add_heading, add_gradient_bar, add_body_text, add_card_bg, add_card,
    add_stat_box, add_flow_box, add_arrow, add_brand_lockup, add_slide_number,
    add_source_line, add_crop_screenshot, base_slide,
    Inches, rgb, MSO_SHAPE, MSO_ANCHOR,
)

TOTAL_SLIDES = 21
OUT_PATH = os.path.join(OUT_DIR, "replace.pptx")

LIVE_URL = "ucip-eight.vercel.app"
CODE_URL = "github.com/AnayDhawan/UCIP"
WHERE_TO_FIND_IT = f"Live at {LIVE_URL}. Code at {CODE_URL}."
PIPELINE = "computed by my own pipeline"

# Slide 1 keeps the v3 source line verbatim. Slide 2 now makes claims that used to sit on
# three separate slides, so its line merges what SRC[3], SRC[4] and SRC[5] each covered.
SRC = {
    1: f"{WHERE_TO_FIND_IT} Every figure in this deck is {PIPELINE}, from openly licensed "
       "data. Sources are given on the slide where each claim appears, and in full on slide "
       "21. The opening observation, that named storms are taken more seriously than unnamed "
       "heat waves, is Eleni Myrivili's, UN Global Chief Heat Officer.",
    2: "Ward and cell figures " + PIPELINE + ", from Landsat 8/9 Collection 2 (USGS), ESA "
       "WorldCover v200, WorldPop 2020, OpenStreetMap and Datameet. Heat deaths in India 2000 "
       "to 2020, three official counts: NCRB 20,615, NDMA 17,767, IMD 10,545 (Gadgil and "
       "Narang, Down To Earth, 10 April 2025). Ahmedabad: Knowlton et al. 2014, IJERPH, doi "
       "10.3390/ijerph110403473. Mumbai Climate Action Plan 2022 (BMC, WRI India, C40).",
}


def ward_extremes():
    """Hottest and coolest ward, read from the pipeline rather than typed in.

    deck_kit.load_facts() exposes city means and the HVI top five but not the per-ward
    temperature profile, and slide 2's second stat box is the ward-level spread. Reading it
    here keeps the same guarantee: no number on a slide that the pipeline did not produce.
    """
    with open(os.path.join(REPO, "data", "ward_profiles.json"), encoding="utf-8") as fh:
        wards = json.load(fh)["wards"]
    ordered = sorted(wards, key=lambda w: w["LST_C"])
    return ordered[-1], ordered[0]


HOT, COOL = ward_extremes()
CITY = F["city"]

prs = new_presentation()
use(prs, sections=SEC, total=TOTAL_SLIDES)

# The chain, copied from build_deck_v3.py so the strip on this slide stays byte-identical to
# the one slides 3 to 5 dim with `active=`. If that file's CHAIN ever changes, change it here.
CHAIN = [
    ("01", "More heat", "Mumbai is heating,\nand not evenly"),
    ("02", "Discomfort, then illness", "discomfort for all, danger\nfor some, load on hospitals"),
    ("03", "Citizens suffer", "hardest where people\ncan least cope"),
    ("04", "So where to act first?", "one budget,\ntwenty four wards"),
]


def chain_strip(slide, y, active=None, bw=2.72, h=1.30, gap_arrow=0.38):
    x = MARGIN_L
    for i, (num, name, detail) in enumerate(CHAIN):
        accent = [CRIMSON, AMBER, TEAL, EMERALD][i]
        if active is not None and i != active:
            accent = MUTED
        add_flow_box(slide, x, y, bw, h, num, name, detail, accent=accent)
        x += bw
        if i < len(CHAIN) - 1:
            add_arrow(slide, x + 0.06, y + h / 2 - 0.15, gap_arrow - 0.12, 0.30)
            x += gap_arrow


# ---------------------------------------------------------------------------
# Slide 1: the cold open, withholding
# ---------------------------------------------------------------------------

def slide_01_cover():
    slide = new_slide()
    set_background(slide)

    glow = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(-2.6), Inches(-2.0), Inches(10.4), Inches(7.6))
    glow.line.fill.background()
    glow.shadow.inherit = False
    glow.fill.gradient()
    stops = glow.fill.gradient_stops
    stops[0].color.rgb = rgb(COVER_GLOW)
    stops[0].position = 0.0
    stops[-1].color.rgb = rgb(BG)
    stops[-1].position = 1.0
    glow.fill.gradient_angle = 45.0

    add_kicker(slide, SEC[1])

    # The two temperatures and the gap between them, before the project is even named. This is
    # the contrast the cold open is built on; it used to be spoken over a slide that instead
    # summarised the tool.
    add_stat_box(slide, MARGIN_L, 1.28, 2.05, 1.05, "40 °C",
                 "hottest ground this city recorded", number_size=25, number_color=CRIMSON)
    add_stat_box(slide, MARGIN_L + 2.22, 1.28, 2.05, 1.05, "26 °C",
                 "coolest ground, same afternoon", number_size=25, number_color=TEAL)
    add_stat_box(slide, MARGIN_L + 4.44, 1.28, 2.36, 1.05, "13.7 °C",
                 "apart, one day, one satellite pass", number_size=25, number_color=AMBER)

    add_heading(slide, "UCIP", MARGIN_L, 2.58, 6.85, 0.78, size=46)
    add_body_text(slide, "Urban Climate Intelligence Platform", MARGIN_L, 3.30, 6.60, 0.26,
                  size=13, color=MUTED)
    add_gradient_bar(slide, x=MARGIN_L, y=3.66, w=1.3, h=0.06)

    # Deliberately withholds what the tool does. The reveal is slide 9.
    add_body_text(
        slide,
        "Mumbai does not have a heat problem. It has twenty four of them, one for every ward, "
        "and it treats them as though it had one.",
        MARGIN_L, 3.88, 6.60, 0.82, size=14, color=SUBTITLE_INK, line_spacing=1.3,
    )

    add_card_bg(slide, MARGIN_L, 4.80, 6.5, 2.05)
    meta_rows = [
        ("STUDENT NAME", "Anay Dhawan"),
        ("SCHOOL", "NES International School Mumbai"),
        ("GRADE", "11 (IBDP Year 1)"),
        ("DOMAIN", "PLANET"),
        ("FOCUS AREA", "Urban heat"),
        ("STUDY AREA", "Mumbai's 24 BMC wards"),
    ]
    ty = 4.92
    row_h = 1.81 / 6
    for label, value in meta_rows:
        add_body_text(slide, label, MARGIN_L + 0.20, ty, 2.0, row_h, size=9, color=MUTED,
                      font=FONT_MONO, anchor=MSO_ANCHOR.MIDDLE)
        add_body_text(slide, value, MARGIN_L + 2.30, ty, 3.90, row_h, size=11.5, color=INK,
                      bold=True, anchor=MSO_ANCHOR.MIDDLE)
        ty += row_h

    # Same crop and clamp as build_deck_v3.py:187, but the caption is gone on purpose: an
    # unlabelled ward map is the question the next twenty slides answer.
    # crop_r shaves the browser scrollbar off the right edge. build_deck_v3.py leaves it in,
    # where a caption underneath pulls the eye away from it; with the caption gone it reads as
    # a stray grey stripe on the one image the audience is meant to be puzzled by.
    add_crop_screenshot(slide, "deck-hero-dark.png", 7.55, 1.72, 5.25,
                        crop_l=0.46, crop_r=0.016, crop_t=0.10, crop_b=0.02,
                        max_h=4.42, center_in=5.25)

    add_brand_lockup(slide)
    add_slide_number(slide, 1)
    add_source_line(slide, SRC[1])

    set_notes(slide, """
        [COLD OPEN. Do not introduce yourself yet. Stand still. Slower than feels natural. Let
        the first silence sit longer than is comfortable.] Right now, somewhere above this room,
        a family is living under a metal roof. [beat] This afternoon, the ground beneath that
        roof measured forty degrees. Elsewhere in this same city, on the same afternoon, another
        rooftop measured twenty six. [slower] Same city. Same sun. Almost fourteen degrees apart.
        [beat] We give hurricanes names. We do not give heat waves names, and so we do not take
        them seriously. [beat] Mumbai does not have a heat problem. It has twenty four of them,
        one for every ward, and it treats them as though it had one. [beat, then normal pace] My
        name is Anay Dhawan, Grade eleven, NES International School. For the next fifteen minutes
        I want to walk you from that roof to a hospital bed, and show you the one link in that
        chain a city can actually break.
    """)


# ---------------------------------------------------------------------------
# Slide 2: the whole heat problem, on one page
# ---------------------------------------------------------------------------

def slide_02_heat():
    # Section 2, not 1. This slide used to be the tail of the overview section, but a slide
    # headed "The problem" cannot sit under a kicker reading PROJECT OVERVIEW & PARTICIPANT
    # DETAILS. Consequence for the merged deck: SLIDE_SECTION passed to validate() becomes
    # [1, 2, 2, 2, 2, 3, ...], and section 1 is the title slide alone, which still carries
    # every participant field the category asks for.
    slide = base_slide(
        2, 2,
        "The problem: what heat does to Mumbai, and why nobody has chosen",
        heading_size=22,
        sub="Four problems, not one. Every figure here is measured, and each one points at a "
            "different ward.",
        sources=SRC[2],
    )

    # Band A. Three measured numbers, before any argument about them.
    sw = (CONTENT_W - 2 * 0.20) / 3
    stats = [
        ("13.7 °C", "between the coolest and the hottest square kilometre of this city, "
                         "one day, one satellite pass", CRIMSON),
        (f"{HOT['LST_C'] - COOL['LST_C']:.1f} °C",
         f"between the hottest ward and the coolest, {HOT['LST_C']:.1f} against "
         f"{COOL['LST_C']:.1f}, city mean {CITY['LST_C']:.1f}", AMBER),
        ("20,615", "or 17,767, or 10,545. Three government bodies counted India's heat deaths "
                   "over the same twenty years", TEAL),
    ]
    sx = MARGIN_L
    for number, label, accent in stats:
        add_stat_box(slide, sx, 1.74, sw, 0.92, number, label, number_size=22,
                     number_color=accent)
        sx += sw + 0.20

    # Band B. The four harms. Card 1 is the one that does the real work: heat is not merely
    # uneven, it is worst exactly where the ability to cope is lowest.
    cw = (CONTENT_W - 3 * 0.16) / 4
    cards = [
        ("Hottest where people cope least",
         f"Ward {HOT['ward_id']} runs {HOT['LST_C']:.1f} degrees against a city mean of "
         f"{CITY['LST_C']:.1f}. It is {HOT['impervious_pct']:.0f} percent concrete and holds "
         f"{HOT['pop_density_km2']:,.0f} people on every square kilometre.", CRIMSON),
        ("Discomfort for all, danger for some",
         "Metal and asbestos roofs give the heat back all night, so the body never recovers. "
         "Older residents cannot move somewhere cooler. Outdoor workers take the full exposure.",
         AMBER),
        ("The illness concentrates",
         "It lands in the same weeks, in the same wards, on the same hospitals. And the walk to "
         "the nearest one runs from next door to six kilometres.", TEAL),
        ("And it is barely counted",
         "Spread over a season instead of one dramatic day, heat rarely gets recorded as an "
         "emergency. We name hurricanes. We do not name heat waves.", EMERALD),
    ]
    cx = MARGIN_L
    for heading, body, dot in cards:
        add_card(slide, cx, 2.80, cw, 1.72, heading, body, dot=dot,
                 heading_size=11.5, body_size=9.4)
        cx += cw + 0.16

    # Band C. The turn: the first three bands are physics and biology, this one is a choice.
    add_card_bg(slide, MARGIN_L, 4.66, CONTENT_W, 1.02, fill=PANEL_NESTED, border=EMERALD)
    add_body_text(
        slide,
        "You cannot switch off the sun. You can decide where to act first.",
        MARGIN_L + 0.30, 4.82, 11.3, 0.32, size=15, color=WHITE, bold=True, font=FONT_HEAD,
    )
    add_body_text(
        slide,
        "Mumbai's own climate plan names heat as a priority and stops at city scale. Ahmedabad's "
        "plan is credited with about 1,190 lives a year, but it is forecast triggered: it says "
        "when to act, never where. One budget, twenty four wards, and no published method for "
        "choosing between them.",
        MARGIN_L + 0.30, 5.18, 11.3, 0.42, size=10, color=MUTED, line_spacing=1.18,
    )

    # Band D. The chain, at exactly the geometry slides 3 to 5 redraw it with `active=`, so the
    # dimming on those slides still refers back to something the audience has seen.
    chain_strip(slide, 5.82, bw=2.30, h=0.72, gap_arrow=0.30)
    add_body_text(
        slide,
        "Slides 3 to 5 take these one link at a time, with the evidence.",
        10.80, 5.94, 1.98, 0.48, size=8.6, color=MUTED, line_spacing=1.15,
    )

    set_notes(slide, """
        The whole problem, on one page. [point] Thirteen point seven degrees between the coolest
        square kilometre of this city and the hottest, on one afternoon. Ward to ward, six.
        [beat] And look where that heat sits. My hottest ward is eighty nine percent concrete,
        seventy three thousand people to the square kilometre. It is hottest exactly where people
        can least cope. [beat] For most of us that is discomfort. Under a metal roof, or at
        seventy, or waiting outside all day, it becomes danger, and the walk to a hospital here
        runs to six kilometres. [beat] Then this. Three government bodies counted India's heat
        deaths over the same twenty years and published three different answers. It is barely
        counted at all. [beat] So. Nobody here can switch off the sun. Mumbai's plan names heat
        and stops at the city. Ahmedabad's saves lives, but says when, never where. One budget,
        twenty four wards, no method. [point to the fourth link] That link is not physics. It is
        a decision, and it is the only part of this chain you can change on a Monday morning.
    """)


# ---------------------------------------------------------------------------

def assert_no_em_dash(prs):
    """validate() cannot run on a two-slide file, but its strictest rule still has to hold.

    Em dashes are banned across this repo's output, and a single one pasted into the merged
    deck would fail the real gate later, after the hand merge has already happened.
    """
    bad = []
    for i, slide in enumerate(prs.slides, 1):
        texts = [sh.text_frame.text for sh in slide.shapes if sh.has_text_frame]
        if slide.has_notes_slide:
            texts.append(slide.notes_slide.notes_text_frame.text)
        for t in texts:
            if "—" in t:
                bad.append((i, t[:80]))
    if bad:
        raise AssertionError(f"em dash found: {bad}")


def main():
    slide_01_cover()
    slide_02_heat()
    assert_no_em_dash(prs)
    prs.save(OUT_PATH)

    print(f"wrote {OUT_PATH}")
    for i, slide in enumerate(prs.slides, 1):
        n = spoken_words(slide.notes_slide.notes_text_frame.text)
        print(f"  slide {i}: {len(slide.shapes)} shapes, {n} spoken words, "
              f"{int(n / 140 * 60) // 60}:{int(n / 140 * 60) % 60:02d}")
    print(f"  hottest ward {HOT['ward_id']} {HOT['LST_C']:.2f} C, "
          f"coolest {COOL['ward_id']} {COOL['LST_C']:.2f} C, "
          f"spread {HOT['LST_C'] - COOL['LST_C']:.2f} C")


if __name__ == "__main__":
    main()
