#!/usr/bin/env python3
"""Draw the 24 November 2026 world-news front page (1024x1024 PNG).

One code-drawn newspaper page: a nameplate, one lead market story, two
second stories, a two-column digest of 30 verified items, and a two-line
footer ticker — 39 stories in total, all checked against reports
published on Tuesday 24 November 2026 (see news-20261124-shortlist.md).

Everything is flat rules, panels and type drawn by this program; there
are no photographs and no copied images. The output is deterministic:
the same input always writes the same bytes.
"""

import sys

from PIL import Image, ImageDraw, ImageFont

PAGE = 1024
EDGE = 28
INNER = PAGE - 2 * EDGE

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANSB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

PAPER = (247, 243, 232)
CARD = (255, 253, 246)
INK = (22, 22, 22)
SOFT = (104, 99, 88)
RULE = (198, 192, 178)
CRIMSON = (172, 32, 22)
NAVY = (26, 74, 132)
FOREST = (16, 102, 86)
GRAPE = (88, 56, 138)
TEAL = (44, 108, 120)
OCHRE = (164, 98, 0)
BAND = (30, 32, 38)

TAGCOL = {
    "WORLD": CRIMSON,
    "US": NAVY,
    "TECH": GRAPE,
    "ASIA": OCHRE,
    "SPORT": (146, 38, 88),
    "CLIMATE": FOREST,
}


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(drw, text, fnt, width):
    """Greedy word wrap of text to a pixel width; returns the lines."""
    words = text.split()
    lines = []
    cur = ""
    for word in words:
        trial = (cur + " " + word).strip()
        if drw.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def para(drw, x, y, text, fnt, color, width, leading):
    """Draw a wrapped paragraph; returns the y just below it."""
    for line in wrap(drw, text, fnt, width):
        drw.text((x, y), line, font=fnt, fill=color)
        y += leading
    return y


def hline(drw, x0, x1, y, color, weight=1):
    drw.rectangle([x0, y, x1, y + weight - 1], fill=color)


def nameplate(drw):
    """Masthead: paper name, date line, double rule."""
    title = font(SERIF, 56)
    drw.text((PAGE // 2, 30), "THE WORLD TODAY", font=title, fill=INK,
             anchor="ma")
    datef = font(SANSB, 15)
    drw.text((PAGE // 2, 96), "TUESDAY 24 NOVEMBER 2026  ·  39 STORIES  ·  SIX CONTINENTS",
             font=datef, fill=SOFT, anchor="ma")
    hline(drw, EDGE, PAGE - EDGE, 122, CRIMSON, 4)
    hline(drw, EDGE, PAGE - EDGE, 129, RULE, 1)


def lead_story(drw, top):
    """Full-width lead: Nvidia's Tuesday pullback + the Dow's 50k day."""
    kick = font(SANSB, 15)
    head = font(SERIF, 33)
    deck = font(SANS, 16)
    stat = font(SANSB, 13)
    statv = font(SANS, 13)
    x = EDGE
    y = top
    drw.text((x, y), "MARKETS  ·  TECH", font=kick, fill=CRIMSON)
    y += 24
    y = para(drw, x, y, "Nvidia gives back a slice of Monday's record rally",
             head, INK, INNER, 40)
    y += 4
    y = para(drw, x, y,
             "Shares close at $155.38, down 5.9%, as profit-taking hits the AI "
             "trade — but the Dow tops 50,000 for the first time",
             deck, INK, INNER, 21)
    y += 10
    # Stat strip: four small boxes with the day's market numbers.
    boxes = [
        ("NVDA", "$155.38  −5.9%"),
        ("DOW", "50,018.70  +0.9%"),
        ("NASDAQ", "23,733.54  −1.5%"),
        ("S&P 500", "7,201.09  −0.5%"),
    ]
    bw = (INNER - 3 * 10) // 4
    bx = x
    for name, val in boxes:
        drw.rectangle([bx, y, bx + bw, y + 34], outline=RULE, width=1)
        drw.text((bx + 10, y + 4), name, font=stat, fill=SOFT)
        drw.text((bx + 10, y + 18), val, font=statv, fill=INK)
        bx += bw + 10
    return y + 34


def second_story(drw, x, y, width, tag, color, head, body):
    """One of the two second-tier stories in a half-width column."""
    kick = font(SANSB, 13)
    headf = font(SERIF, 21)
    bodyf = font(SANS, 13)
    drw.text((x, y), tag, font=kick, fill=color)
    y += 21
    y = para(drw, x, y, head, headf, INK, width, 25)
    y += 3
    y = para(drw, x, y, body, bodyf, SOFT, width, 17)
    return y


def digest_item(drw, x, y, width, tag, text):
    """One bulletin row: coloured tag, then a headline over two lines."""
    labelf = font(SANSB, 11)
    bodyf = font(SANS, 12)
    label = tag + "  "
    lw = drw.textlength(label, font=labelf)
    drw.text((x, y), label, font=labelf, fill=TAGCOL[tag])
    first = width - lw
    lines = wrap(drw, text, bodyf, first)
    if len(lines) > 1:
        # Re-wrap the overflow at full width for the second line.
        rest = " ".join(lines[1:])
        second = wrap(drw, rest, bodyf, width)
        lines = [lines[0]] + second[:1]
    drw.text((x + lw, y), lines[0], font=bodyf, fill=INK)
    if len(lines) > 1:
        drw.text((x, y + 14), lines[1], font=bodyf, fill=INK)
    if len(lines) > 2:
        print("WARN: digest item overflows two lines:", text[:60],
              file=sys.stderr)
    return y + 29


BULLETIN = [
    ("WORLD", "Zaporizhzhia: overnight Russian strike kills 2, wounds 40 "
              "including 4 children, hits an apartment block."),
    ("WORLD", "Gaza: Israeli strikes kill Hamas security chief Naeem Abu "
              "Nahel and six others, including two police officers."),
    ("WORLD", "Gaza: earlier strikes kill at least three people, "
              "including a man working for UNRWA."),
    ("WORLD", "Iran: Vance and Rubio meet Qatar's PM separately at the "
              "White House; Tehran vows to confront the US naval blockade."),
    ("WORLD", "UK logs record Iranian attacks in the Strait of Hormuz."),
    ("WORLD", "Russia warns Estonia's moves are \u201con verge of "
              "triggering open war\u201d."),
    ("WORLD", "More than 700,000 Russian soldiers killed in the nearly "
              "five-year-old Ukraine war, a new analysis finds."),
    ("WORLD", "NATO chief Rutte: alliance will defend against threats "
              "in space after reports of a Russian nuclear-armed satellite."),
    ("WORLD", "Zelenskyy calls for NATO to admit Ukraine at the "
              "assembly in Berlin."),
    ("WORLD", "Seven countries back an EU push to limit Russian visas "
              "for tourists and sports."),
    ("WORLD", "Cyprus expels two Russian diplomats over spying claims."),
    ("WORLD", "Russian aircraft enter South Korea's air defence "
              "identification zone."),
    ("WORLD", "Germany first to access Ukraine's Delta combat system; "
              "preliminary deal on more interceptor missiles."),
    ("WORLD", "DR Congo: fighting near a hospital in Ituri traps Ebola "
              "responders for 24+ hours."),
    ("WORLD", "Somalia and Uganda to intensify operations against "
              "al-Shabaab as withdrawal begins."),
    ("US", "Democrats clinch 258 House seats, the largest majority "
           "since 1992; Hubbard beats Foxx by 330 votes."),
    ("US", "Trump to sign a directive expediting federal death "
           "sentences."),
    ("US", "Pentagon accuses Canada of falling short as a credible "
           "partner in defending North America."),
    ("US", "Oregon and Virginia sue SpaceX over alleged Grok-generated "
           "child abuse images."),
    ("US", "US seeks seizure of $1.1bn+ in crypto linked to North "
           "Korean hackers."),
    ("TECH", "US blacklists Singapore cloud firm Megaspeed over Nvidia "
             "chip diversion to China."),
    ("TECH", "Arm extends CEO Rene Haas's tenure to 2033 amid Nvidia "
             "speculation."),
    ("TECH", "South Korea offers up to $375,000 rewards to catch AI "
             "cheating in the college entrance exam."),
    ("TECH", "US intelligence chief says China probably got limited "
             "access to AI chips."),
    ("ASIA", "Indonesia factory fire toll rises to 26; eight still "
            "missing after the Serang candy-plant blaze."),
    ("SPORT", "Champions League: Real Madrid 5\u20131 PSV in a comeback; "
              "Arsenal 1\u20131 Dortmund; Man City 2\u20132 Napoli."),
    ("WORLD", "Iraq's PM orders the oil ministry to manage oilfields "
              "in Kurdish-held areas."),
    ("WORLD", "Sudan: RSF defectors join the army in Khartoum; UN "
              "condemns strikes on the capital blamed on Ethiopia."),
    ("WORLD", "Denmark: bomb threats reported at schools across the "
              "country."),
    ("WORLD", "EU puts Rinaldo Nazzaro, founder of \u201cThe Base\u201d, "
              "on its sanctions list."),
]

TICKER = [
    "Dow closes above 50,000 for the first time \u2014 50,018.70",
    "Consumer confidence jumps to 103.3, smashing the 92.2 forecast",
    "Gold \u22122.7% to $3,552.80  ·  Oil +1.8% to $81.63",
    "Anthropic drops below its IPO price as AI shares slide",
    "COP32 heads to Addis Ababa in 2027 after the Antalya flop",
    "Huang faces House committees on 1 Dec, the Senate on 3 Dec",
]


def ticker_band(drw, top):
    """Dark footer band with the six ticker items on three lines.

    Two items per line at 12pt measure ~780px, comfortably inside the
    968px inner width — the earlier two-row layout overflowed both
    edges, so the ticker now gets three rows instead.
    """
    tickf = font(SANS, 12)
    rows = (TICKER[0:2], TICKER[2:4], TICKER[4:6])
    drw.rectangle([EDGE, top, PAGE - EDGE, top + 58], fill=BAND)
    for row, items in enumerate(rows):
        line = "   \u2022   ".join(items)
        drw.text((PAGE // 2, top + 8 + row * 16), line, font=tickf,
                 fill=(235, 232, 222), anchor="ma")


def build():
    img = Image.new("RGB", (PAGE, PAGE), PAPER)
    drw = ImageDraw.Draw(img)
    drw.rectangle([10, 10, PAGE - 11, PAGE - 11], outline=RULE, width=1)
    nameplate(drw)
    y = lead_story(drw, 142)
    y += 12
    hline(drw, EDGE, PAGE - EDGE, y, RULE, 1)
    y += 12
    colw = (INNER - 20) // 2
    left = second_story(
        drw, EDGE, y, colw, "CLIMATE", FOREST,
        "COP31 autopsy: the deal that died in Antalya",
        "The first COP since Copenhagen 2009 to end without a deal. "
        "Ninety-plus nations signed an electrification pledge, a "
        "just-transition package was agreed, and only $142m in new "
        "funding appeared. The focus now shifts to COP32 in Addis Ababa.")
    right = second_story(
        drw, EDGE + colw + 20, y, colw, "WORLD  ·  UKRAINE", CRIMSON,
        "Kyiv's war at sea reaches Libya's shores",
        "The UN mission in Libya wants an independent probe into the "
        "Benghazi port attacks; Zelenskyy says Ukrainian naval drones "
        "sank the Russian warship Mercury. Russia's 2026 troop losses "
        "hit a record 432,000.")
    y = max(left, right) + 10
    hline(drw, EDGE, PAGE - EDGE, y, RULE, 1)
    y += 10
    secf = font(SANSB, 15)
    drw.text((EDGE, y), "THE DAY IN BRIEF", font=secf, fill=INK)
    drw.text((PAGE - EDGE, y), "30 STORIES", font=secf, fill=SOFT,
             anchor="ra")
    y += 24
    colw = (INNER - 20) // 2
    half = (len(BULLETIN) + 1) // 2
    row_y = y
    for i, (tag, text) in enumerate(BULLETIN):
        col = i // half
        row = i % half
        ix = EDGE + col * (colw + 20)
        iy = row_y + row * 29
        digest_item(drw, ix, iy, colw, tag, text)
    y = row_y + half * 29 + 8
    ticker_band(drw, y)
    return img


def main():
    img = build()
    img.save("entry.png", format="PNG", optimize=True)
    print("wrote entry.png")


if __name__ == "__main__":
    main()
