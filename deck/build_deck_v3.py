"""
Generates UCIP-Pitch-Deck-v3.pptx: the v3 (plain-language) 20-slide, 15-minute pitch deck.

Same layout as v2, same 6 organizer sections, same slide count. Two differences:

  1. Plain words. No PCA, no z-score, no NDVI, no Kendall tau, no choropleth on a slide.
     The technical terms still exist in the pipeline and in FAQ.md; they are simply not the
     language a non-specialist judge has to decode in real time.
  2. The opening is built around one causal chain, stated on slide 2 and then walked link by
     link across slides 3 to 5:
         more heat  ->  greater health risk  ->  citizens suffer  ->  cities must choose
     and the last link is where the tool lives: to break the chain, a city has to know where
     to act first.

Layout primitives, brand tokens and the pipeline-fact loader live in deck_kit.py, shared with
build_deck.py, so v2 and v3 cannot drift apart on layout.

Usage: python build_deck_v3.py   (run from this directory)
"""

import os

from deck_kit import (
    F, SEC, OUT_DIR, MARGIN_L, PAPERS, DATA_SOURCES,
    BG, COVER_GLOW, PANEL_NESTED, INK, MUTED, SUBTITLE_INK, WHITE,
    TEAL, EMERALD, AMBER, CRIMSON,
    FONT_HEAD, FONT_BODY, FONT_MONO,
    new_presentation, use, new_slide, set_background, set_notes,
    add_kicker, add_heading, add_gradient_bar, add_dot_heading, add_body_text,
    add_card_bg, add_card, add_stat_box, add_pill_list, add_callout,
    add_table, add_bar_row, add_flow_box, add_arrow, add_brand_lockup, add_slide_number,
    add_source_line,
    add_crop_screenshot, base_slide,
    backup_existing, validate, check_shots,
    Inches, rgb, MSO_SHAPE, MSO_ANCHOR, PP_ALIGN,
)

TOTAL_SLIDES = 21
MIN_TOTAL_SEC = 14 * 60
MAX_TOTAL_SEC = 15 * 60

# Verified 2026-08-04: the site, /methodology and /legal all return 200.
LIVE_URL = "ucip-eight.vercel.app"
CODE_URL = "github.com/AnayDhawan/UCIP"
WHERE_TO_FIND_IT = f"Live at {LIVE_URL}. Code at {CODE_URL}." if LIVE_URL else f"Code at {CODE_URL}."

# Every claim on a slide has to be checkable from that slide. These strings are hand written
# rather than pasted from citations.ts, whose `usage` fields contain em dashes that validate()
# rejects. Where a figure is the pipeline's own output, the line says so instead of staying
# silent: that distinction is the whole argument of slide 6.
PIPELINE = "computed by my own pipeline"

SRC = {
    1: f"{WHERE_TO_FIND_IT} Every figure in this deck is {PIPELINE}, from openly licensed data. "
       f"Sources are given on the slide where each claim appears, and in full on slide 21. The "
       f"opening observation, that named storms are taken more seriously than unnamed heat "
       f"waves, is Eleni Myrivili's, UN Global Chief Heat Officer.",
    2: "The chain is my framing. Evidence for each link follows on slides 3 to 5.",
    3: "Landsat 8/9 Collection 2 (USGS), ESA WorldCover v200, WorldPop 2020, OpenStreetMap, "
       "Datameet. Global anomaly map: NASA Goddard Scientific Visualization Studio, GISTEMP v4, "
       "1880 to 2024. Ward figures " + PIPELINE + ".",
    4: "Reid et al. 2009, Environ Health Perspect, doi 10.1289/ehp.0900683 (age and isolation as "
       "heat-vulnerability factors). Hospital locations: OpenStreetMap. Ward distances " + PIPELINE + ".",
    5: "Heat deaths in India 2000 to 2020, three official counts: NCRB 20,615, NDMA 17,767, "
       "IMD 10,545 (Gadgil and Narang, Down To Earth, 10 April 2025). Ahmedabad: Knowlton et al. "
       "2014, IJERPH, doi 10.3390/ijerph110403473. Mumbai Climate Action Plan 2022 (BMC, WRI "
       "India, C40).",
    6: "Landsat 8/9 Collection 2 (USGS), ESA WorldCover v200, WorldPop 2020, OpenStreetMap "
       "(ODbL), Datameet. Composited in Google Earth Engine. Every figure on this slide is "
       + PIPELINE + ".",
    7: "Ziter et al. 2019, PNAS, doi 10.1073/pnas.1817561116. Santamouris 2014, Solar Energy, "
       "doi 10.1016/j.solener.2012.07.003. Bastin et al. 2019, Science, doi 10.1126/science.aax0848 "
       "and Veldman et al. 2019, Science, doi 10.1126/science.aay7976.",
    8: "Mumbai Climate Action Plan 2022 (BMC, WRI India, C40); Azhar et al. 2017, doi "
       "10.3390/ijerph14040357; Mehrotra, Bardhan and Ramamritham 2018, doi 10.1177/0975425318783548; "
       "C40 and Ramboll, Urban Cooling Toolbox 2021; Knowlton et al. 2014. Each row reflects what "
       "that tool's own publications claim to do, read and tabulated by me.",
    9: "The four steps are my design. Each one is evidenced on the slides that follow.",
    10: "Indicator set and the direction of each one follow Reid et al. 2009, doi "
        "10.1289/ehp.0900683, and Azhar et al. 2017, doi 10.3390/ijerph14040357. Values " + PIPELINE + ".",
    11: "Weighting method follows Reid et al. 2009, doi 10.1289/ehp.0900683. Weights, explained "
        "variance and the fallback state are read from data/hvi_pca_log.json, " + PIPELINE + ".",
    12: "Planting gate: Bastin et al. 2019 and Veldman et al. 2019, Science. Cooling evidence: "
        "Ziter et al. 2019, PNAS, and Santamouris 2014, Solar Energy. Rule output: "
        "data/nbs_recommendations.json, " + PIPELINE + ".",
    13: "Google Earth Engine, Supabase Postgres, Next.js and Leaflet. Basemap tiles: CARTO and "
        "OpenStreetMap contributors. The offline test was run by me on 2026-07-24. " + WHERE_TO_FIND_IT,
    14: "Ward boundaries: Datameet BMC_Wards. Basemap: CARTO and OpenStreetMap contributors. "
        "Ranking read from data/wards_hvi.geojson, " + PIPELINE + ".",
    15: "Screenshot of the live site. The contribution bars are computed from the same weights "
        "and standardised values as the score itself, " + PIPELINE + ".",
    16: "Land cover: ESA WorldCover v200, classes 30 (grassland) and 50 (built up). Refusal rule "
        "follows Bastin et al. 2019 and Veldman et al. 2019, Science. Cooling estimates: Ziter "
        "et al. 2019, Santamouris 2014, Bowler et al. 2010.",
    17: f"{F['n_runs']} runs, each weight moved plus and minus 20 percent in turn. Rank "
        "correlation and top-five overlap read from data/sensitivity.json, " + PIPELINE + ".",
    18: "Land surface temperature against air temperature: a standard limitation of thermal "
        "remote sensing. Cooling coefficients are transferred from Ziter et al. 2019, "
        "Santamouris 2014 and Bowler et al. 2010, not measured in Mumbai. Population estimates: "
        "WorldPop 2020. The same list is published on the site's methodology page.",
    19: "All eight datasets behind this work are openly licensed; the full list is on slide 21. "
        + WHERE_TO_FIND_IT,
    20: f"The roadmap is mine. {WHERE_TO_FIND_IT} Limitation being closed by item two: cooling "
        "coefficients from Ziter et al. 2019 and Santamouris 2014 are transferred, not local.",
    21: "Read at build time from the same citation module the live site renders, so this list "
        "cannot drift from the one published online.",
}

OUT_PATH = os.path.join(OUT_DIR, "UCIP-Pitch-Deck-v3.pptx")
BACKUP_PATH = os.path.join(OUT_DIR, "UCIP-Pitch-Deck-v3.bak.pptx")

prs = new_presentation()
use(prs, sections=SEC, total=TOTAL_SLIDES)

# The chain, reused as a visual motif on slides 2 to 5 so the argument stays visible.
CHAIN = [
    ("01", "More heat", "Mumbai is heating,\nand not evenly"),
    # Two lines, not three: the strip is drawn at h=0.72 on slides 3 to 5 and a third line
    # spills below the card border there.
    ("02", "Discomfort, then illness", "discomfort for all, danger\nfor some, load on hospitals"),
    ("03", "Citizens suffer", "hardest where people\ncan least cope"),
    ("04", "So where to act first?", "one budget,\ntwenty four wards"),
]


def chain_strip(slide, y, active=None, bw=2.72, h=1.30, gap_arrow=0.38):
    """Draw the four-link chain. `active` dims the other links so one stands out."""
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
    add_heading(slide, "UCIP: Urban Climate Intelligence Platform", MARGIN_L, 1.72, 6.85, 1.6, size=34)
    add_gradient_bar(slide, x=MARGIN_L, y=3.40, w=1.3, h=0.06)
    add_body_text(
        slide,
        "Built for Mumbai's 24 wards. It says which ward to cool first, why that one, "
        "and what to build there.",
        MARGIN_L, 3.62, 6.60, 0.9, size=14, color=SUBTITLE_INK, line_spacing=1.3,
    )

    add_card_bg(slide, MARGIN_L, 4.62, 6.5, 2.20)
    meta_rows = [
        ("STUDENT NAME", "Anay Dhawan"),
        ("SCHOOL", "NES International School Mumbai"),
        ("GRADE", "11 (IBDP Year 1)"),
        ("DOMAIN", "PLANET"),
        ("FOCUS AREA", "Urban heat and public health"),
        ("STUDY AREA", "Mumbai, 24 BMC wards"),
    ]
    ty = 4.74
    row_h = 1.96 / 6
    for label, value in meta_rows:
        add_body_text(slide, label, MARGIN_L + 0.20, ty, 2.0, row_h, size=9, color=MUTED,
                      font=FONT_MONO, anchor=MSO_ANCHOR.MIDDLE)
        add_body_text(slide, value, MARGIN_L + 2.30, ty, 3.90, row_h, size=11.5, color=INK,
                      bold=True, anchor=MSO_ANCHOR.MIDDLE)
        ty += row_h

    add_crop_screenshot(slide, "deck-hero-dark.png", 7.55, 1.72, 5.25,
                        crop_l=0.46, crop_r=0.0, crop_t=0.10, crop_b=0.02,
                        max_h=4.42, center_in=5.25,
                        caption="Every ward in Mumbai, raised and coloured by its heat risk.",
                        caption_size=8.5)

    add_brand_lockup(slide)
    add_slide_number(slide, 1)
    add_source_line(slide, SRC[1])

    set_notes(slide, """
        [COLD OPEN. Do not introduce yourself yet. Stand still. Slower than feels natural. Let
        the first silence sit longer than is comfortable.] Right now, somewhere above this room,
        a family is living under a metal roof. [beat] This afternoon, the ground beneath that
        roof measured forty degrees. Three kilometres away, another rooftop measured twenty six.
        [slower] Same city. Same afternoon. Same sun. Fourteen degrees apart. [beat] We give
        hurricanes names. We do not give heat waves names, and so we do not take them seriously.
        [beat] Mumbai does not have a heat problem. It has twenty four of them, one for every
        ward, and it treats them as though it had one. [beat, then normal pace] My name is Anay
        Dhawan. I am in Grade eleven at NES International School. For the next fifteen minutes I
        want to walk you along a chain that runs from that roof to a hospital bed, and show you
        the one link in it a city can actually break.
    """)


def slide_02_chain():
    slide = new_slide()
    set_background(slide)
    add_kicker(slide, SEC[1])
    add_gradient_bar(slide, x=MARGIN_L, y=1.05, w=1.3, h=0.06)

    add_body_text(slide, "The problem, stated as one chain",
                  MARGIN_L, 1.45, 11.8, 0.5, size=27, color=WHITE, bold=True, font=FONT_HEAD)

    chain_strip(slide, 2.30)

    add_card_bg(slide, MARGIN_L, 4.00, 11.94, 1.30, fill=PANEL_NESTED, border=EMERALD)
    add_body_text(
        slide,
        "You cannot switch off the sun. You can decide where to act first.",
        MARGIN_L + 0.30, 4.22, 11.3, 0.42, size=19, color=WHITE, bold=True, font=FONT_HEAD,
    )
    add_body_text(
        slide,
        "The first three links are physics and biology. The fourth is a decision, and a decision "
        "is the only part of a chain you can change on a Monday morning. That is the link this "
        "project works on.",
        MARGIN_L + 0.30, 4.72, 11.3, 0.50, size=10.5, color=MUTED, line_spacing=1.2,
    )

    add_pill_list(slide, MARGIN_L, 5.62, 11.94, 1.10, [
        ("How the next eighteen slides run.", "First the chain, link by link. Then what already "
         "exists and why it stops short. Then the tool itself, how it decides, what it refuses "
         "to do, and what it changes for Mumbai."),
    ], gap=0.10, lead_size=11, rest_size=10)

    add_brand_lockup(slide)
    add_slide_number(slide, 2)
    add_source_line(slide, SRC[2])

    set_notes(slide, """
        Here is the chain. It is short enough to hold in your head. [point to each link] More
        heat. Discomfort for everyone, illness for some, and a load on the hospitals. Citizens
        suffer. So a city has to decide where to act. [beat] The first three links are physics
        and biology. Nobody in this room can switch off the sun. [beat] But look at the fourth
        one. That link is not physics. It is a decision, made by a person, in a room, with a
        budget. And a decision is the only part of a chain you can change on a Monday morning.
        [beat] So that is the link I built for. Not measuring heat. That is done. Deciding where
        to act. That is not.
    """)


# ---------------------------------------------------------------------------
# 02 - PROBLEM UNDERSTANDING
# ---------------------------------------------------------------------------

def slide_03_more_heat():
    slide = base_slide(3, 2, "Link one: more heat, and it lands unevenly", sources=SRC[3])
    city = F["city"]

    chain_strip(slide, 1.42, active=0, bw=2.30, h=0.72, gap_arrow=0.30)

    add_callout(slide, MARGIN_L, 2.42, 7.4, 1.00, "13.7 °C",
                "difference between the coolest and the hottest square kilometre of this city, "
                "measured on the same day, from the same satellite pass.",
                number_size=26, accent=CRIMSON)

    rows = [
        ("How hot the ground gets", "26 °C to 40 °C", f"{city['LST_C']:.0f} °C"),
        ("How green it is", "almost bare to lush", "patchy"),
        ("Concrete and paving", "0 % to 97 %", f"{city['impervious_pct']:.0f} %"),
        ("People per square kilometre", "16 to 115,000", f"{city['pop_density_km2']:,.0f}"),
        ("Walk to the nearest hospital", "next door to 6 km", f"{city['hospital_dist_m']:,.0f} m"),
    ]
    add_table(slide, MARGIN_L, 3.66, 7.4, 2.44,
              ["Indicator", "Range across Mumbai", "City average"],
              rows, [3.0, 2.55, 1.85], body_size=9.4)

    add_body_text(
        slide,
        "One city-wide average erases all of it. Every gap above is somewhere you could act.",
        MARGIN_L, 6.28, 7.4, 0.4, size=10.5, color=INK, bold=True,
    )

    add_crop_screenshot(slide, "deck-global-heat-anomaly.png", 8.30, 2.42, 4.48,
                        crop_l=0.41, crop_r=0.03, crop_t=0.01, crop_b=0.10,
                        max_h=3.68, center_in=4.48,
                        caption="Not only here. NASA's map of how much warmer each part of the "
                                "world now runs.")

    set_notes(slide, """
        Link one. More heat. [beat] And the important word in that sentence is not more. It is
        uneven. Ground temperature across Mumbai runs from twenty six degrees to forty. Concrete
        cover, from nothing to almost everything. Population, from sixteen people per square
        kilometre to a hundred and fifteen thousand. [beat] Now average all of it. Mumbai is
        thirty two degrees. That is true. It is also useless, because nobody lives in an average.
        [gesture right] And this is not a Mumbai quirk. That is NASA's map of where the world has
        warmed. Mumbai is simply where I could test it first.
    """)


def slide_04_health_risk():
    slide = base_slide(4, 2, "Link two: heat is uncomfortable for everyone and dangerous for some",
                       heading_size=23, sources=SRC[4])

    chain_strip(slide, 1.42, active=1, bw=2.30, h=0.72, gap_arrow=0.30)

    cw = 2.86
    gap = 0.16
    cx = MARGIN_L
    for title, body, dot in [
        ("Homes that hold heat",
         "Metal and asbestos roofs soak up heat all day and give it back all night. The body "
         "never gets the cool break it needs to recover.", CRIMSON),
        ("Older residents",
         "The risk of dying in a heat wave rises steeply with age, and older people are the "
         "least able to move somewhere cooler.", AMBER),
        ("Far from help",
         "Heat illness gets dangerous in hours. In this city, the distance to the nearest "
         "hospital ranges from next door to six kilometres.", TEAL),
        ("Out in it all day",
         "Anyone waiting at a bus stop or on a platform takes the full exposure, with no cool "
         "room to go back to.", EMERALD),
    ]:
        add_card(slide, cx, 2.42, cw, 1.76, title, body, dot=dot, body_size=9.6)
        cx += cw + gap

    add_card_bg(slide, MARGIN_L, 4.30, 5.85, 1.02, fill=PANEL_NESTED, border=AMBER)
    add_body_text(slide, "Why this is a public health problem, not a private discomfort",
                  MARGIN_L + 0.26, 4.46, 5.35, 0.46, size=11, color=WHITE, bold=True,
                  line_spacing=1.15)
    add_body_text(
        slide,
        "Everyone is uncomfortable. But the illness lands in the same weeks, in the same wards, "
        "on the same hospitals, and it arrives where the ambulance has furthest to travel.",
        MARGIN_L + 0.26, 4.92, 5.35, 0.34, size=9.6, color=MUTED, line_spacing=1.15,
    )

    add_card_bg(slide, MARGIN_L + 6.09, 4.30, 5.85, 1.02, fill=PANEL_NESTED, border=TEAL)
    add_body_text(slide, "And the people most at risk are the ones the city knows least about",
                  MARGIN_L + 6.35, 4.46, 5.35, 0.46, size=11, color=WHITE, bold=True,
                  line_spacing=1.15)
    add_body_text(
        slide,
        "Informal neighbourhoods are, almost by definition, the least surveyed places in any "
        "city. Waiting for perfect local records means never acting at all.",
        MARGIN_L + 6.35, 4.92, 5.35, 0.34, size=9.6, color=MUTED, line_spacing=1.15,
    )

    add_card_bg(slide, MARGIN_L, 5.46, 11.94, 0.92, fill=PANEL_NESTED, border=EMERALD)
    add_body_text(
        slide,
        "That pair is the reason a city has to rank wards rather than treat itself as one place.",
        MARGIN_L + 0.30, 5.62, 11.3, 0.32, size=15, color=WHITE, bold=True, font=FONT_HEAD,
    )
    add_body_text(
        slide,
        "So I built this from satellite images and public population data, which cover every ward "
        "equally, and made it state plainly which of its own numbers are estimates.",
        MARGIN_L + 0.30, 5.98, 11.3, 0.32, size=10, color=MUTED, line_spacing=1.15,
    )

    set_notes(slide, """
        Link two. Heat is uncomfortable for every person in this room. [beat] For four groups it
        stops being discomfort and becomes danger. People under metal roofs that soak heat up all
        day and give it back all night, so the body never recovers. Older residents. People far
        from help. Anyone who waits outside all day. [beat] And that is what makes it public
        health, not private discomfort. The illness lands in the same weeks, in the same wards,
        on the same hospitals, and it arrives where the ambulance has furthest to travel. [beat]
        Now the hard part. The people most at risk live exactly where the city knows least about
        them.
    """)


def slide_05_suffer_and_choose():
    slide = base_slide(5, 2, "Links three and four: people suffer, and someone has to choose",
                       sources=SRC[5])

    chain_strip(slide, 1.42, active=2, bw=2.30, h=0.72, gap_arrow=0.30)

    add_card(slide, MARGIN_L, 2.42, 5.85, 1.62,
             "Heat kills quietly, and India cannot agree how many",
             "Three government bodies counted heat deaths for the same twenty years and "
             "published 20,615, 17,767 and 10,545. Spread over a season instead of one dramatic "
             "day, heat rarely gets counted as an emergency, or counted well.",
             body_size=10, dot=CRIMSON)

    add_callout(slide, MARGIN_L, 4.24, 5.85, 1.30, "~1,190",
                "lives estimated saved every year in Ahmedabad after India's first heat action "
                "plan. It proves deliberate heat action works. What it does not do is say which "
                "part of a city to treat first: it is a forecast-triggered warning system.",
                number_size=25, accent=EMERALD)

    add_card_bg(slide, MARGIN_L + 6.09, 2.42, 5.85, 3.12, border=EMERALD)
    add_dot_heading(slide, "So why has nobody chosen?", MARGIN_L + 6.34, 2.62, 5.35, 0.30, size=13)
    add_body_text(
        slide,
        "Because choosing is harder than measuring.\n"
        "This city's climate plan already names heat as a priority. It is a serious document. "
        "But it sets goals for the whole city and stops there.\n"
        "It never answers the question a person with one budget actually faces: which ward gets "
        "cooled first, and how do I prove that was the right one?\n"
        "That is not missing data. It is a missing decision.",
        MARGIN_L + 6.34, 3.06, 5.35, 2.32, size=10.5, color=MUTED, line_spacing=1.22,
        space_before=7,
    )

    add_body_text(
        slide,
        "Break the chain here, and everything upstream still happens, but far fewer people get hurt.",
        MARGIN_L, 5.74, 11.94, 0.4, size=11, color=INK, bold=True,
    )

    set_notes(slide, """
        Links three and four. People suffer, and somebody has to choose. [beat] Heat kills
        quietly, and here is how badly that shows. Three government bodies counted India's heat
        deaths over the same twenty years and published twenty thousand, seventeen thousand, and
        ten thousand. Nobody is lying. It simply is not counted. [beat] So does acting save
        anyone? Ahmedabad's heat action plan is credited with roughly eleven hundred and ninety
        lives a year. It proves acting works. But it is forecast-triggered, so it says when to
        act, never where. [beat] Nobody has answered where, because choosing is harder than
        measuring. That is not missing data. It is a missing decision.
    """)


# ---------------------------------------------------------------------------
# 03 - RESEARCH & INSIGHTS
# ---------------------------------------------------------------------------

def slide_06_measured():
    slide = base_slide(6, 3, "I measured this myself, rather than reusing someone's heat map",
                       heading_size=23, sources=SRC[6],
                       sub="Every number in this deck came out of a pipeline I ran, not a report I found.")

    city = F["city"]
    stats = [
        ("12", "satellite passes\ncombined"),
        (f"{city['LST_C']:.0f} °C", "typical ground\ntemperature"),
        (f"{F['n_cells']}", "squares of the city\nscored separately"),
        (f"{F['n_wards']}", "wards covered,\nthe whole city"),
    ]
    bw, gap = 2.88, 0.20
    bx = MARGIN_L
    for num, label in stats:
        add_stat_box(slide, bx, 1.86, bw, 1.05, num, label, number_size=19)
        bx += bw + gap

    rows = [
        ("Satellite heat and greenery", "US Geological Survey", "How hot the ground is, how green"),
        ("Satellite land cover", "European Space Agency", "Concrete, water, grass, trees"),
        ("Population estimates", "WorldPop", "How many people, and how many are older"),
        ("Community map data", "OpenStreetMap", "Where the hospitals are"),
        ("Municipal boundaries", "Datameet, open data", "Ward outlines, informal settlements"),
    ]
    add_table(slide, MARGIN_L, 3.20, 11.94, 2.45,
              ["Dataset", "Published by", "What it provides"],
              rows, [3.85, 3.25, 4.84])

    add_body_text(
        slide,
        "Every one of these is free and public. Nobody has to buy anything to check this work, "
        "or to repeat it somewhere else.",
        MARGIN_L, 5.80, 7.8, 0.4, size=10.5, color=INK, bold=True,
    )
    add_body_text(
        slide,
        f"{F['n_citations']} research papers behind the method, listed in full on slide 21.",
        7.05, 5.80, 5.5, 0.4, size=10.5, color=EMERALD, bold=True, align=PP_ALIGN.RIGHT,
    )

    set_notes(slide, """
        So I had a choice. I could take somebody's published heat map and put a nice interface
        on it. Plenty of projects do. [beat] I did not. Every number here came out of a pipeline
        I ran. Twelve satellite passes, cloud and shadow removed. And look at what is
        underneath. Satellite images from the US Geological Survey and the European Space
        Agency. Population from WorldPop. Hospitals from OpenStreetMap. Boundaries from open
        municipal data. Every one free and public. Hold on to that. It matters at the end.
    """)


def slide_07_science():
    slide = base_slide(7, 3, "What the science says, including the finding I did not want",
                       sources=SRC[7])

    add_card(slide, MARGIN_L, 1.80, 3.86, 2.45, "A few trees will not do it",
             "Cooling only really begins once an area is roughly two fifths covered by "
             "tree canopy. Below that, planting a handful of trees looks good and changes almost "
             "nothing.\n\nZiter and colleagues, 2019", dot=EMERALD)

    add_card(slide, MARGIN_L + 4.04, 1.80, 3.86, 2.45, "Pale roofs work, reliably",
             "Painting a dark roof a reflective colour measurably drops the peak temperature "
             "underneath. It is cheap, it is fast, and it works on exactly the roofs that trap "
             "the most heat.\n\nSantamouris, 2014", dot=TEAL)

    add_card(slide, MARGIN_L + 8.08, 1.80, 3.86, 2.45, "Trees in the wrong place do harm",
             "Some open land is naturally grassland, not forest. Planting trees there damages "
             "the ecosystem that is already doing a job. Good intentions, real damage.\n\n"
             "Bastin 2019 and Veldman 2019", dot=CRIMSON)

    add_card_bg(slide, MARGIN_L, 4.50, 11.94, 1.82, fill=PANEL_NESTED, border=CRIMSON)
    add_body_text(slide, "Why the third finding changed the design", MARGIN_L + 0.30, 4.70, 7.0, 0.26,
                  size=11, color=WHITE, bold=True)
    add_body_text(
        slide,
        "Almost every green-city tool answers heat with the same three words: plant more trees. "
        "Two teams of scientists arguing in the journal Science established that this is wrong "
        "often enough to matter. So this tool does not recommend planting until it has checked "
        "whether trees belong there, and when the answer is no, it says no and suggests pale "
        "roofs instead. I will show that running shortly.",
        MARGIN_L + 0.30, 5.02, 11.3, 1.10, size=10.5, color=MUTED, line_spacing=1.22,
    )

    set_notes(slide, """
        Three findings shaped this tool. Two of them I expected. [beat] First, a few trees will
        not do it. Cooling only really begins once an area is about two fifths covered in
        canopy. Below that, planting a handful of trees looks good in a photograph and changes
        almost nothing. Second, pale reflective roofs work, cheaply and reliably. [beat] And then
        there is the third, which I did not want to be true. Some open land is naturally
        grassland, and planting trees there damages an ecosystem already doing a job. [beat]
        Almost every green-city tool answers heat with the same three words. Plant more trees.
        After reading that, I could not.
    """)


def slide_08_priorart():
    slide = base_slide(8, 3, "Five serious efforts already exist. None of them combines all five jobs.",
                       heading_size=23, sources=SRC[8],
                       sub="Every one of these is better resourced than I am. This is what each "
                           "one sets out to do, not a scorecard of how well it does it.")

    rows = [
        ("Mumbai Climate Action Plan 2022", "city scale", "no", "yes", "no", "no"),
        ("RAND India heat risk study 2017", "640 districts", "partly", "no", "no", "no"),
        ("IIT Bombay Mumbai heat mapping", "yes", "partly", "no", "no", "no"),
        ("C40 global cooling toolbox", "no", "no", "yes", "no", "partly"),
        ("Ahmedabad heat action plan", "no", "no", "yes", "no", "no"),
        ("UCIP", "24 wards", "yes", "yes", "yes", "planned"),
    ]
    add_table(slide, MARGIN_L, 2.05, 11.94, 2.90,
              ["Tool", "Ranks every\nward", "Explains\nwhy", "Names an\nintervention",
               "Refuses unsuitable\nones", "Handles\nbudget"],
              rows, [4.14, 1.86, 1.44, 1.62, 1.74, 1.14],
              body_size=8.8, header_size=8.4, highlight_last=True)

    add_card_bg(slide, MARGIN_L, 5.10, 7.85, 1.30, fill=PANEL_NESTED, border=TEAL)
    add_body_text(
        slide,
        "Each one is built for at most two of these five jobs. This is built for four.",
        MARGIN_L + 0.28, 5.27, 7.3, 0.38, size=14.5, color=WHITE, bold=True, font=FONT_HEAD,
    )
    add_body_text(
        slide,
        "The fifth, spending a fixed budget well, is designed but not built. It appears on the "
        "last slide as a plan, and is not claimed here as a feature.",
        MARGIN_L + 0.28, 5.70, 7.3, 0.52, size=10, color=MUTED, line_spacing=1.2,
    )

    add_stat_box(slide, 8.72, 5.10, 1.95, 1.30, "640",
                 "districts nationally in\nthe closest study", number_size=20, number_color=AMBER)
    add_stat_box(slide, 10.83, 5.10, 1.95, 1.30, f"{F['n_wards']}",
                 "wards this resolves\ninside one of them",
                 number_size=20, number_color=EMERALD)

    set_notes(slide, """
        Now the obvious question. Surely somebody has already built this. [beat] Five serious
        efforts exist, every one better resourced than I am. Mumbai's own climate plan names
        heat, at city scale. The RAND study is peer reviewed, but covers six hundred and forty
        districts, so all of Mumbai is one dot. IIT Bombay's mapping is rigorous and local, and
        it diagnoses: where it is hot, then stops. C40's toolbox is generic, with no Mumbai data
        underneath. Ahmedabad tells you when, not where. [beat] None of that is a criticism. Each
        was built for a different job. What nobody has done is put all five jobs in one tool.
    """)


# ---------------------------------------------------------------------------
# 04 - PROPOSED SOLUTION
# ---------------------------------------------------------------------------

def slide_09_four_steps():
    slide = base_slide(9, 4, "The solution, in four steps: score, explain, suggest, check",
                       sources=SRC[9])

    steps = [
        ("01", "Score", "Every ward gets\none heat risk number,\n0 to 100"),
        ("02", "Explain", "Show which factors\npushed that number up,\nand by how much"),
        ("03", "Suggest", "Turn the score into a\nspecific thing to build,\nwith the research behind it"),
        ("04", "Check", "Refuse the suggestion\nif it would damage\nwhat is already there"),
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

    add_body_text(slide, "Who it is built for", MARGIN_L, 4.10, 6.0, 0.26, size=11,
                  color=WHITE, bold=True)
    add_pill_list(slide, MARGIN_L, 4.42, 11.94, 1.88, [
        ("City officials:", "a ranked list they can defend in a meeting, where every position can "
                            "be traced back to the thing that caused it."),
        ("Residents:", "a plain answer to why their ward ranks where it does, and what "
                       "is being suggested for it."),
        ("Researchers and NGOs:", "the full method, the data sources, and a written list of what "
                                  "the tool cannot do."),
    ], gap=0.10, lead_size=11, rest_size=9.8)

    set_notes(slide, """
        So here is the whole thing, in four words. [beat] Score. Explain. Suggest. Check. [beat]
        Score gives every ward one number out of a hundred. Explain shows which factors pushed it
        up. Suggest turns that into a specific thing you could build. [beat] And check is the
        step almost nobody has. It refuses its own suggestion if building it would damage what is
        already there. Remember that fourth one. It is the part of this I would defend hardest.
        [beat] Three people use it. Officials who have to defend a decision. Residents who
        deserve a plain answer. And researchers, who get the method and a written list of what it
        cannot do.
    """)


def slide_10_factors():
    slide = base_slide(10, 4, "The seven things that go into the score", sources=SRC[10])

    rows = [
        ("How hot the ground gets", "raises risk", "The hazard itself."),
        ("How green it is", "lowers risk", "Plants cool the air around them."),
        ("How crowded it is", "raises risk", "More people exposed in the same space."),
        ("Share of older residents", "raises risk", "Heat deaths climb steeply with age."),
        ("Share of informal housing", "raises risk", "Roofs that trap heat, little relief indoors."),
        ("Distance to a hospital", "raises risk", "Heat illness is dangerous within hours."),
        ("Concrete and paving", "raises risk", "Hard surfaces store heat and release it at night."),
    ]
    add_table(slide, MARGIN_L, 1.80, 11.94, 3.35,
              ["Indicator", "Direction", "Why it is included"],
              rows, [4.10, 2.20, 5.64], body_size=9.2)

    add_card_bg(slide, MARGIN_L, 5.35, 5.85, 1.10, fill=PANEL_NESTED)
    add_body_text(slide, "I did not invent this list.",
                  MARGIN_L + 0.26, 5.52, 5.35, 0.30, size=11, color=WHITE, bold=True)
    add_body_text(
        slide,
        "These are the factors published heat risk studies already use. Greenery is the only one "
        "where more of it means less risk.",
        MARGIN_L + 0.26, 5.83, 5.35, 0.50, size=9.5, color=MUTED, line_spacing=1.18,
    )

    add_card_bg(slide, MARGIN_L + 6.09, 5.35, 5.85, 1.10, fill=PANEL_NESTED)
    add_body_text(slide, "Everything is put on the same scale first.",
                  MARGIN_L + 6.35, 5.52, 5.35, 0.30, size=11, color=WHITE, bold=True)
    add_body_text(
        slide,
        "Degrees, people and metres are different units. They get converted to a common scale so "
        "no factor wins simply because its numbers are bigger.",
        MARGIN_L + 6.35, 5.83, 5.35, 0.50, size=9.5, color=MUTED, line_spacing=1.18,
    )

    set_notes(slide, """
        Seven factors go in. How hot the ground gets. How green it is, the one where more means
        safer. How crowded. How many older residents. How much informal housing. How far the
        nearest hospital is. And how much concrete, because hard surfaces hold heat into the
        night. [beat] Now, the question I would be asking if I were sitting where you are. Where
        does he get to put his thumb on the scale? Two places. The first is deciding which way
        each factor points, and I did not decide that, the published research did. The second is
        how much each counts. Next slide.
    """)


def slide_11_weights():
    slide = base_slide(11, 4, "How much should each factor count?", sources=SRC[11])

    add_card_bg(slide, MARGIN_L, 1.80, 6.90, 1.10, fill=PANEL_NESTED, border=AMBER)
    add_body_text(slide, "The easy way, and why I did not take it",
                  MARGIN_L + 0.26, 1.98, 6.4, 0.30, size=11.5, color=WHITE, bold=True)
    add_body_text(
        slide,
        "Most risk scores let the author pick the weights. Pick numbers that feel about right, "
        "publish, and nobody can check you.",
        MARGIN_L + 0.26, 2.30, 6.4, 0.50, size=10, color=MUTED, line_spacing=1.18,
    )

    add_callout(slide, MARGIN_L, 3.02, 6.90, 0.86,
                "58%",
                "of the variation between wards comes down to one underlying pattern. Strong "
                "enough that I let that pattern set the weights, instead of setting them by hand.",
                number_size=24, accent=EMERALD)

    add_body_text(slide, "The weights the data produced", MARGIN_L, 4.06, 6.0, 0.26, size=11,
                  color=WHITE, bold=True)

    labels = {
        "impervious_pct": "Concrete and paving",
        "pop_density_km2": "How crowded",
        "LST_C": "Ground temperature",
        "NDVI": "How green",
        "hospital_dist_m": "Distance to hospital",
        "slum_pct": "Informal housing",
        "elderly_pct": "Older residents",
    }
    ordered = sorted(F["weights"].items(), key=lambda kv: -kv[1])
    wmax = 0.20
    ry = 4.38
    for key, val in ordered:
        add_bar_row(slide, MARGIN_L, ry, 6.90, 0.30, labels[key], val / wmax,
                    f"{val * 100:.0f}%", label_w=2.05, value_w=0.72)
        ry += 0.32

    add_card_bg(slide, 7.75, 1.80, 5.03, 1.14, fill=PANEL_NESTED, border=AMBER)
    add_dot_heading(slide, "To be exact about what I did choose", 8.00, 1.96, 4.6, 0.28,
                    size=11.5, dot=AMBER)
    add_body_text(
        slide,
        "I chose the seven factors and which direction each one points, both taken from published "
        "studies. What I did not choose is how much each one counts. That is the part the data "
        "sets, and it is the part that is usually hidden.",
        8.00, 2.28, 4.53, 0.58, size=9.4, color=MUTED, line_spacing=1.15,
    )

    add_card_bg(slide, 7.75, 3.02, 5.03, 0.88, fill=PANEL_NESTED, border=TEAL)
    add_dot_heading(slide, "The safety catch", 8.00, 3.14, 4.5, 0.26, size=11.5, dot=TEAL)
    add_body_text(
        slide,
        "Below a set threshold the program stops trusting that pattern and counts every factor "
        "equally instead. It did not need to here, and the site says so.",
        8.00, 3.44, 4.53, 0.38, size=9.2, color=MUTED, line_spacing=1.12,
    )

    # Cropped to the bar rows only. The paragraph above them is written for a technical
    # reader and would undercut the plain-language framing of this deck.
    add_crop_screenshot(slide, "deck-methodology-weights-dark.png", 7.75, 4.06, 5.03,
                        crop_l=0.21, crop_r=0.21, crop_t=0.395, crop_b=0.31,
                        max_h=2.24, center_in=5.03,
                        caption="The website reads these numbers straight from the program's own output.")

    set_notes(slide, """
        This is where most risk scores quietly cheat. The author picks how much each factor
        counts, publishes, and nobody can check them. [beat] So let me be exact about what I
        chose. I chose the seven factors and which direction each points, both from published
        studies. I did not choose how much each counts. The program finds the strongest pattern
        across the seven and lets that set the weights. Here that one pattern explains fifty
        eight percent of the variation between wards. [beat] Concrete counts most. Older
        residents least. Not the order I expected, but I did not get a vote. And if the pattern
        had been weak, the program counts everything equally instead.
    """)


def slide_12_rules():
    slide = base_slide(12, 4, "From a score to something you can actually build", sources=SRC[12])

    rows = [
        ("Plant native trees and green corridors", "Hot, bare, and trees belong there", "1"),
        ("Pale roofs and reflective paving", "Hot and bare, but trees do NOT belong", "1"),
        ("Cooling centres, placed deliberately", "Many older residents, far from a hospital", "1"),
        ("Rain gardens and soak-away paving", "Lots of concrete, close to water", "2"),
        ("Pocket parks", "Very crowded, almost no open space", "3"),
    ]
    add_table(slide, MARGIN_L, 1.80, 7.85, 2.55,
              ["Intervention", "When it is suggested", "Priority"],
              rows, [3.95, 3.15, 0.75], body_size=8.8)

    add_card_bg(slide, MARGIN_L, 4.55, 7.85, 1.80, fill=PANEL_NESTED, border=CRIMSON)
    add_dot_heading(slide, "The check, in plain words", MARGIN_L + 0.26, 4.74, 7.3, 0.28,
                    size=12, dot=CRIMSON)
    add_body_text(
        slide,
        "Trees are allowed only if the ground is not already built on, not water or wetland,\n"
        "not naturally grassland, and not almost entirely paved over.\n"
        "Fail any one of those and the suggestion switches to pale roofs instead.",
        MARGIN_L + 0.26, 5.12, 7.3, 0.95, size=10, color=EMERALD, line_spacing=1.28,
        space_before=3,
    )

    stats = [
        (f"{F['n_nbs']}", "suggestions generated,\ncovering every ward"),
        ("38%", "of the city where planting trees\nwould be the wrong answer"),
        ("5", "kinds of intervention, each with\nits own research behind it"),
    ]
    sy = 1.80
    for num, label in stats:
        add_stat_box(slide, 8.72, sy, 4.06, 1.05, num, label, number_size=20, layout="row")
        sy += 1.17

    add_card_bg(slide, 8.72, 5.35, 4.06, 1.00, fill=PANEL_NESTED)
    add_body_text(
        slide,
        "The first two rows are the same situation with opposite answers. What decides between "
        "them is the check.",
        8.98, 5.52, 3.56, 0.70, size=9.5, color=MUTED, line_spacing=1.2,
    )

    set_notes(slide, """
        A score on its own is still only a diagnosis. So it feeds a set of rules, each naming a
        thing to build and how urgent it is. [beat] Look at the top two rows. They contradict
        each other on purpose. They fire in the same situation, a hot bare ward, and give
        opposite answers. What decides between them is the check. Trees are allowed only if the
        ground is not already built on, not water, not naturally grassland, and not almost
        entirely paved. [beat] And here is the number that surprised me most. That check rules
        out planting across thirty eight percent of Mumbai.
    """)


# ---------------------------------------------------------------------------
# 05 - PROTOTYPE / SOLUTION DESIGN
# ---------------------------------------------------------------------------

def slide_13_how_built():
    slide = base_slide(13, 5, "How the prototype works, end to end", sources=SRC[13])

    boxes = [
        ("01", "Free public data", "Satellite images,\npopulation estimates,\nmaps"),
        ("02", "Processing", f"{F['n_stages']} steps that clean it,\nscore it, and apply\nthe rules"),
        ("03", "Stored twice", "In a database,\nand as plain files\nthe site can read"),
        ("04", "Website", "A map anyone can\nopen and click,\nno login"),
        ("05", "Published", "Live on the web,\nand the code is\npublic"),
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
        (f"{F['n_cells']}", "squares measured"),
        (f"{F['n_nbs']}", "suggestions made"),
        (f"{F['n_stages']}", "processing steps"),
        (f"{F['n_citations']}", "research papers used"),
    ]
    bw2, gap2 = 2.30, 0.16
    bx = MARGIN_L
    for num, label in stats:
        add_stat_box(slide, bx, 3.68, bw2, 0.92, num, label, number_size=20)
        bx += bw2 + gap2

    add_card_bg(slide, MARGIN_L, 4.80, 11.94, 1.62, fill=PANEL_NESTED, border=EMERALD)
    add_dot_heading(slide, "The decision I would defend hardest, and it is not a feature",
                    MARGIN_L + 0.30, 4.98, 9.0, 0.28, size=12.5, dot=EMERALD)
    add_body_text(
        slide,
        "Every demo has one thing that can kill it: the internet dropping out. So the results are "
        "written to plain files on the website itself before anything is sent to a database, and "
        "the site never calls out to the database while you are using it. I tested that by "
        "cutting off both data providers at the network level and walking through the whole thing. "
        "Nothing broke. This demo cannot be killed by bad wifi, and that was decided on day one, "
        "not patched the night before.",
        MARGIN_L + 0.30, 5.36, 11.34, 0.95, size=10.2, color=MUTED, line_spacing=1.2,
    )

    set_notes(slide, """
        How the prototype actually works. Free public data comes in. Thirteen steps clean it,
        score it and apply the rules. Results are stored twice, and a website draws the map.
        [beat] Now one decision, and it is not a feature. Every demo has one thing that can kill
        it, and it is the wifi. So the results are written as plain files on the site itself, and
        the site never calls out while you are using it. [beat] And I tested that rather than
        assuming it. I cut both data providers off at the network level and walked the whole
        thing. Nothing broke.
    """)


def slide_14_map():
    slide = base_slide(14, 5, "The map: every ward in Mumbai, ranked by measured risk",
                       sources=SRC[14])

    add_crop_screenshot(slide, "deck-dashboard-hvi-dark.png", MARGIN_L, 1.80, 8.05,
                        crop_l=0.0, crop_r=0.10, crop_t=0.055, crop_b=0.0,
                        max_h=4.42, center_in=8.05,
                        caption="Darker means more at risk. The list beside it is the same "
                                "information, ranked.")

    add_body_text(slide, "The five highest ranked wards", 8.92, 1.80, 4.0, 0.26,
                  size=11, color=WHITE, bold=True)

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
        add_body_text(slide, f"{hvi:.0f}", 11.98, ry, 0.66, 0.52, size=11.5, color=CRIMSON,
                      bold=True, font=FONT_MONO, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.RIGHT)
        ry += 0.60

    add_card_bg(slide, 8.92, 5.20, 3.86, 1.02, fill=PANEL_NESTED)
    add_body_text(
        slide,
        "You can search by the name people actually use. Type Dharavi and it finds the right "
        "ward. Every ward has its own web link you can send to someone.",
        9.18, 5.32, 3.36, 0.56, size=9.3, color=MUTED, line_spacing=1.2,
    )
    add_body_text(slide, LIVE_URL or CODE_URL, 9.18, 5.90, 3.36, 0.24, size=9.5,
                  color=TEAL, font=FONT_MONO)

    set_notes(slide, """
        So here it is. Every ward, coloured by risk, with the same information ranked
        beside it, and a key that stays on screen, because a coloured map nobody can read is
        decoration, not help. And I want to be precise about one thing. [beat] I did not choose
        this order. I did not put Dharavi near the top because Dharavi is the famous answer. The
        ward containing Dharavi came second on its own. And two small things. You can search by
        the name people actually use. And every ward has its own link, so an official
        sends a colleague one place, not a screenshot.
    """)


def slide_15_explain():
    slide = base_slide(15, 5, "Click one ward, and it explains itself", sources=SRC[15])

    add_crop_screenshot(slide, "deck-ward-c-dark.png", MARGIN_L, 1.80, 7.30,
                        crop_l=0.752, crop_r=0.005, crop_t=0.055, crop_b=0.0,
                        max_h=4.42, center_in=7.30,
                        caption="Every number here is looked up, not generated.")

    add_card(slide, 8.20, 1.80, 4.58, 1.62, "Written in plain English",
             "\"This ward runs about 3 degrees hotter than the city average.\" Those sentences are "
             "assembled from the ward's own measurements. There is no AI writing them, so they "
             "cannot make something up.", body_size=9.5)

    add_card(slide, 8.20, 3.58, 4.58, 1.42, "The bars are the reason",
             "Each bar shows how much one factor pushed this ward's score up or down. "
             "Red pushed it up. Green pulled it down. Add them together and you get the score "
             "itself.", body_size=9.5, dot=CRIMSON)

    add_card_bg(slide, 8.20, 5.16, 4.58, 1.06, fill=PANEL_NESTED, border=EMERALD)
    add_body_text(slide, "Nothing here is a black box.", 8.46, 5.33, 4.06, 0.30,
                  size=11.5, color=WHITE, bold=True)
    add_body_text(
        slide,
        "You are not being shown a guess about how the score was made. You are being shown the "
        "arithmetic that made it.",
        8.46, 5.64, 4.06, 0.50, size=9.3, color=MUTED, line_spacing=1.2,
    )

    set_notes(slide, """
        Now click the one at the top. [beat] First, three sentences of plain English, assembled
        from that ward's own measurements. There is no AI writing them, which means they cannot
        make anything up. [beat] Then these bars, which are the heart of it. Each shows how much
        one factor pushed this ward up or down. Red pushed it up. Green pulled it down. [beat]
        And here is the part I care about. Add those bars together and you get the score itself.
        You are being shown the arithmetic, not an explanation of it.
    """)


def slide_16_check():
    slide = base_slide(16, 5, "The check, running on real data: where this tool refuses to plant",
                       heading_size=23, sources=SRC[16])

    _, _, _, ph = add_crop_screenshot(
        slide, "deck-ward-a-plantability-dark.png", MARGIN_L, 1.80, 7.30,
        crop_l=0.0, crop_r=0.245, crop_t=0.055, crop_b=0.0,
        max_h=4.05, center_in=7.30)
    add_body_text(
        slide,
        "Green squares: trees belong here. Red squares: they do not, so pale roofs instead. "
        "One ward, both answers.",
        MARGIN_L, 1.80 + ph + 0.10, 7.30, 0.42, size=9, color=MUTED, align=PP_ALIGN.CENTER,
        line_spacing=1.15,
    )

    add_card_bg(slide, 8.20, 1.80, 4.58, 2.28, border=CRIMSON)
    add_dot_heading(slide, "Two opposite answers, one place", 8.46, 1.98, 4.06, 0.28,
                    size=12, dot=CRIMSON)
    add_body_text(
        slide,
        "▸  Pale roofs and reflective paving\n"
        "     \"planting here would do ecological harm\"\n\n"
        "▸  Plant native trees and green corridors\n"
        "     \"this part genuinely suits restoration\"\n\n"
        "Same ward. Different squares. Each one\n"
        "linked to the paper it came from.",
        8.46, 2.36, 4.10, 1.58, size=9.5, color=MUTED, line_spacing=1.22, space_before=2,
    )

    add_card_bg(slide, 8.20, 4.24, 4.58, 1.10, fill=PANEL_NESTED)
    add_body_text(slide, "Most tools cannot produce that pair.", 8.46, 4.42, 4.06, 0.28,
                  size=11, color=WHITE, bold=True)
    add_body_text(
        slide,
        "A tool whose only answer is plant more trees has no way of ever saying no. Saying no is "
        "the point.",
        8.46, 4.72, 4.06, 0.50, size=9.3, color=MUTED, line_spacing=1.2,
    )

    add_crop_screenshot(slide, "deck-simulate-dark.png", 8.20, 5.44, 4.58,
                        crop_l=0.21, crop_r=0.21, crop_t=0.745, crop_b=0.02,
                        max_h=0.90, center_in=4.58,
                        caption="Move a slider, and the estimated cooling updates.",
                        caption_size=8.5)

    set_notes(slide, """
        If you remember one slide from today, make it this one. [beat, then click to the tree
        layer] Green squares mean trees belong there. Red squares mean they do not. [beat] Now
        look at the panel on the right. This is one ward, holding two opposite answers at the
        same time. The first card says pale roofs, because planting there would do ecological
        harm. Directly below it, the second says plant native trees, because that part genuinely
        suits it. [slower] Same ward. Opposite advice. Different squares. Both cited. [beat] A
        tool whose only answer is plant more trees has no way of ever saying no. Saying no is the
        point.
    """)


def slide_17_holdup():
    slide = base_slide(17, 5, "Does the answer hold up if you push it?", sources=SRC[17],
                       sub="The fairest attack on any score is that the author picked the weights. So I ran that attack myself.")

    _, _, _, sh = add_crop_screenshot(
        slide, "deck-methodology-sensitivity-dark.png", MARGIN_L, 1.92, 7.30,
        crop_l=0.235, crop_r=0.235, crop_t=0.28, crop_b=0.28,
        max_h=3.36, center_in=7.30)
    add_body_text(
        slide,
        f"All {F['n_runs']} test runs. Every bar sits near the top, meaning the order barely moved.",
        MARGIN_L, 1.92 + sh + 0.10, 7.30, 0.30, size=9, color=MUTED, align=PP_ALIGN.CENTER,
    )

    add_body_text(slide, "How I tested it", MARGIN_L, 5.76, 3.0, 0.26, size=11, color=WHITE,
                  bold=True)
    add_body_text(
        slide,
        "Change how much each factor counts by a fifth, up and down, one at a time, then redo the "
        f"whole ranking from scratch. {F['n_runs']} runs.",
        MARGIN_L, 6.06, 7.30, 0.55, size=10, color=MUTED, line_spacing=1.2,
    )

    add_stat_box(slide, 8.20, 1.92, 4.58, 1.22, "almost\nunchanged",
                 "the ranking stayed nearly identical every time I changed the weights.",
                 number_size=17, layout="row")
    add_stat_box(slide, 8.20, 3.28, 4.58, 1.22, "4 of 5",
                 "the same wards stayed in the top five, on average, across every run.",
                 number_size=24, layout="row", number_color=AMBER)

    add_card_bg(slide, 8.20, 4.64, 4.58, 1.97, fill=PANEL_NESTED, border=AMBER)
    add_dot_heading(slide, "Where it is not perfect", 8.46, 4.82, 4.06, 0.28, size=12, dot=AMBER)
    add_body_text(
        slide,
        "It is four out of five, not five out of five. In 2 of the 14 runs, the fifth place "
        "swapped.\n"
        "That is not the method wobbling. Those two wards score 64.84 and 64.82. They are "
        "effectively tied, and any nudge flips a tie.\n"
        "I would rather show you that than round it away.",
        8.46, 5.20, 4.10, 1.32, size=9.4, color=MUTED, line_spacing=1.2, space_before=5,
    )

    set_notes(slide, """
        Now the question I was most afraid of. [beat] What if those weights are simply wrong? So
        I ran that attack before you could. I moved every factor's weight by a fifth, up and
        down, one at a time, and redid the whole ranking. Fourteen times. The order barely moved.
        [beat] On average, four of the same five stayed in the top five. And I want to stop on
        that, because four out of five is not five, and I could have quietly rounded it. In two
        runs the fifth place swapped. That is not the method wobbling. Those two wards are tied
        to two decimal places, and any nudge flips a tie.
    """)


# ---------------------------------------------------------------------------
# 06 - IMPACT & FUTURE SCOPE
# ---------------------------------------------------------------------------

def slide_18_limits():
    slide = base_slide(18, 6, "What this tool does not know", sources=SRC[18])

    items = [
        ("Satellites measure the ground, not the air.",
         "What the satellite records is how hot the surface is, which is related to, but not the "
         "same as, the temperature a person standing there actually feels."),
        ("The cooling numbers were measured in another country.",
         "The figures for how much trees and pale roofs cool things down come from studies "
         "elsewhere, because nobody has run that experiment in Mumbai yet. That is a borrowed "
         "assumption, not a local measurement."),
        ("Some of the population data is an estimate.",
         "The figures on informal housing and older residents are modelled from satellite and "
         "map data, not counted door to door. They are good enough to rank with, and not good "
         "enough to quote as fact."),
        ("The slider tool gives a rough estimate.",
         "It adds up published figures. It is not a weather model, and it does not simulate what "
         "would really happen to your street."),
        ("The tree check works at street-block scale.",
         "It is reliable for saying this area is grassland. It is not precise enough to tell you "
         "where to put one particular tree."),
    ]
    y = 1.72
    for lead, rest in items:
        add_card_bg(slide, MARGIN_L, y, 8.30, 0.86, fill=PANEL_NESTED)
        add_body_text(slide, "▸  " + lead, MARGIN_L + 0.24, y + 0.10, 7.85, 0.24,
                      size=10.5, color=WHITE, bold=True)
        add_body_text(slide, rest, MARGIN_L + 0.24, y + 0.36, 7.85, 0.44,
                      size=9.3, color=MUTED, line_spacing=1.18)
        y += 0.94

    add_card_bg(slide, 9.20, 1.72, 3.58, 4.66, border=EMERALD)
    add_dot_heading(slide, "Why this slide exists", 9.46, 1.94, 3.1, 0.28, size=12.5)
    add_body_text(
        slide,
        "Most tools like this present their answers as more certain than they really are. "
        "Someone acts on that certainty, it turns out to be wrong, and afterwards nobody trusts "
        "any of them.\n\n"
        "This is the part of the project I am most confident about.\n\n"
        "All of it is on the public website too, not just in this deck. Including the awkward "
        "one: the top-ranked ward is small, so its score rests on fewer measurements than a large "
        "ward's does.\n\n"
        "If you spot something I have missed, I want to hear it, and it goes on the list.",
        9.46, 2.34, 3.10, 3.90, size=9.6, color=MUTED, line_spacing=1.22, space_before=6,
    )

    set_notes(slide, """
        Now let me spend a minute arguing against my own project. [beat] Satellites measure the
        ground, not the air, so what I record is related to what a person feels, but is not the
        same. The cooling figures are borrowed from studies abroad. Some population data is
        modelled, not counted. [beat] Why put this on a slide at a competition? Because tools
        that oversell certainty get believed, then get caught, and then nobody trusts the next
        one. I would rather be the tool you can check than the tool you have to trust.
    """)


def slide_19_impact():
    slide = base_slide(19, 6, "The impact: who this helps, and what it changes", sources=SRC[19])

    add_card(slide, MARGIN_L, 1.78, 3.86, 2.42, "Mumbai",
             "It turns something already known, that the city is hot, into something you can act "
             "on: this ward first, for this reason, build this. Someone with a fixed budget gets "
             "a starting order they can defend, instead of a hunch they cannot.",
             dot=TEAL)

    add_card(slide, MARGIN_L + 4.04, 1.78, 3.86, 2.42, "Any other city",
             "Every input is free and public. Moving this to another city needs a different map "
             "of its boundaries, not a different method and not a purchase. That is the whole "
             "reason I insisted on open data.", dot=EMERALD)

    add_card(slide, MARGIN_L + 8.08, 1.78, 3.86, 2.42, "Anyone working on this",
             "The code is public and free to reuse. The idea worth copying is not the map. It is "
             "that a heat tool should sometimes refuse to give the popular answer.", dot=AMBER)

    add_body_text(slide, "What changes in practice", MARGIN_L, 4.48, 7.0, 0.26,
                  size=11, color=WHITE, bold=True)
    add_pill_list(slide, MARGIN_L, 4.80, 11.94, 1.55, [
        ("An official", "opens one link, sees every ward ranked by measured need, and can show a "
                        "committee exactly what drove the order, factor by factor."),
        ("A resident", "types the name of their own neighbourhood, sees its score and what is "
                       "suggested for it, and can read what the tool admits it does not know."),
    ], gap=0.12, lead_size=11, rest_size=9.8)

    set_notes(slide, """
        So what actually changes? [beat] For Mumbai, something already known becomes something
        you can act on. This ward first, for this reason, build this. Someone with a fixed budget
        gets an order they can defend in a room, instead of a hunch they cannot. [beat] For any
        other city, and this is the part I care most about, remember what I asked you to hold on
        to. Every input is free and public. Moving this needs a different boundary file. It does
        not need a different method, and it does not need money.
    """)


def slide_20_future():
    slide = base_slide(20, 6, "What comes next", sources=SRC[20])

    items = [
        ("Look at the city in finer detail.",
         "Halving the size of each measured square would make the smallest wards far more "
         "reliable. It is a one-line change."),
        ("Measure the cooling here, instead of borrowing it.",
         "Put sensors on real roofs in this city and replace the borrowed figures with local "
         "ones. This is the limitation I would most like to close."),
        ("Add the budget.",
         "Work out how to get the most risk reduction per rupee across wards. This is "
         "the fifth column that was empty earlier. It is designed, and it does not exist yet."),
        ("Use real counts when they become available.",
         "Replace the estimated population figures with proper local records if and when those "
         "open up."),
        ("Make it easy to move to another city.",
         "Package it so the next city only has to supply its own boundaries."),
    ]
    y = 1.72
    for lead, rest in items:
        add_card_bg(slide, MARGIN_L, y, 7.85, 0.84, fill=PANEL_NESTED)
        add_body_text(slide, "▸  " + lead, MARGIN_L + 0.24, y + 0.10, 7.40, 0.24,
                      size=10.5, color=WHITE, bold=True)
        add_body_text(slide, rest, MARGIN_L + 0.24, y + 0.35, 7.40, 0.42,
                      size=9.3, color=MUTED, line_spacing=1.18)
        y += 0.92

    add_card_bg(slide, 8.72, 1.72, 4.06, 2.10, border=TEAL)
    add_dot_heading(slide, "Being straight about this list", 8.98, 1.92, 3.5, 0.28, size=12, dot=TEAL)
    add_body_text(
        slide,
        "Four of these five make something that already works better.\n"
        "The third one is different. The budget feature does not exist, which is exactly why it "
        "appears here and nowhere earlier in this deck.",
        8.98, 2.32, 3.56, 1.36, size=9.5, color=MUTED, line_spacing=1.22, space_before=6,
    )

    add_gradient_bar(slide, x=8.72, y=4.10, w=1.3, h=0.06)
    add_body_text(slide, "Which ward, why,\nand what to build.",
                  8.72, 4.42, 4.06, 1.10, size=20, color=WHITE, bold=True,
                  font=FONT_HEAD, line_spacing=1.18)

    add_card_bg(slide, 8.72, 5.74, 4.06, 0.64, fill=PANEL_NESTED, border=TEAL)
    add_body_text(slide, LIVE_URL or CODE_URL, 8.98, 5.78, 3.56, 0.28, size=11.5,
                  color=TEAL, font=FONT_MONO, anchor=MSO_ANCHOR.MIDDLE)
    add_body_text(slide, CODE_URL, 8.98, 6.06, 3.56, 0.26, size=9, color=MUTED,
                  font=FONT_MONO, anchor=MSO_ANCHOR.MIDDLE)

    add_body_text(
        slide,
        "I cannot cool that roof. I can tell you, with evidence, which one to cool first.",
        MARGIN_L, 6.40, 7.85, 0.40, size=11, color=INK, bold=True,
    )

    set_notes(slide, """
        Three things next. Finer detail, a one-line change that fixes a weakness I showed you.
        Measure the cooling in Mumbai instead of borrowing it, the limitation I would most like
        to close. And build the budget layer, that fifth empty column, which does not exist yet,
        which is exactly why it is on this slide and nowhere earlier. [beat, slow right down] I
        began by telling you about a family under a metal roof at forty degrees. [beat] I cannot
        cool that roof. Nobody in this room can switch off the sun. [beat] But I can now tell
        you, with evidence you are free to go and check tonight, that theirs is the roof to cool
        first. Which ward. Why. And what to build. [beat] Thank you.
    """)


def slide_21_sources():
    """Every paper and dataset behind the deck, on one page.

    Built from deck_kit.PAPERS / DATA_SOURCES, which are parsed out of the frontend's own
    citation module, so this page cannot drift from the bibliography the live site renders.
    """
    slide = base_slide(21, 6, "Every source behind this deck", sources=SRC[21],
                       sub="Not presented. This page exists so any claim in the deck can be "
                           "traced without asking me.")

    add_body_text(slide, f"Research papers ({len(PAPERS)})", MARGIN_L, 1.76, 6.0, 0.26,
                  size=11, color=WHITE, bold=True)
    rows = [(a, v, d) for a, v, d in PAPERS]
    add_table(slide, MARGIN_L, 2.06, 7.55, 4.05,
              ["Authors", "Venue", "DOI"],
              rows, [2.15, 2.55, 2.85], body_size=7.4, header_size=8.0)

    add_body_text(slide, f"Data sources ({len(DATA_SOURCES)}), all openly licensed",
                  8.42, 1.76, 4.4, 0.26, size=11, color=WHITE, bold=True)
    add_table(slide, 8.42, 2.06, 4.37, 4.05,
              ["Dataset", "Used for"],
              list(DATA_SOURCES), [1.95, 2.42], body_size=7.0, header_size=8.0)

    # Sources cited on a slide but not held in citations.ts: the imagery credit, the heat
    # mortality figures, and the three prior-art tools that are reports rather than papers.
    add_body_text(slide, "Also cited in this deck", MARGIN_L, 6.22, 6.0, 0.24,
                  size=10, color=WHITE, bold=True)
    add_body_text(
        slide,
        "Global temperature anomaly imagery: NASA Goddard Space Flight Center, Scientific "
        "Visualization Studio, GISTEMP v4 (slide 3). India heat mortality, three official counts: "
        "Gadgil and Narang, Down To Earth, 10 April 2025 (slide 5). Mumbai Climate Action Plan "
        "2022, BMC with WRI India and C40 (slides 5 and 8). Mehrotra, Bardhan and Ramamritham "
        "2018, doi 10.1177/0975425318783548 (slide 8). C40 and Ramboll, Urban Cooling Toolbox "
        "2021 (slide 8).",
        MARGIN_L, 6.48, 12.24, 0.46, size=7.4, color=MUTED, line_spacing=1.15,
    )

    set_notes(slide, """
        [APPENDIX. Not presented and not timed. Open this only if a judge asks where something
        came from. Built from the same citation module the live site renders.]
    """)


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

BUILDERS = [
    slide_01_title, slide_02_chain,
    slide_03_more_heat, slide_04_health_risk, slide_05_suffer_and_choose,
    slide_06_measured, slide_07_science, slide_08_priorart,
    slide_09_four_steps, slide_10_factors, slide_11_weights, slide_12_rules,
    slide_13_how_built, slide_14_map, slide_15_explain, slide_16_check, slide_17_holdup,
    slide_18_limits, slide_19_impact, slide_20_future, slide_21_sources,
]

SLIDE_SECTION = [1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 5, 6, 6, 6, 6]


def main():
    check_shots()
    backup_existing(OUT_PATH, BACKUP_PATH)
    for build in BUILDERS:
        build()
    prs.save(OUT_PATH)
    validate(OUT_PATH, TOTAL_SLIDES, MIN_TOTAL_SEC, MAX_TOTAL_SEC, SLIDE_SECTION)


if __name__ == "__main__":
    main()
