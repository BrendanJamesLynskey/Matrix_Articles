"""Assembles the two slide decks from the shared house head plus a body file.

The head/style block is the one already used across the MML, Linear Algebra and
Wilmott deck repos, so the new decks drop straight into the existing set. Only
the accent triple and the title change per deck.
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STYLE = open(os.path.join(HERE, "_house_style.css.html"), encoding="utf-8").read()

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>__TITLE__</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js" onload="renderMathInElement(document.body,{delimiters:[{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}]})"></script>
__STYLE__
</head>
<body>
"""

FOOT = """
<div class="footer">
    <p>__FOOTER__</p>
    <p style="margin-top:.6rem">Single-page HTML &middot; KaTeX-rendered maths &middot; no build step.
    <a href="https://github.com/BrendanJamesLynskey/__REPO__">Source on GitHub</a>
    &middot; <a href="__REPO__.pdf">long-form PDF</a></p>
</div>

</body>
</html>
"""

# Extra components these two decks need on top of the shared system.
EXTRA_CSS = """
        .plane-grid{display:grid;grid-template-columns:1fr 1fr;gap:.75rem}
        @media (max-width:640px){.plane-grid{grid-template-columns:1fr}}
        .legend{display:flex;flex-wrap:wrap;gap:1rem;justify-content:center;margin-top:.6rem;font-family:var(--font-mono);font-size:.72rem;color:var(--text-secondary)}
        .legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:.35rem;vertical-align:middle}
        .verdict{font-family:var(--font-mono);font-size:.8rem;padding:.35rem .7rem;border-radius:4px;display:inline-block;margin-top:.5rem}
        .verdict.ok{color:var(--accent-4);border:1px solid var(--accent-4);background:rgba(111,187,169,.12)}
        .verdict.bad{color:var(--accent-2);border:1px solid var(--accent-2);background:rgba(215,141,164,.12)}
        .canvas-wrap canvas{image-rendering:auto}
        .metric-label .katex,.callout-label .katex,.series-label .katex,
        .metric-label .katex *,.callout-label .katex *{text-transform:none}
        .note{font-size:.85rem;color:var(--text-secondary);font-style:italic;margin-top:.5rem}
"""


def build(body_file, out_file, title, footer, repo, accents):
    style = STYLE
    for k, v in accents.items():
        style = style.replace(k, v)
    style = style.replace("    </style>", EXTRA_CSS + "    </style>")
    body = open(os.path.join(HERE, body_file), encoding="utf-8").read()
    head = HEAD.replace("__TITLE__", title).replace("__STYLE__", style)
    foot = FOOT.replace("__FOOTER__", footer).replace("__REPO__", repo)
    html = head + body + foot
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as fh:
        fh.write(html)
    n = len(re.findall(r'<section class="slide"', html))
    print("wrote %s  (%d slides, %d KB)" % (out_file, n, len(html) // 1024))


ROOT = "/home/brendan/Claude_sandbox"

def build_all():
    build("deck_network_body.html",
          os.path.join(ROOT, "Matrix_Methods_Network_Parameters", "index.html"),
          "Matrix Methods &mdash; Network Parameters (S, Z, Y)",
          "Deck 01 of the Matrix Methods in Engineering series. Companions: "
          "<a href=\"https://brendanjameslynskey.github.io/Matrix_Concepts_Digital_Filters/\">"
          "Digital Filter Design</a> and "
          "<a href=\"https://brendanjameslynskey.github.io/SerDes_Equalisation/\">"
          "Equalisation in High-Speed Serial Links</a>.",
          "Matrix_Methods_Network_Parameters",
          {"#a896c7": "#95c7db", "rgba(168,150,199,.25)": "rgba(149,199,219,.25)"})

    build("deck_filters_body.html",
          os.path.join(ROOT, "Matrix_Concepts_Digital_Filters", "index.html"),
          "Matrix Concepts &mdash; Digital Filter Design",
          "Deck 02 of the Matrix Methods in Engineering series. Companions: "
          "<a href=\"https://brendanjameslynskey.github.io/Matrix_Methods_Network_Parameters/\">"
          "Network Parameters (S, Z, Y)</a> and "
          "<a href=\"https://brendanjameslynskey.github.io/SerDes_Equalisation/\">"
          "Equalisation in High-Speed Serial Links</a>.",
          "Matrix_Concepts_Digital_Filters",
          {"#a896c7": "#6fbba9", "rgba(168,150,199,.25)": "rgba(111,187,169,.25)"})

    build("deck_serdes_body.html",
          os.path.join(ROOT, "SerDes_Equalisation", "index.html"),
          "Equalisation in High-Speed Serial Links",
          "Deck 03 of the Matrix Methods in Engineering series. Companions: "
          "<a href=\"https://brendanjameslynskey.github.io/Matrix_Methods_Network_Parameters/\">"
          "Network Parameters (S, Z, Y)</a> and "
          "<a href=\"https://brendanjameslynskey.github.io/Matrix_Concepts_Digital_Filters/\">"
          "Digital Filter Design</a>.",
          "SerDes_Equalisation",
          {"#a896c7": "#d88954", "rgba(168,150,199,.25)": "rgba(216,137,84,.25)"})


if __name__ == "__main__":
    build_all()
