"""
Generates UCIP-Pitch-Deck.pptx: the v2 (technical) 20-slide, 15-minute pitch deck.

Layout primitives, brand tokens and the pipeline-fact loader all live in deck_kit.py, which
build_deck_v3.py imports too, so the two decks cannot drift apart on layout. This file owns
only what is specific to v2: its slide content and its speaker notes.

Speaker notes go in the notes pane and ARE the 15-minute script. The build asserts the total
spoken time lands between 14:00 and 15:00 at 140 words per minute, excluding bracketed stage
directions, which are delivery cues rather than spoken words.

Usage: python build_deck.py   (run from this directory)
"""

import os

from deck_kit import *  # noqa: F401,F403  layout toolkit, brand tokens, F (pipeline facts)
from deck_kit import (
    F, SEC, SHOTS, OUT_DIR, MARGIN_L, CONTENT_W, SLIDE_W_IN, SLIDE_H_IN,
    BG, COVER_GLOW, PANEL_SOLID, PANEL_NESTED, BORDER, INK, MUTED, MUTED_FAINT,
    SUBTITLE_INK, WHITE, TEAL, EMERALD, AMBER, CRIMSON,
    FONT_HEAD, FONT_BODY, FONT_MONO,
    new_presentation, use, new_slide, set_background, set_notes, pct,
    add_kicker, add_heading, add_gradient_bar, add_dot_heading, add_body_text,
    add_lead_body, add_card_bg, add_card, add_stat_box, add_pill_list, add_callout,
    add_table, add_bar_row, add_flow_box, add_arrow, add_brand_lockup, add_slide_number,
    add_screenshot, add_crop_screenshot, base_slide,
    backup_existing, validate, check_shots,
    Inches, Pt, rgb, MSO_SHAPE, MSO_ANCHOR, PP_ALIGN,
)

TOTAL_SLIDES = 20
MIN_TOTAL_SEC = 14 * 60
MAX_TOTAL_SEC = 15 * 60

OUT_PATH = os.path.join(OUT_DIR, "UCIP-Pitch-Deck.pptx")
BACKUP_PATH = os.path.join(OUT_DIR, "UCIP-Pitch-Deck-6slide.bak.pptx")

prs = new_presentation()
use(prs, sections=SEC, total=TOTAL_SLIDES)

# ---------------------------------------------------------------------------
# 01 - PROJECT OVERVIEW & PARTICIPANT DETAILS
# ---------------------------------------------------------------------------

def slide_01_title():
    slide = new_slide()
    set_background(slide)

    glow = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(-2.0), Inches(-1.5), Inches(9.0), Inches(6.5))
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
    # Text column is capped at 6.85 in so it clears the hero image parked at x = 7.55.
    add_heading(slide, "UCIP: Urban Climate Intelligence Platform", MARGIN_L, 1.72, 6.85, 1.6, size=34)
    add_gradient_bar(slide, x=MARGIN_L, y=3.40, w=1.3, h=0.06)
    add_body_text(
        slide,
        "A decision-support tool that tells Mumbai's city planners which of the 24 BMC wards "
        "to cool first, why, and what to build there.",
        MARGIN_L, 3.62, 6.60, 0.9, size=14, color=SUBTITLE_INK, line_spacing=1.3,
    )

    add_card_bg(slide, MARGIN_L, 4.65, 6.5, 2.30)
    meta_rows = [
        ("STUDENT NAME", "Anay Dhawan"),
        ("SCHOOL", "NES International School Mumbai"),
        ("GRADE", "11 (IBDP Year 1)"),
        ("DOMAIN", "PLANET"),
        ("FOCUS AREA", "Urban heat resilience, climate adaptation"),
    ]
    ty = 4.80
    row_h = 2.00 / 5
    for label, value in meta_rows:
        add_body_text(slide, label, MARGIN_L + 0.20, ty, 2.0, row_h, size=9, color=MUTED,
                      font=FONT_MONO, anchor=MSO_ANCHOR.MIDDLE)
        add_body_text(slide, value, MARGIN_L + 2.30, ty, 3.90, row_h, size=11.5, color=INK,
                      bold=True, anchor=MSO_ANCHOR.MIDDLE)
        ty += row_h

    # crop_l clears the hero headline entirely; anything under 0.44 leaves "el" of "ward-level".
    add_crop_screenshot(slide, "deck-hero-dark.png", 7.55, 1.72, 5.25,
                        crop_l=0.46, crop_r=0.0, crop_t=0.10, crop_b=0.02,
                        max_h=4.42, center_in=5.25,
                        caption="All 24 wards, extruded and coloured by their real vulnerability score.",
                        caption_size=8.5)

    add_brand_lockup(slide)
    add_slide_number(slide, 1)

    set_notes(slide, """
        [COLD OPEN. Do not introduce yourself yet. Slow. Let the silence sit.] Somewhere in this
        city, right now, someone is on a top floor under a metal roof. The ground under that
        roof read forty degrees. Three kilometres away, another rooftop read twenty six. Same
        city. Same afternoon. Same sun. [beat] Mumbai does not have a heat problem. Mumbai has
        twenty four separate heat problems, and it funds them as though it had one. I am Anay
        Dhawan, Grade eleven, NES International School. This is UCIP. And I want to convince you
        that the useful question is not how hot is this city. It is which one do we fix first.
    """)


def slide_02_claim():
    slide = new_slide()
    set_background(slide)
    add_kicker(slide, SEC[1])
    add_gradient_bar(slide, x=MARGIN_L, y=1.05, w=1.3, h=0.06)

    add_body_text(
        slide,
        "Mumbai already has a heat diagnosis.\nWhat it does not have is a reproducible method\n"
        "for choosing which ward to cool first.",
        MARGIN_L, 1.55, 11.8, 2.0, size=29, color=WHITE, bold=True, line_spacing=1.22,
        font=FONT_HEAD,
    )
    add_body_text(slide, "UCIP is that method.", MARGIN_L, 3.62, 11.8, 0.5, size=29,
                  color=TEAL, bold=True, font=FONT_HEAD)

    add_body_text(slide, "THE NEXT TWENTY MINUTES", MARGIN_L, 4.75, 6.0, 0.26, size=9.5,
                  color=MUTED, font=FONT_MONO, bold=True)

    steps = [
        ("01", "The problem", "why a city-wide plan\nis not enough"),
        ("02", "The research", "what is already out there,\nand what it misses"),
        ("03", "The method", "seven indicators, PCA weights,\nsensitivity-tested"),
        ("04", "The product", "a live dashboard you\ncan click through"),
        ("05", "The limits", "what this tool\ndoes not know"),
        ("06", "What's next", "finer grid, more cities,\nbudget layer"),
    ]
    bw, gap = 1.86, 0.18
    bx = MARGIN_L
    for num, name, detail in steps:
        add_flow_box(slide, bx, 5.12, bw, 1.28, num, name, detail)
        bx += bw + gap

    add_brand_lockup(slide)
    add_slide_number(slide, 2)

    set_notes(slide, """
        Now, the gap here is not what you would expect. It is not a lack of data. IIT Bombay has
        mapped the heat island. The city has a climate action plan. The diagnosis exists. What
        does not exist is the sentence that comes after the diagnosis. [beat] Twenty four wards.
        One budget. No defensible way to say this ward before that one. So it gets decided on
        instinct, and instinct cannot be shown to a committee. UCIP turns that decision into a
        method.
    """)


# ---------------------------------------------------------------------------
# 02 - PROBLEM UNDERSTANDING
# ---------------------------------------------------------------------------

def slide_03_uneven():
    slide = base_slide(3, 2, "Mumbai is not uniformly hot. It is unevenly hot.")
    city = F["city"]

    add_body_text(
        slide,
        "Measured across the 541 one-kilometre cells in this project's own satellite pipeline "
        "for Mumbai, the pilot city, not quoted from a report.",
        MARGIN_L, 1.34, 7.4, 0.32, size=10.5, color=SUBTITLE_INK,
    )

    add_callout(slide, MARGIN_L, 1.86, 7.4, 1.05, "13.7 \u00b0C",
                "spread in land-surface temperature between the coolest and hottest "
                "square kilometre inside a single city, from 26.2 \u00b0C to 40.0 \u00b0C.",
                number_size=26, accent=CRIMSON)

    rows = [
        ("Land-surface temperature", "26.2 to 40.0 \u00b0C", f"{city['LST_C']:.1f} \u00b0C"),
        ("Green cover (NDVI index)", "-0.07 to 0.71", f"{city['NDVI']:.2f}"),
        ("Impervious / built-up", "0 to 96.8 %", f"{city['impervious_pct']:.0f} %"),
        ("Population density", "16 to 115,272 /km\u00b2", f"{city['pop_density_km2']:,.0f} /km\u00b2"),
        ("Distance to nearest hospital", "4 m to 6.2 km", f"{city['hospital_dist_m']:,.0f} m"),
    ]
    add_table(slide, MARGIN_L, 3.16, 7.4, 2.94,
              ["INDICATOR", "RANGE ACROSS THE CITY", "CITY MEAN"],
              rows, [3.0, 2.55, 1.85], body_size=9.4)

    add_body_text(
        slide,
        "A city-wide average hides all of this. Every one of these gaps is a targeting opportunity.",
        MARGIN_L, 6.30, 7.4, 0.4, size=10.5, color=INK, bold=True,
    )

    add_crop_screenshot(slide, "deck-global-heat-anomaly.png", 8.30, 1.86, 4.48,
                        crop_l=0.41, crop_r=0.03, crop_t=0.01, crop_b=0.10,
                        max_h=4.24, center_in=4.48,
                        caption="The same unevenness, worldwide. NASA / GISS global surface "
                                "temperature anomaly, 2024.")

    set_notes(slide, """
        So let me show you what an average hides. Not from a report. Five hundred and forty one
        square kilometre cells out of my own pipeline. Surface temperature runs from twenty six
        degrees to forty. Density, sixteen people per square kilometre to over a hundred and
        fifteen thousand. Now average it. Mumbai is thirty two degrees. Perfectly true.
        Completely useless. [beat] And look right. That is NASA's global anomaly map. This
        unevenness is not a Mumbai quirk. Mumbai is just where I could test it first.
    """)


def slide_04_who():
    slide = base_slide(4, 2, "The burden is not shared evenly either")

    # 4 equal cards, gap=0.18, card_w=(CONTENT_W - 3*0.18)/4 = 2.923
    cw = 2.923
    cx1 = MARGIN_L
    cx2 = MARGIN_L + 3.103
    cx3 = MARGIN_L + 6.206
    cx4 = MARGIN_L + 9.309

    add_card(slide, cx1, 1.75, cw, 2.35, "Slum households",
             "Metal and asbestos roofs trap heat by day, release it at night. Cooling access is "
             "lowest where indoor heat is highest.", dot=CRIMSON)
    add_card(slide, cx2, 1.75, cw, 2.35, "Elderly residents",
             "Heat mortality concentrates sharply with age. Elderly residents are also least able "
             "to relocate during a heat event.", dot=AMBER)
    add_card(slide, cx3, 1.75, cw, 2.35, "Wards far from care",
             "Heat illness is time-critical. Hospital distance ranges from four metres to over "
             "six kilometres across the city.", dot=TEAL)
    add_card(slide, cx4, 1.75, cw, 2.35, "Everyday commuters",
             "Bus stops and rail platforms offer little shade. Anyone waiting for transit absorbs "
             "the same heat exposure, with no home to retreat to.", dot=EMERALD)

    add_card_bg(slide, MARGIN_L, 4.35, 11.94, 1.95, fill=PANEL_NESTED, border=TEAL)
    add_body_text(slide, "THE PART THAT MAKES THIS HARD", MARGIN_L + 0.30, 4.55, 6.0, 0.26,
                  size=9.5, color=TEAL, font=FONT_MONO, bold=True)
    add_body_text(
        slide,
        "Vulnerability is highest exactly where the data is scarcest.",
        MARGIN_L + 0.30, 4.88, 11.3, 0.42, size=19, color=WHITE, bold=True, font=FONT_HEAD,
    )
    add_body_text(
        slide,
        "Informal settlements are, almost by definition, under-surveyed. That is precisely why "
        "UCIP is built on open satellite and modelled-population data rather than waiting on a "
        "ward-level census that does not exist. It is also why I state plainly, later in this "
        "deck, which of my own layers are proxies.",
        MARGIN_L + 0.30, 5.42, 11.3, 0.75, size=10.5, color=MUTED, line_spacing=1.2,
    )

    set_notes(slide, """
        But heat is only half the story, because heat does not hurt everyone equally. Four
        groups carry it. Slum households, where metal roofs bank heat all day and release it all
        night. Elderly residents, where mortality climbs sharply with age. Anyone far from care,
        and hospital distance here runs from four metres to over six kilometres. And commuters,
        on unshaded platforms. Now the cruel part. [beat] Vulnerability is highest exactly where
        the data is thinnest. Informal settlements are under-surveyed almost by definition. That
        one fact shaped everything. I could not wait for a census that does not exist.
    """)


def slide_05_matters():
    slide = base_slide(5, 2, "Why this matters, and what is actually missing")

    add_card(slide, MARGIN_L, 1.75, 5.85, 2.05, "Heat is India's deadliest weather hazard",
             "It kills more people than floods or cyclones, and it does so quietly, spread across "
             "a season rather than concentrated in one visible disaster. That makes it easy to "
             "under-invest in.")

    add_callout(slide, MARGIN_L, 4.00, 5.85, 1.30, "~1,190",
                "lives saved per year in Ahmedabad once heat action was targeted locally rather "
                "than declared city-wide (Knowlton et al. 2014, IJERPH). Targeting is the "
                "variable that moved the number.",
                number_size=25, accent=EMERALD)

    add_card_bg(slide, MARGIN_L + 6.09, 1.75, 5.85, 3.55, border=CRIMSON)
    add_dot_heading(slide, "The gap Mumbai actually has", MARGIN_L + 6.34, 1.95, 5.35, 0.30,
                    size=13, dot=CRIMSON)
    add_body_text(
        slide,
        "The Mumbai Climate Action Plan 2022 names heat as a priority pillar. It sets city-wide "
        "goals, and it is a serious document.\n"
        "But it stops at strategy. It does not contain a reproducible method for answering the "
        "one question a planner with a finite budget has to answer first:\n"
        "which ward gets cooled before the others, and on what evidence?\n"
        "That is a targeting gap, not a data gap. Mumbai has the data. It does not have the "
        "decision layer that sits on top of it.",
        MARGIN_L + 6.34, 2.40, 5.35, 2.75, size=10.5, color=MUTED, line_spacing=1.22,
        space_before=7,
    )

    add_body_text(
        slide,
        "UCIP is scoped tightly to the 24 BMC wards, on a 1 km grid. The approach is not "
        "Mumbai-specific, but the build is.",
        MARGIN_L, 5.62, 11.94, 0.4, size=10.5, color=INK, bold=True,
    )

    set_notes(slide, """
        At which point you should ask whether targeting actually changes anything. One city
        already answered that. [beat] Ahmedabad. After it moved from city-wide heat warnings to
        locally targeted action, Knowlton and colleagues estimated roughly eleven hundred and
        ninety lives saved per year. Not from more money. Not from new technology. From deciding
        where. Heat is India's deadliest weather hazard, and it kills quietly, across a season
        rather than one visible disaster. Mumbai's plan names heat as a priority, then stops at
        strategy. That is not a data gap. That is a targeting gap.
    """)


# ---------------------------------------------------------------------------
# 03 - RESEARCH & INSIGHTS
# ---------------------------------------------------------------------------

def slide_06_measured():
    slide = base_slide(6, 3, "What I measured, not what I looked up",
                       sub="Every figure in this deck comes out of a pipeline I ran, on free and public data.")

    city = F["city"]
    stats = [
        ("12", "Landsat 8/9 scenes\ncomposited"),
        (f"{city['LST_C']:.1f} \u00b0C", "mean land-surface\ntemperature, city-wide"),
        (f"{city['NDVI']:.2f}", "mean NDVI\ngreen-cover index"),
        (f"{F['n_cells']}", "1 km cells scored\nacross 24 wards"),
    ]
    bw, gap = 2.88, 0.20
    bx = MARGIN_L
    for num, label in stats:
        add_stat_box(slide, bx, 1.86, bw, 1.05, num, label, number_size=19)
        bx += bw + gap

    rows = [
        ("Landsat 8 & 9 Collection 2 L2", "USGS via Google Earth Engine",
         "Surface temperature, NDVI", "30 m"),
        ("ESA WorldCover v200", "ESA via Google Earth Engine",
         "Impervious cover, land class", "10 m"),
        ("WorldPop pop_age_sex (IND_2020)", "WorldPop via Google Earth Engine",
         "Population, elderly share", "100 m"),
        ("OpenStreetMap (osmnx)", "OSM contributors, ODbL",
         "Hospital locations", "vector"),
        ("Datameet Municipal Spatial Data", "Datameet, open",
         "BMC ward boundaries, slum clusters", "vector"),
    ]
    add_table(slide, MARGIN_L, 3.20, 11.94, 2.45,
              ["DATASET", "PROVENANCE", "WHAT IT CONTRIBUTES", "RES."],
              rows, [3.85, 3.25, 3.64, 1.20])

    add_body_text(
        slide,
        "Dry-season window, November 2025 to February 2026. Cloud cover under 20 percent, "
        "cloud and shadow masked per pixel, median composite.",
        MARGIN_L, 5.80, 7.6, 0.4, size=10, color=MUTED,
    )
    add_body_text(
        slide,
        f"{F['n_citations']} papers cited. Every DOI verified.",
        8.55, 5.80, 4.0, 0.4, size=10.5, color=EMERALD, bold=True, align=PP_ALIGN.RIGHT,
    )

    set_notes(slide, """
        So I had a choice. I could download somebody's published heat map and build a nice
        interface on top of it. Plenty of projects do. [beat] I did not. Every number in this
        deck came out of a pipeline I ran. Twelve Landsat scenes composited across the dry
        season, cloud and shadow masked pixel by pixel. And look what sits underneath. Landsat.
        WorldCover. WorldPop. OpenStreetMap. Datameet. Every one free and public. Hold on to
        that. It matters at the end.
    """)


def slide_07_literature():
    slide = base_slide(7, 3, "What the literature says, including the inconvenient part")

    add_card(slide, MARGIN_L, 1.75, 3.86, 2.45, "Canopy cooling is nonlinear",
             "Below roughly 40 % canopy cover, daytime cooling is negligible. Between 40 and 80 % "
             "you get about 1 \u00b0C. Planting a few trees in a bare ward buys almost nothing.\n\n"
             "Ziter et al. 2019, PNAS", dot=EMERALD)

    add_card(slide, MARGIN_L + 4.04, 1.75, 3.86, 2.45, "Cool roofs are the reliable lever",
             "Roughly 0.6 K of peak cooling per +0.1 albedo, quoted at the conservative end of the "
             "published range. Cheap, fast, and it works on exactly the roofs that trap the most "
             "heat.\n\nSantamouris 2014, Solar Energy", dot=TEAL)

    add_card(slide, MARGIN_L + 8.08, 1.75, 3.86, 2.45, "The inconvenient finding",
             "Planting trees on native grassland is ecologically harmful. Restoration potential is "
             "real, but it is not everywhere, and treating it as everywhere causes damage.\n\n"
             "Bastin et al. 2019 vs Veldman et al. 2019, Science", dot=CRIMSON)

    add_card_bg(slide, MARGIN_L, 4.45, 11.94, 1.85, fill=PANEL_NESTED, border=CRIMSON)
    add_body_text(slide, "WHY THIS ONE CHANGED THE DESIGN", MARGIN_L + 0.30, 4.65, 7.0, 0.26,
                  size=9.5, color=CRIMSON, font=FONT_MONO, bold=True)
    add_body_text(
        slide,
        "Almost every urban-greening tool answers heat with \"plant more trees\". The Bastin and "
        "Veldman exchange in Science says that is wrong often enough to matter. So UCIP does not "
        "recommend planting until it has checked whether planting belongs there, and when the "
        "answer is no, it says no and routes to cool roofs instead. That guardrail is the single "
        "biggest design consequence of the reading, and I will show it running on slide sixteen.",
        MARGIN_L + 0.30, 4.98, 11.3, 1.15, size=10.5, color=MUTED, line_spacing=1.22,
    )

    set_notes(slide, """
        And then I read the paper that broke my plan. [beat] Three findings shaped this build.
        Canopy cooling is nonlinear. Ziter, in PNAS, found that below about forty percent cover
        you get essentially nothing, so a handful of trees in a bare ward is decoration, not
        cooling. Second, cool roofs are the dependable lever, about zero point six Kelvin per
        zero point one of albedo. Third is the one I did not want to find. An argument in
        Science between Bastin, who mapped where the world could plant trees, and Veldman, who
        replied that much of that map is native grassland, where planting does real ecological
        harm. Almost every greening tool answers heat with plant more trees. After that, I could
        not.
    """)


def slide_08_priorart():
    slide = base_slide(8, 3, "Five tools already exist. None does all five jobs.")

    rows = [
        ("Mumbai Climate Action Plan 2022", "no", "no", "no", "no", "no"),
        ("Azhar et al. 2017 India HVI (RAND)", "district only", "partial", "no", "no", "no"),
        ("IIT Bombay Mumbai UHI studies", "yes", "partial", "no", "no", "no"),
        ("C40 Urban Cooling Toolbox", "no", "no", "yes", "no", "partial"),
        ("Ahmedabad Heat Action Plan", "no", "no", "yes", "no", "no"),
        ("UCIP", "yes", "yes", "yes", "yes", "roadmap"),
    ]
    add_table(slide, MARGIN_L, 1.80, 11.94, 3.05,
              ["TOOL", "WARD-LEVEL\nRANKING", "PER-FACTOR\nEXPLAINABILITY",
               "INTERVENTION\nENGINE", "ECOLOGICAL\nGUARDRAIL", "BUDGET\nLAYER"],
              rows, [4.14, 1.56, 1.86, 1.62, 1.62, 1.14],
              body_size=8.6, header_size=8.2, highlight_last=True)

    add_card_bg(slide, MARGIN_L, 5.05, 7.85, 1.35, fill=PANEL_NESTED, border=TEAL)
    add_body_text(
        slide,
        "Every prior tool does at most two of the five. UCIP does four.",
        MARGIN_L + 0.28, 5.24, 7.3, 0.38, size=15, color=WHITE, bold=True, font=FONT_HEAD,
    )
    add_body_text(
        slide,
        "The fifth, a budget-allocation layer, is designed but not built. It is on the roadmap "
        "slide, not claimed here.",
        MARGIN_L + 0.28, 5.68, 7.3, 0.55, size=10, color=MUTED, line_spacing=1.2,
    )

    add_stat_box(slide, 8.72, 5.05, 1.95, 1.35, "640",
                 "districts in the closest\nIndian HVI",
                 number_size=20, layout="stacked", number_color=AMBER)
    add_stat_box(slide, 10.83, 5.05, 1.95, 1.35, "24",
                 "wards UCIP resolves inside\none of those districts",
                 number_size=20, layout="stacked", number_color=EMERALD)

    set_notes(slide, """
        Now the obvious question. Surely someone has already built this. [beat] Five people had,
        all better resourced than a Grade eleven student. The RAND index by Azhar is peer
        reviewed, but resolves six hundred and forty districts nationally, so all of Mumbai is
        about one pixel. IIT Bombay's work is rigorous, and diagnostic. It tells you where it is
        hot, never what to build. C40's toolbox is real decision support, but global and
        generic. Ahmedabad's plan tells you when a heat wave is coming, not where to invest.
        Every one does at most two of five capabilities. UCIP does four. The fifth I marked
        roadmap, because it does not exist yet.
    """)


# ---------------------------------------------------------------------------
# 04 - PROPOSED SOLUTION
# ---------------------------------------------------------------------------

def slide_09_chain():
    slide = base_slide(9, 4, "The chain: rank, explain, recommend, check")

    steps = [
        ("01", "Rank", "One vulnerability score\nper ward, 0 to 100,\nweights derived from\nthe data itself"),
        ("02", "Explain", "Seven contribution bars\nper ward showing exactly\nwhich factor pushed\nthe score up"),
        ("03", "Recommend", "Five cited rules turn\nthe score into a specific\nintervention with a\npriority level"),
        ("04", "Check", "Ecological guardrail\nblocks tree planting\nwhere it would backfire,\nroutes to cool roofs"),
    ]
    bw = 2.72
    arrow_w = 0.38
    bx = MARGIN_L
    for i, (num, name, detail) in enumerate(steps):
        add_flow_box(slide, bx, 1.85, bw, 1.85, num, name, detail,
                     accent=[TEAL, TEAL, EMERALD, CRIMSON][i])
        bx += bw
        if i < 3:
            add_arrow(slide, bx + 0.06, 2.62, arrow_w - 0.12, 0.30)
            bx += arrow_w

    add_body_text(slide, "WHO ACTS ON IT", MARGIN_L, 4.10, 6.0, 0.26, size=9.5,
                  color=MUTED, font=FONT_MONO, bold=True)
    add_pill_list(slide, MARGIN_L, 4.42, 11.94, 1.88, [
        ("BMC planners:", "a defensible, auditable priority list instead of intuition, where every "
                          "ranking can be traced back to the indicator that caused it."),
        ("Vulnerable residents:", "cooling investment lands where need is measurably highest, and "
                                  "the reasoning is public rather than internal."),
        ("Researchers and NGOs:", "open method, open data, open code, and a limitations section "
                                  "that is written down rather than discovered later."),
    ], gap=0.10, lead_size=11, rest_size=9.8)

    set_notes(slide, """
        So here is the whole system, in four verbs. Rank. Explain. Recommend. Check. Rank gives
        every ward one score, with weights the data chose, not weights I chose. Explain breaks
        that score into seven bars so you see which factor did the damage. Recommend fires five
        cited rules that turn a number into something you can build. And check is the one almost
        nobody has. The guardrail that refuses the obvious answer when the ecology says refuse.
        [beat] Three people act on this. A planner who must defend a decision. A resident who
        deserves to know why. And a researcher who wants to take it apart.
    """)


def slide_10_indicators():
    slide = base_slide(10, 4, "What goes into the score")

    rows = [
        ("Land-surface temperature", "+", "Direct exposure. The hazard itself.", "Landsat 8/9"),
        ("Green cover (NDVI)", "\u2212", "Vegetation cools. More green means less vulnerable.", "Landsat 8/9"),
        ("Population density", "+", "More people exposed per unit of area affected.", "WorldPop"),
        ("Elderly share", "+", "Heat mortality concentrates sharply with age.", "WorldPop"),
        ("Slum share", "+", "Heat-trapping roofs, low cooling access.", "Datameet"),
        ("Distance to hospital", "+", "Heat illness is time-critical. Access is protective.", "OSM"),
        ("Impervious / built-up", "+", "Concrete and asphalt store and re-radiate heat.", "ESA WorldCover"),
    ]
    add_table(slide, MARGIN_L, 1.80, 11.94, 3.35,
              ["INDICATOR", "DIR.", "WHY IT IS IN THE INDEX", "SOURCE"],
              rows, [3.20, 0.78, 5.86, 2.10], body_size=9.2)

    add_card_bg(slide, MARGIN_L, 5.35, 5.85, 1.10, fill=PANEL_NESTED)
    add_body_text(slide, "Direction is set by the literature, not by the maths.",
                  MARGIN_L + 0.26, 5.52, 5.35, 0.30, size=11, color=WHITE, bold=True)
    add_body_text(
        slide,
        "Green cover is the only inverted indicator. Reid 2009, Knowlton 2014 and Azhar 2017 all "
        "use this indicator family for heat vulnerability.",
        MARGIN_L + 0.26, 5.83, 5.35, 0.50, size=9.5, color=MUTED, line_spacing=1.18,
    )

    add_card_bg(slide, MARGIN_L + 6.09, 5.35, 5.85, 1.10, fill=PANEL_NESTED)
    add_body_text(slide, "Every indicator is standardised before it is combined.",
                  MARGIN_L + 6.35, 5.52, 5.35, 0.30, size=11, color=WHITE, bold=True)
    add_body_text(
        slide,
        "A z-score puts degrees Celsius, people per square kilometre and metres on the same scale, "
        "so no indicator wins simply because its units are bigger.",
        MARGIN_L + 6.35, 5.83, 5.35, 0.50, size=9.5, color=MUTED, line_spacing=1.18,
    )

    set_notes(slide, """
        Seven indicators go in. Heat itself. Green cover, the only one where more is better.
        Density. Elderly share. Slum share. Hospital distance. And built-up surface, because
        concrete banks heat all day and hands it back at night. Now, the question I would ask if
        I were sitting where you are. Where does he get to cheat? [beat] Exactly two places, and
        this is the first. Deciding which direction each indicator points. I did not decide
        that. Reid, Knowlton and Azhar did. The second is the weights. Next slide.
    """)


def slide_11_weights():
    slide = base_slide(11, 4, "How the score is built")

    steps = [
        ("01", "Standardise", "z-score each\nof 7 indicators"),
        ("02", "Orient", "flip sign so higher\nalways means worse"),
        ("03", "Weight", "PCA, weights from\nPC1 loadings"),
        ("04", "Combine", "weighted sum,\nrescaled 0 to 100"),
    ]
    bw, gap = 1.56, 0.14
    bx = MARGIN_L
    for num, name, detail in steps:
        add_flow_box(slide, bx, 1.78, bw, 1.02, num, name, detail)
        bx += bw + gap

    add_callout(slide, MARGIN_L, 2.98, 6.90, 0.82, pct(F["pc1"]),
                "of total variance explained by the first principal component, comfortably above "
                "the 30 % floor, so PCA weights are used directly.",
                number_size=22, accent=EMERALD)

    add_body_text(slide, "WEIGHTS THIS RUN PRODUCED", MARGIN_L, 4.02, 6.0, 0.26, size=9.5,
                  color=MUTED, font=FONT_MONO, bold=True)

    labels = {
        "impervious_pct": "Impervious / built-up",
        "pop_density_km2": "Population density",
        "LST_C": "Land-surface temp",
        "NDVI": "Green cover (NDVI)",
        "hospital_dist_m": "Hospital distance",
        "slum_pct": "Slum index",
        "elderly_pct": "Elderly share",
    }
    ordered = sorted(F["weights"].items(), key=lambda kv: -kv[1])
    wmax = 0.20
    ry = 4.34
    for key, val in ordered:
        add_bar_row(slide, MARGIN_L, ry, 6.90, 0.30, labels[key], val / wmax, pct(val),
                    label_w=2.05, value_w=0.72)
        ry += 0.32

    add_card_bg(slide, 7.75, 1.78, 5.03, 2.02, fill=PANEL_NESTED, border=AMBER)
    add_dot_heading(slide, "The safety rule", 8.00, 1.96, 4.5, 0.28, size=12, dot=AMBER)
    add_body_text(
        slide,
        "If PC1 had explained less than 30 % of variance, the loadings would be unstable for a "
        "single-city, single-snapshot sample. The code detects that and falls back to equal "
        "weighting rather than trusting them.\n"
        "It did not trigger. But it is in the code, and the site prints which branch ran.",
        8.00, 2.34, 4.53, 1.36, size=9.8, color=MUTED, line_spacing=1.2, space_before=6,
    )

    add_crop_screenshot(slide, "deck-methodology-weights-dark.png", 7.75, 4.02, 5.03,
                        crop_l=0.21, crop_r=0.21, crop_t=0.10, crop_b=0.33,
                        max_h=2.28, center_in=5.03,
                        caption="The site reads these numbers straight from the pipeline's JSON output.")

    set_notes(slide, """
        And this is where most indices quietly lie. [beat] You pick weights that feel about
        right, you publish a number, and nobody can check you. So I do not pick them. I follow
        Reid two thousand and nine, run a principal component analysis, and take the weights
        from the first component's loadings. The data decides which indicators carry this index.
        This run, that component explains fifty eight percent of the variance. Impervious
        surface highest at eighteen percent. Elderly share lowest, under eight. Honestly, not
        the ordering I expected. But I did not get a vote. [beat] And there is a trapdoor. Below
        thirty percent, the loadings are not trustworthy, so the code throws them away and falls
        back to equal weighting. It did not trigger. But the site prints which branch ran.
    """)


def slide_12_rules():
    slide = base_slide(12, 4, "From score to recommendation, with a guardrail")

    rows = [
        ("Native tree planting + green corridors",
         "Hot, low canopy, AND ecologically plantable", "Bastin 2019", "1"),
        ("Cool roofs + reflective pavements",
         "Hot, low canopy, but NOT plantable", "Veldman 2019", "1"),
        ("Cooling centres, priority siting",
         "High elderly share + poor hospital access", "Knowlton 2014", "1"),
        ("Rain gardens + water-sensitive design",
         "Highly impervious + near mapped water", "proxy, stated", "2"),
        ("Pocket parks",
         "High density + little existing open space", "C40 Toolbox", "3"),
    ]
    add_table(slide, MARGIN_L, 1.80, 7.85, 2.55,
              ["INTERVENTION", "FIRES WHEN", "CITATION", "PRI."],
              rows, [3.20, 2.90, 1.35, 0.40], body_size=8.8)

    add_card_bg(slide, MARGIN_L, 4.55, 7.85, 1.80, fill=PANEL_NESTED, border=CRIMSON)
    add_dot_heading(slide, "The guardrail, stated as code", MARGIN_L + 0.26, 4.74, 7.3, 0.28,
                    size=12, dot=CRIMSON)
    add_body_text(
        slide,
        "plantable  =  NOT built-up, water, wetland or mangrove\n"
        "                    AND  NOT native grassland\n"
        "                    AND  impervious cover below the 75th percentile",
        MARGIN_L + 0.26, 5.12, 7.3, 0.85, size=10, color=EMERALD, font=FONT_MONO,
        line_spacing=1.28, space_before=3,
    )
    add_body_text(
        slide,
        "Rules 1 and 2 are the same situation with opposite answers. The guardrail decides which.",
        MARGIN_L + 0.26, 6.00, 7.3, 0.30, size=9.5, color=MUTED,
    )

    stats = [
        (f"{F['n_nbs']}", "ward-level recommendations\ngenerated, across all 24 wards"),
        ("204", f"of {F['n_cells']} cells rejected for\nplanting by the guardrail"),
        ("5", "distinct interventions, each\ncarrying its own citation"),
    ]
    sy = 1.80
    for num, label in stats:
        add_stat_box(slide, 8.72, sy, 4.06, 1.05, num, label, number_size=20, layout="row")
        sy += 1.17

    add_card_bg(slide, 8.72, 5.35, 4.06, 1.00, fill=PANEL_NESTED)
    add_body_text(
        slide,
        "Thresholds are percentiles of this run, not fixed absolute cutoffs. Re-run on new imagery "
        "and they move with the city.",
        8.98, 5.52, 3.56, 0.70, size=9.5, color=MUTED, line_spacing=1.2,
    )

    set_notes(slide, """
        A score is still only a diagnosis. So it feeds a rule engine. Five rules, each carrying
        an intervention, a reason, a citation and a priority. Now look at the top two rows,
        because they contradict each other on purpose. [beat] They fire on the identical
        situation. A hot ward with low canopy. And they give opposite answers. Plantable, you
        get trees, cited to Bastin. Not plantable, you get cool roofs, cited to Veldman. What
        sits between them is the guardrail. Not built up, water or wetland. Not native
        grassland. Impervious cover below the seventy fifth percentile. And here is the number
        that surprised me most. That guardrail rejects thirty eight percent of Mumbai, where
        plant trees is the wrong answer.
    """)


# ---------------------------------------------------------------------------
# 05 - PROTOTYPE / SOLUTION DESIGN
# ---------------------------------------------------------------------------

def slide_13_arch():
    slide = base_slide(13, 5, "Architecture")

    add_body_text(
        slide,
        "Google Earth Engine  \u2192  Python (geopandas, scikit-learn, osmnx, scipy)  \u2192  "
        "Supabase + PostGIS  \u2192  Next.js 16 + Leaflet + three.js  \u2192  Vercel",
        MARGIN_L, 1.36, 11.94, 0.32, size=10.5, color=TEAL, font=FONT_MONO,
    )

    boxes = [
        ("01", "Open data", "Landsat 8/9\nWorldCover\nWorldPop\nOSM, Datameet"),
        ("02", "Python pipeline", f"{F['n_stages']} numbered stages\ngrid, zonal stats,\nPCA index,\nrule engine"),
        ("03", "Storage", "Supabase Postgres\n+ PostGIS\nand static GeoJSON\nsnapshots"),
        ("04", "Web app", "Next.js 16, React 19\nLeaflet choropleth\nthree.js hero\n8 static routes"),
        ("05", "Deploy", "Vercel\nstatic prerender\nno server-side\ndata calls"),
    ]
    bw = 2.16
    arrow_w = 0.32
    bx = MARGIN_L
    for i, (num, name, detail) in enumerate(boxes):
        add_flow_box(slide, bx, 1.85, bw, 1.62, num, name, detail)
        bx += bw
        if i < 4:
            add_arrow(slide, bx + 0.04, 2.52, arrow_w - 0.08, 0.28)
            bx += arrow_w

    stats = [
        (f"{F['n_wards']}", "wards scored"),
        (f"{F['n_cells']}", "1 km grid cells"),
        (f"{F['n_nbs']}", "cited recommendations"),
        (f"{F['n_stages']}", "pipeline stages"),
        (f"{F['n_citations']}", "papers, DOIs verified"),
    ]
    bw2, gap2 = 2.30, 0.16
    bx = MARGIN_L
    for num, label in stats:
        add_stat_box(slide, bx, 3.68, bw2, 0.92, num, label, number_size=20)
        bx += bw2 + gap2

    add_card_bg(slide, MARGIN_L, 4.80, 11.94, 1.62, fill=PANEL_NESTED, border=EMERALD)
    add_dot_heading(slide, "The design decision I would defend hardest", MARGIN_L + 0.30, 4.98,
                    8.0, 0.28, size=12.5, dot=EMERALD)
    add_body_text(
        slide,
        "The loader writes GeoJSON snapshots first and unconditionally, then attempts the database "
        "load on a best-effort basis. The shipped frontend never imports the Supabase client at "
        "all. On 21 July I verified this by blocking supabase.co and earthengine.googleapis.com at "
        "the network layer and walking the entire judged flow. Zero errors. The demo cannot die "
        "from a dead network dependency, and that was a deliberate choice made on day zero rather "
        "than a patch applied after something broke.",
        MARGIN_L + 0.30, 5.36, 11.34, 0.95, size=10.2, color=MUTED, line_spacing=1.2,
    )

    set_notes(slide, """
        Architecture, quickly. Open data in. Thirteen numbered Python stages. Results to
        Postgres and to static files. A Next.js app on top. Twenty four wards, five hundred and
        forty one cells, eighty one recommendations, eleven cited papers. But I want to tell you
        about one decision, and it is not a feature. [beat] Every demo in this building has the
        same failure mode. The wifi. So the loader writes static snapshots first, then tries the
        database. The shipped frontend never imports the database client at all. And I proved
        that rather than assuming it. I blocked both data providers at the network layer and
        walked the whole flow. Zero errors.
    """)


def slide_14_dashboard():
    slide = base_slide(14, 5, "The dashboard")

    # Full frame, no right crop: cutting mid-sidebar left truncated labels on screen.
    add_crop_screenshot(slide, "deck-dashboard-hvi-dark.png", MARGIN_L, 1.80, 8.05,
                        crop_l=0.0, crop_r=0.0, crop_t=0.055, crop_b=0.0,
                        max_h=4.42, center_in=8.05,
                        caption="Twenty four wards, coloured by vulnerability, ranked in the sidebar, "
                                "with a persistent legend.")

    add_body_text(slide, "MOST VULNERABLE, COMPUTED NOT CHOSEN", 8.92, 1.80, 4.0, 0.26,
                  size=9.5, color=MUTED, font=FONT_MONO, bold=True)

    ranked_names = {"C": "Marine Lines, Kalbadevi", "G/N": "Dadar, Mahim, Dharavi",
                    "L": "Kurla", "E": "Byculla, Mazgaon", "F/S": "Parel, Lalbaug, Sewri"}
    ry = 2.14
    for i, (wid, hvi) in enumerate(F["top5"], start=1):
        add_card_bg(slide, 8.92, ry, 3.86, 0.52, fill=PANEL_NESTED)
        add_body_text(slide, str(i), 9.08, ry, 0.30, 0.52, size=11, color=MUTED,
                      font=FONT_MONO, anchor=MSO_ANCHOR.MIDDLE)
        add_body_text(slide, f"Ward {wid}", 9.42, ry, 1.30, 0.52, size=11.5, color=WHITE,
                      bold=True, anchor=MSO_ANCHOR.MIDDLE)
        add_body_text(slide, ranked_names[wid], 10.62, ry, 1.55, 0.52, size=8.2, color=MUTED,
                      anchor=MSO_ANCHOR.MIDDLE)
        add_body_text(slide, f"{hvi:.1f}", 11.98, ry, 0.66, 0.52, size=11.5, color=CRIMSON,
                      bold=True, font=FONT_MONO, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.RIGHT)
        ry += 0.60

    add_card_bg(slide, 8.92, 5.20, 3.86, 1.02, fill=PANEL_NESTED)
    add_body_text(
        slide,
        "Search resolves locality names, so typing \"Dharavi\" finds Ward G/N. Every ward is a "
        "shareable link, and browser Back steps through your selections.",
        9.18, 5.38, 3.36, 0.72, size=9.3, color=MUTED, line_spacing=1.2,
    )

    set_notes(slide, """
        So here it is. Twenty four wards, coloured by need, ranked beside the map, with a legend
        that never leaves the screen, because an unexplained choropleth is decoration, not
        decision support. Top five. C, G north, L, E, F south. And I want to be precise about
        one thing. [beat] I did not pick these. I did not put Dharavi near the top because
        Dharavi is the famous answer. Ward G north contains Dharavi, and it arrived at number
        two on its own. And every ward is a link, so a planner sends a colleague one ward, not a
        screenshot.
    """)


def slide_15_explain():
    slide = base_slide(15, 5, "Ward C: explainability, end to end")

    # Sidebar-only crop, so this is portrait. Width is derived from max_h, not the other way round.
    add_crop_screenshot(slide, "deck-ward-c-dark.png", MARGIN_L, 1.80, 7.30,
                        crop_l=0.752, crop_r=0.005, crop_t=0.055, crop_b=0.0,
                        max_h=4.42, center_in=7.30,
                        caption="Every number on this panel is a lookup, not a second model.")

    add_card(slide, 8.20, 1.80, 4.58, 1.62, "Generated, not hand-written",
             "\"Ward C runs about 3.4 \u00b0C hotter than the city average across its 2 grid cells, "
             "at 35.8 \u00b0C of land surface temperature.\" Deterministic prose over the profile "
             "data. No language model in the loop.", body_size=9.5)

    add_card(slide, 8.20, 3.58, 4.58, 1.42, "Seven contribution bars",
             "Each bar is literally weight multiplied by z-score. Red pushed this ward up, green "
             "pulled it down. It is the same arithmetic that produced the score, shown back to you.",
             body_size=9.5, dot=CRIMSON)

    add_card_bg(slide, 8.20, 5.16, 4.58, 1.06, fill=PANEL_NESTED, border=EMERALD)
    add_body_text(slide, "No black box, and no SHAP either.", 8.46, 5.33, 4.06, 0.30,
                  size=11.5, color=WHITE, bold=True)
    add_body_text(
        slide,
        "A linear index does not need a post-hoc explainer. Refusing to add one was a design "
        "choice, recorded in the code.",
        8.46, 5.64, 4.06, 0.50, size=9.3, color=MUTED, line_spacing=1.2,
    )

    set_notes(slide, """
        Now click the worst one. Ward C, the old fort and market core. First, three sentences of
        plain English, generated deterministically from that ward's own data. Not a language
        model. Every number is a lookup, so this panel cannot hallucinate at you. Then these
        seven bars, which are the heart of it. Each bar is literally the weight multiplied by
        the z-score. Red pushed this ward up. Green pulled it down. [beat] That is not an
        explanation of the model. That is the model, shown back to you. Which is why there is no
        SHAP here. A transparent index does not need a post-hoc explainer.
    """)


def slide_16_guardrail():
    slide = base_slide(16, 5, "The guardrail, running on real data")

    _, _, _, ph = add_crop_screenshot(
        slide, "deck-ward-a-plantability-dark.png", MARGIN_L, 1.80, 7.30,
        crop_l=0.0, crop_r=0.245, crop_t=0.055, crop_b=0.0,
        max_h=4.05, center_in=7.30)
    add_body_text(
        slide,
        "Ward A. Green cells are ecologically suitable for planting, red cells are routed to cool "
        "roofs instead. The same ward carries both answers.",
        MARGIN_L, 1.80 + ph + 0.10, 7.30, 0.42, size=9, color=MUTED, align=PP_ALIGN.CENTER,
        line_spacing=1.15,
    )

    add_card_bg(slide, 8.20, 1.80, 4.58, 2.28, border=CRIMSON)
    add_dot_heading(slide, "Two recommendations, one ward", 8.46, 1.98, 4.06, 0.28,
                    size=12, dot=CRIMSON)
    add_body_text(
        slide,
        "\u25B8  Cool roofs + reflective pavements\n"
        "     \"afforestation would backfire ecologically\"\n"
        "     Veldman et al. 2019\n\n"
        "\u25B8  Native tree planting + green corridors\n"
        "     \"ecologically suitable for restoration\"\n"
        "     Bastin et al. 2019",
        8.46, 2.36, 4.10, 1.58, size=9.5, color=MUTED, line_spacing=1.22, space_before=2,
    )

    add_card_bg(slide, 8.20, 4.24, 4.58, 1.10, fill=PANEL_NESTED)
    add_body_text(slide, "Most tools cannot produce this pair.", 8.46, 4.42, 4.06, 0.28,
                  size=11, color=WHITE, bold=True)
    add_body_text(
        slide,
        "A tool that answers heat with \"plant trees\" has no way to say no. Saying no is the "
        "feature.",
        8.46, 4.72, 4.06, 0.50, size=9.3, color=MUTED, line_spacing=1.2,
    )

    add_crop_screenshot(slide, "deck-simulate-dark.png", 8.20, 5.44, 4.58,
                        crop_l=0.21, crop_r=0.21, crop_t=0.745, crop_b=0.02,
                        max_h=0.90, center_in=4.58,
                        caption="The what-if estimator, also cited coefficient by coefficient.",
                        caption_size=8.5)

    set_notes(slide, """
        If you remember one slide from today, make it this one. [beat] Switch to the
        plantability layer. Green means trees belong here. Red means they do not. Now look at
        the panel. This is Ward A, holding both answers at once. One card says cool roofs,
        because afforestation would backfire ecologically. Veldman. Directly below it, another
        says plant native trees, because that part suits restoration. Bastin. Same ward.
        Opposite advice. Different cells. Both traceable to a paper. A tool that answers heat
        with plant more trees cannot produce that pair. Saying no is the feature.
    """)


def slide_17_holdup():
    slide = base_slide(17, 5, "Does it hold up?",
                       sub="The hardest question a researcher can ask an index is whether the answer survives the weights changing.")

    _, _, _, sh = add_crop_screenshot(
        slide, "deck-methodology-sensitivity-dark.png", MARGIN_L, 1.92, 7.30,
        crop_l=0.235, crop_r=0.235, crop_t=0.28, crop_b=0.28,
        max_h=3.36, center_in=7.30)
    add_body_text(
        slide,
        f"All {F['n_runs']} perturbation runs, plotted. Every bar sits near 1.0.",
        MARGIN_L, 1.92 + sh + 0.10, 7.30, 0.30, size=9, color=MUTED, align=PP_ALIGN.CENTER,
    )

    add_body_text(slide, "THE TEST", MARGIN_L, 5.76, 3.0, 0.26, size=9.5, color=MUTED,
                  font=FONT_MONO, bold=True)
    add_body_text(
        slide,
        f"Perturb each of the 7 weights by \u00b1{F['perturb'] * 100:.0f} %, one at a time, "
        f"renormalise, and recompute the entire ward ranking. {F['n_runs']} runs.",
        MARGIN_L, 6.06, 7.30, 0.55, size=10, color=MUTED, line_spacing=1.2,
    )

    add_stat_box(slide, 8.20, 1.92, 4.58, 1.22, f"{F['tau']:.3f}",
                 "mean Kendall tau against the baseline ranking. 1.0 would be a perfectly "
                 "identical order.", number_size=26, layout="row")
    add_stat_box(slide, 8.20, 3.28, 4.58, 1.22, f"{F['overlap']:.1f} / 5",
                 "mean overlap in the top five wards across every perturbation run.",
                 number_size=26, layout="row", number_color=AMBER)

    add_card_bg(slide, 8.20, 4.64, 4.58, 1.97, fill=PANEL_NESTED, border=AMBER)
    add_dot_heading(slide, "Where it is not perfect", 8.46, 4.82, 4.06, 0.28, size=12, dot=AMBER)
    add_body_text(
        slide,
        "The overlap is 4.4, not 5. In 2 of the 14 runs the fifth ward swaps.\n"
        "The reason is not instability in the method. Ward F/S scores 64.838 and Ward B scores "
        "64.819. They are 0.019 apart, which is a tie in any practical sense.\n"
        "I would rather show you that than round it away.",
        8.46, 5.20, 4.10, 1.32, size=9.4, color=MUTED, line_spacing=1.2, space_before=5,
    )

    set_notes(slide, """
        Now the question I was most afraid of. [beat] You picked those weights from one run, on
        one city, on one day. What if they are simply wrong? So I attacked it before you could.
        I moved every weight by twenty percent, up and down, one at a time, and recomputed the
        entire ranking. Fourteen runs. Mean Kendall tau against the baseline, zero point nine
        seven eight, where one would be identical. Mean top-five overlap, four point four out of
        five. And I want to stop on that second number, because four point four is not five, and
        I could have quietly rounded it. [beat] In two runs the fifth ward swaps. But Ward F
        south and Ward B are nineteen thousandths of a point apart. That is a tie, and any
        perturbation flips a tie.
    """)


# ---------------------------------------------------------------------------
# 06 - IMPACT & FUTURE SCOPE
# ---------------------------------------------------------------------------

def slide_18_limits():
    slide = base_slide(18, 6, "Limitations, stated openly")

    items = [
        ("Land-surface temperature is not air temperature.",
         "Satellites measure the temperature of the ground, not what a person standing on it feels. "
         "The two correlate but they are not the same number, and the site says so on the landing page."),
        ("Cooling coefficients are transferred, not Mumbai-calibrated.",
         "Ziter measured Madison, Bowler is a global meta-analysis. I apply their numbers to Mumbai "
         "because no local field study exists yet. That is an assumption, not a measurement."),
        ("Slum and elderly layers are proxies.",
         "WorldPop 2020 modelled rasters and mapped slum-cluster boundaries, not a ward-level "
         "census. Elderly share varies only from 4.0 to 5.6 % across the whole city, so it "
         "separates wards weakly, and I do not lean on it."),
        ("The what-if estimator is first-order, not a climate model.",
         "It sums three cited coefficients as independent terms. There is no coupled physics and "
         "no check for double-counting between canopy and park area."),
        ("The plantability layer is coarse.",
         "10 m land-cover classes aggregated to a 1 km cell. It is good enough to catch grassland, "
         "not good enough to site an individual tree."),
    ]
    y = 1.72
    for lead, rest in items:
        add_card_bg(slide, MARGIN_L, y, 8.30, 0.86, fill=PANEL_NESTED)
        add_lead_body(slide, MARGIN_L + 0.24, y + 0.10, 7.85, 0.70, "\u25B8  " + lead, rest,
                      lead_size=10.5, rest_size=9.3, line_spacing=1.18)
        y += 0.94

    add_card_bg(slide, 9.20, 1.72, 3.58, 4.66, border=EMERALD)
    add_dot_heading(slide, "Why this slide exists", 9.46, 1.94, 3.1, 0.28, size=12.5)
    add_body_text(
        slide,
        "Most city heat tools present their outputs as more certain than they are. A planner then "
        "acts on that certainty, and when it turns out to be wrong the whole category loses "
        "credibility.\n\n"
        "This is the product feature I am most confident about.\n\n"
        "Every one of these limits is on the public methodology page, not just in this deck. The "
        "small-ward caveat is there too. Ward C ranks first on only 2 grid cells, while Ward R/C "
        "has 61, so small wards are noisier by construction.\n\n"
        "If you find a limitation I have not listed, I want to hear it, and it goes on the page.",
        9.46, 2.34, 3.10, 3.90, size=9.6, color=MUTED, line_spacing=1.22, space_before=6,
    )

    set_notes(slide, """
        And now let me spend a minute arguing against my own project. [beat] Land surface
        temperature is not air temperature. Satellites read the ground, not what your skin
        feels. My cooling coefficients were measured in Madison, Wisconsin, and I apply them to
        Mumbai because no local study exists. That is an assumption wearing the costume of a
        measurement. My slum and elderly layers are proxies. Why put this on a slide at a
        competition? Because tools that oversell certainty get believed, then get caught, and
        then nobody believes the next one. I would rather be the tool you can check than the
        tool you have to trust.
    """)


def slide_19_impact():
    slide = base_slide(19, 6, "Impact")

    add_card(slide, MARGIN_L, 1.78, 3.86, 2.42, "For Mumbai",
             "Turns an existing diagnosis into an operational answer. Which ward first, why that "
             "ward, and what to build there. A planner with a finite budget gets a defensible "
             "starting order instead of an intuition they cannot show anyone.", dot=TEAL)

    add_card(slide, MARGIN_L + 4.04, 1.78, 3.86, 2.42, "For other cities",
             "Every input is free and public. Porting to Pune, Ahmedabad or Delhi needs a different "
             "boundary file, not a different method, and not a data-purchase budget. The pipeline "
             "and the citations travel unchanged.", dot=EMERALD)

    add_card(slide, MARGIN_L + 8.08, 1.78, 3.86, 2.42, "For the field",
             "Apache 2.0, public repository, method and limitations documented in the open. The "
             "guardrail idea in particular is worth copying, whatever happens to this specific "
             "tool.", dot=AMBER)

    add_body_text(slide, "WHAT CHANGES ON MONDAY MORNING", MARGIN_L, 4.48, 6.0, 0.26,
                  size=9.5, color=MUTED, font=FONT_MONO, bold=True)
    add_pill_list(slide, MARGIN_L, 4.80, 11.94, 1.55, [
        ("A planner", "opens one URL, sorts 24 wards by measured need, and can show the reasoning "
                      "to a committee, factor by factor, with a paper behind each one."),
        ("A resident", "types their neighbourhood name, sees their own ward's score and what is "
                       "recommended for it, and can read exactly what the tool does not know."),
    ], gap=0.12, lead_size=11, rest_size=9.8)

    set_notes(slide, """
        So, back to that rooftop. What actually changes? [beat] For Mumbai, a diagnosis becomes
        an instruction. Which ward, why that ward, what to build there. A planner gets an order
        they can defend in a room, factor by factor, instead of an instinct they cannot. For
        other cities, and this is the part I care most about, remember what I asked you to hold
        on to. Every input was free and public. Porting this to Pune or Ahmedabad is a boundary
        file and a day of work, not a procurement cycle.
    """)


def slide_20_future():
    slide = base_slide(20, 6, "Future scope")

    items = [
        ("Finer grid, 1 km to 500 m.",
         "A single constant in the grid stage. It quadruples cell count and directly fixes the "
         "small-ward noise problem, because Ward C would stop resting on 2 cells."),
        ("Mumbai-calibrated cooling coefficients.",
         "Replace the transferred Madison and meta-analysis numbers with local field measurement. "
         "This is the limitation I would most like to close."),
        ("Budget allocation layer.",
         "Maximise vulnerability reduction per rupee across wards. This is the fifth capability "
         "from the matrix on slide eight. Designed, not built, and not claimed."),
        ("Census-linked demographics.",
         "Replace the WorldPop and slum-cluster proxies with real ward-level counts when they "
         "become accessible."),
        ("Replication kit.",
         "Config-driven port to another city, so the boundary file is the only thing that changes."),
    ]
    y = 1.72
    for lead, rest in items:
        add_card_bg(slide, MARGIN_L, y, 7.85, 0.84, fill=PANEL_NESTED)
        add_lead_body(slide, MARGIN_L + 0.24, y + 0.10, 7.40, 0.68, "\u25B8  " + lead, rest,
                      lead_size=10.5, rest_size=9.3, line_spacing=1.18)
        y += 0.92

    add_card_bg(slide, 8.72, 1.72, 4.06, 2.10, border=TEAL)
    add_dot_heading(slide, "Honest status", 8.98, 1.92, 3.5, 0.28, size=12, dot=TEAL)
    add_body_text(
        slide,
        "Rows one, two and four are extensions of something that already works.\n"
        "Row three is the one thing this deck promised nowhere else: the budget layer does not "
        "exist yet, and I have kept it off every earlier slide.",
        8.98, 2.32, 3.56, 1.36, size=9.5, color=MUTED, line_spacing=1.22, space_before=6,
    )

    add_gradient_bar(slide, x=8.72, y=4.10, w=1.3, h=0.06)
    add_body_text(slide, "UCIP.\nWhich ward, why,\nand what to build.",
                  8.72, 4.36, 4.06, 1.30, size=20, color=WHITE, bold=True,
                  font=FONT_HEAD, line_spacing=1.18)

    add_card_bg(slide, 8.72, 5.82, 4.06, 0.56, fill=PANEL_NESTED)
    add_body_text(slide, "github.com/AnayDhawan/UCIP", 8.98, 5.82, 3.56, 0.56, size=10.5,
                  color=TEAL, font=FONT_MONO, anchor=MSO_ANCHOR.MIDDLE)

    add_body_text(
        slide,
        "Apache 2.0. Every data source free and public. Thank you, and I am happy to take "
        "questions on the method.",
        MARGIN_L, 6.40, 7.85, 0.40, size=10, color=MUTED,
    )

    set_notes(slide, """
        Where this goes. A five hundred metre grid, one constant, which fixes the honest
        weakness I showed you, that Ward C rests on two cells. Cooling coefficients measured in
        Mumbai instead of borrowed from Wisconsin. And the budget layer, that fifth empty
        column, which I will say once more does not exist yet, which is exactly why it is on
        this slide and no other. I started by telling you about someone on a top floor at forty
        degrees. [beat] I cannot cool that roof. But I can tell you, with receipts, that hers is
        the one to cool first. UCIP. Which ward, why, and what to build. Thank you. Ask me the
        hard ones.
    """)


# ---------------------------------------------------------------------------
# Backup + validation + main
# ---------------------------------------------------------------------------


BUILDERS = [
    slide_01_title, slide_02_claim,
    slide_03_uneven, slide_04_who, slide_05_matters,
    slide_06_measured, slide_07_literature, slide_08_priorart,
    slide_09_chain, slide_10_indicators, slide_11_weights, slide_12_rules,
    slide_13_arch, slide_14_dashboard, slide_15_explain, slide_16_guardrail, slide_17_holdup,
    slide_18_limits, slide_19_impact, slide_20_future,
]

SLIDE_SECTION = [1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 5, 6, 6, 6]

def main():
    check_shots()
    backup_existing(OUT_PATH, BACKUP_PATH)
    for build in BUILDERS:
        build()
    prs.save(OUT_PATH)
    # v2 is the technical cut, kept for reference. Per-slide source lines are a v3 requirement;
    # v2 has not been retrofitted, so it opts out of that assert rather than failing on it.
    validate(OUT_PATH, TOTAL_SLIDES, MIN_TOTAL_SEC, MAX_TOTAL_SEC, SLIDE_SECTION,
             require_sources=False)


if __name__ == "__main__":
    main()
