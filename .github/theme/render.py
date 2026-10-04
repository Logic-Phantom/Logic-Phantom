"""Render README.md from today's layout + colour theme (both rotate daily, KST).

    python .github/theme/render.py                                  # today's rotation
    python .github/theme/render.py --theme dracula --layout terminal  # force (or THEME= / LAYOUT= env)
    python .github/theme/render.py --list 30                        # preview the schedule, writes nothing

Content lives in profile.json, colours in themes.json, structure in layouts/*.md.
Layouts use {{block}} or {{block:arg:arg}} tokens — see BLOCKS below.
Also writes current.json, which snake.yml reads to colour the contribution snake.
"""

import argparse
import json
import os
import random
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote, quote_plus

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
THEMES = json.loads((HERE / "themes.json").read_text(encoding="utf-8"))
PROFILE = json.loads((HERE / "profile.json").read_text(encoding="utf-8"))
LAYOUTS = sorted(p.stem for p in (HERE / "layouts").glob("*.md"))

KST = timezone(timedelta(hours=9))
EPOCH = datetime(1970, 1, 1).date()
# Empty-cell colours match GitHub's own page backgrounds so the grid blends in.
EMPTY_DOT = {"dark": "#161b22", "light": "#ebedf0"}
CARDS_URL = f"https://raw.githubusercontent.com/{PROFILE['username']}/{PROFILE['username']}/main/profile-summary-card-output"
SNAKE_URL = f"https://raw.githubusercontent.com/{PROFILE['username']}/{PROFILE['username']}/output"
DOCS_URL = f"https://github.com/{PROFILE['username']}/{PROFILE['username']}/tree/main/.github/theme"
CARD_ALTS = {
    "0-profile-details": "Profile details and contributions over the last year",
    "1-repos-per-language": "Top languages by repository",
    "2-most-commit-language": "Top languages by commit",
    "3-stats": "GitHub stats",
    "4-productive-time": "Most productive time of day",
}
HERO_SHAPES = {"waving", "slice", "soft", "cylinder", "shark", "rounded", "egg"}


# ---------------------------------------------------------------- rotation

def pick(items, day, salt):
    """Every item appears once per cycle in a fresh order; never the same item two days in a row."""
    n = len(items)
    cycle, pos = divmod(day, n)

    def order_for(c):
        order = list(range(n))
        random.Random(f"{salt}:{c}").shuffle(order)
        return order

    order = order_for(cycle)
    if n > 2 and order[0] == order_for(cycle - 1)[-1]:
        order[0], order[1] = order[1], order[0]
    return items[order[pos]]


def theme_for_day(day):
    return pick(THEMES, day, "theme")


def layout_for_day(day):
    return pick(LAYOUTS, day, "layout")


# ---------------------------------------------------------------- blocks

def md_inline_to_html(text):
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


def luminance(hex_color):
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


class Blocks:
    def __init__(self, theme, date):
        self.t = theme
        self.date = date
        stops = theme["gradient"]
        self.gradient = ",".join(f"{round(i / (len(stops) - 1) * 100)}:{c}" for i, c in enumerate(stops))

    def _capsule(self, kind, height, section, extra=""):
        return (
            f'<img src="https://capsule-render.vercel.app/api?type={kind}&color={self.gradient}'
            f'&height={height}&section={section}{extra}" width="100%" alt="" />'
        )

    # -- decoration
    def banner_header(self):
        b = self.t["banner"]
        return self._capsule(b["type"], b["height"], "header") if b["type"] != "none" else ""

    def banner_footer(self):
        b = self.t["banner"]
        return self._capsule(b["type"], b["height"], "footer") if b["type"] != "none" else ""

    def _hero_shape(self):
        kind = self.t["banner"]["type"]
        return kind if kind in HERO_SHAPES else "waving"

    def hero(self):
        mid = self.t["gradient"][len(self.t["gradient"]) // 2]
        font_color = "1f2328" if luminance(mid) > 0.6 else "ffffff"
        extra = (
            f"&text={quote(PROFILE['displayName'])}&fontSize=56&fontColor={font_color}&fontAlignY=36"
            f"&desc={quote(PROFILE['heroDesc'])}&descSize=18&descAlignY=56&animation=fadeIn"
        )
        return self._capsule(self._hero_shape(), 200, "header", extra)

    def hero_footer(self):
        return self._capsule(self._hero_shape(), 100, "footer")

    def divider(self, section="header"):
        return self._capsule("rect", 3, section)

    # -- header
    def typing(self):
        lines = ";".join(quote_plus(line) for line in PROFILE["typingLines"])

        def url(color):
            return (
                f"https://readme-typing-svg.demolab.com?font={quote_plus(self.t['font'])}&weight=700"
                f"&size={self.t['fontSize']}&duration=2800&pause=900&color={color}"
                f"&center=true&vCenter=true&width=760&height=70&lines={lines}"
            )

        dark, light = url(self.t["accent"]["dark"]), url(self.t["accent"]["light"])
        return (
            "<picture>\n"
            f'  <source media="(prefers-color-scheme: dark)" srcset="{dark}" />\n'
            f'  <source media="(prefers-color-scheme: light)" srcset="{light}" />\n'
            f'  <img src="{dark}" alt="{PROFILE["displayName"]}" />\n'
            "</picture>"
        )

    def badges(self, style="for-the-badge"):
        out = []
        for b in PROFILE["badges"]:
            color = self.t["badge"] if b["color"] == "accent" else b["color"]
            logo = f"&logo={b['logo']}&logoColor=white" if b.get("logo") else ""
            out.append(f'  <img src="https://img.shields.io/badge/{b["label"]}-{color}?style={style}{logo}" alt="{b["alt"]}" />')
        out.append(
            f'  <img src="https://komarev.com/ghpvc/?username={PROFILE["username"]}&style={style}'
            f'&color={self.t["badge"]}&label=PROFILE+VIEWS" alt="Profile views" />'
        )
        return "<p>\n" + "\n".join(out) + "\n</p>"

    # -- about
    def quote(self):
        return f'> **"{PROFILE["quote"]}"**'

    def about_list(self):
        return "\n".join(f"- {a['icon']} &nbsp;{a['text']}" for a in PROFILE["about"])

    def about_html(self):
        items = "\n".join(f"  <li>{a['icon']} {md_inline_to_html(a['text'])}</li>" for a in PROFILE["about"])
        return f"<ul>\n{items}\n</ul>"

    def about_code(self):
        def js(v):
            if isinstance(v, list):
                return "[" + ", ".join(js(x) for x in v) + "]"
            return json.dumps(v, ensure_ascii=False)

        w = PROFILE["whoami"]
        body = "\n".join(f"  {k}: {js(v)}," for k, v in w["fields"].items())
        return f"```ts\nconst {w['var']} = {{\n{body}\n}};\n```"

    # -- stack
    def _icons(self, icons, perline=None):
        per = f"&perline={perline}" if perline else ""
        return f"https://skillicons.dev/icons?i={','.join(icons)}&theme={self.t['icons']}{per}"

    def stack_table(self):
        rows = []
        for i, g in enumerate(PROFILE["stack"]):
            width = ' width="150"' if i == 0 else ""
            rows.append(
                f"  <tr>\n    <td{width}><b>{g['label']}</b></td>\n"
                f'    <td><img src="{self._icons(g["icons"])}" alt="{g["alt"]}" /></td>\n  </tr>'
            )
        return "<table>\n" + "\n".join(rows) + "\n</table>"

    def stack_row(self, perline="12"):
        icons = [i for g in PROFILE["stack"] for i in g["icons"]]
        alt = ", ".join(g["alt"] for g in PROFILE["stack"])
        return f'<img src="{self._icons(icons, perline)}" alt="{alt}" />'

    # -- stats
    def card(self, name, width="345"):
        dark = f"{CARDS_URL}/{self.t['cards']['dark']}/{name}.svg"
        light = f"{CARDS_URL}/{self.t['cards']['light']}/{name}.svg"
        return (
            "<picture>\n"
            f'  <source media="(prefers-color-scheme: dark)" srcset="{dark}" />\n'
            f'  <source media="(prefers-color-scheme: light)" srcset="{light}" />\n'
            f'  <img src="{dark}" alt="{CARD_ALTS[name]}" width="{width}" />\n'
            "</picture>"
        )

    def cards_credit(self):
        return (
            '<sub>Cards are generated daily by <a href="https://github.com/vn7n24fzkq/github-profile-summary-cards">'
            "github-profile-summary-cards</a> and served from this repository — no third-party uptime required.</sub>"
        )

    def snake(self):
        return (
            "<picture>\n"
            f'  <source media="(prefers-color-scheme: dark)" srcset="{SNAKE_URL}/github-snake-dark.svg" />\n'
            f'  <source media="(prefers-color-scheme: light)" srcset="{SNAKE_URL}/github-snake.svg" />\n'
            f'  <img src="{SNAKE_URL}/github-snake.svg" alt="Contribution snake animation" width="100%" />\n'
            "</picture>"
        )

    # -- outro
    def connect(self, style="for-the-badge"):
        return "\n".join(
            f'<a href="{l["href"]}"><img src="https://img.shields.io/badge/{l["label"]}-{l["color"]}'
            f'?style={style}&logo={l["logo"]}&logoColor=white" alt="{l["alt"]}" /></a>'
            for l in PROFILE["links"]
        )

    def footer(self):
        return (
            f'<sub>💬 <i>"{PROFILE["footerQuote"]}"</i></sub>\n<br />\n'
            f"<sub>🎨 Today's look · <b>{self.t['name']}</b> — "
            f'<a href="{DOCS_URL}">refreshed daily at 12:00 KST</a></sub>'
        )

    # -- scalars
    def e(self, key):
        return self.t["emoji"][key]

    def theme_name(self):
        return self.t["name"]


BLOCKS = {name for name in dir(Blocks) if not name.startswith("_")}


def render(template, blocks):
    def sub(match):
        name, *args = match.group(1).split(":")
        if name not in BLOCKS:
            raise KeyError(f"Unknown layout token {{{{{match.group(1)}}}}}")
        return str(getattr(blocks, name)(*args))

    out = re.sub(r"\{\{([\w:%.-]+)\}\}", sub, template)
    # Empty optional blocks (e.g. no banner) shouldn't leave stacks of blank lines behind.
    return re.sub(r"\n{3,}", "\n\n", out).strip() + "\n"


def snake_outputs(theme):
    def out(filename, mode, extra=""):
        palette = theme["snake"][mode]
        dots = ",".join([EMPTY_DOT[mode], *palette["dots"]])
        return f"dist/{filename}?{extra}color_snake={palette['color']}&color_dots={dots}"

    return [out("github-snake.svg", "light"), out("github-snake-dark.svg", "dark", "palette=github-dark&")]


# ---------------------------------------------------------------- main

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--theme", default=os.environ.get("THEME") or None)
    parser.add_argument("--layout", default=os.environ.get("LAYOUT") or None)
    parser.add_argument("--list", type=int, nargs="?", const=len(THEMES), metavar="DAYS")
    args = parser.parse_args()

    today = datetime.now(KST).date()
    day = (today - EPOCH).days

    if args.list:
        for d in range(day, day + args.list):
            print(f"{EPOCH + timedelta(days=d)}  {layout_for_day(d):<10} {theme_for_day(d)['id']}")
        return

    theme = theme_for_day(day)
    if args.theme:
        theme = next((t for t in THEMES if t["id"] == args.theme), None)
        if theme is None:
            sys.exit(f'Unknown theme "{args.theme}". Available: {", ".join(t["id"] for t in THEMES)}')
    layout = args.layout or layout_for_day(day)
    if layout not in LAYOUTS:
        sys.exit(f'Unknown layout "{layout}". Available: {", ".join(LAYOUTS)}')

    date = today.isoformat()
    template = (HERE / "layouts" / f"{layout}.md").read_text(encoding="utf-8")
    header = (
        f"<!-- ⚠️ AUTO-GENERATED by .github/theme/render.py — edit .github/theme/ instead. "
        f"Layout: {layout} · Theme: {theme['id']} · {date} -->\n"
    )
    readme = header + render(template, Blocks(theme, date))
    # newline="\n" keeps LF endings on Windows too, so local runs don't churn the diff.
    (ROOT / "README.md").write_text(readme, encoding="utf-8", newline="\n")
    current = {
        "id": theme["id"],
        "name": theme["name"],
        "layout": layout,
        "date": date,
        "snakeOutputs": snake_outputs(theme),
    }
    (HERE / "current.json").write_text(
        json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"Applied: layout={layout} theme={theme['name']} ({theme['id']}) for {date}")


if __name__ == "__main__":
    main()
