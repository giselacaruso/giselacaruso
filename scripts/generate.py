#!/usr/bin/env python3
"""Genera los SVG del README de perfil.

    python scripts/generate.py static          -> assets/ (hero, redes, stack, casos)
    python scripts/generate.py dynamic out/    -> out/ (repos destacados y actividad; pide GITHUB_TOKEN)

Sin dependencias: sólo la librería estándar de Python.
Cada pieza sale en dos versiones, -light y -dark, para el <picture> del README.
"""
import base64, json, os, sys, urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
USER = os.environ.get("PROFILE_USER", "giselacaruso")

# Repos que aparecen como tarjeta. "desc" pisa la descripción de GitHub si querés otra.
FEATURED = [
    {"repo": "atelier-de-norma",
     "desc": "A ceramics shop for my aunt Norma, 70 and computer-free: customers order over WhatsApp and she uploads her pieces with a photo."},
    {"repo": "christmas-time",
     "desc": "An interactive 3D snow globe: travel through Christmas in cities around the world, with their weather and coordinates. Built with React Three Fiber."},
]

THEMES = {
    "dark": {
        "bg": "#141413", "card": "#1a1a19", "fg": "#F3E7DA", "soft": "#8a8a85",
        "line": "#2b2b28", "chip": "#1f1f1d",
        "heat": ["#232321", "#4a2419", "#82321f", "#e04a2f", "#f59356"],
    },
    "light": {
        "bg": "#F3E7DA", "card": "#F8F1E9", "fg": "#181816", "soft": "#7a746c",
        "line": "#e2d3c2", "chip": "#efe3d5",
        "heat": ["#eadccb", "#f6c9a6", "#f59356", "#ea6a40", "#c93a22"],
    },
}
G1, G2 = "#e04a2f", "#f59356"


def b64(path):
    return base64.b64encode(Path(path).read_bytes()).decode()


SANS = b64(HERE / "fonts/FamiljenGrotesk.woff2")
MONO = b64(HERE / "fonts/JetBrainsMono.woff2")


def fonts(mono=True):
    css = ("@font-face{font-family:F;src:url(data:font/woff2;base64,%s) format('woff2');"
           "font-weight:400 700}" % SANS)
    if mono:
        css += ("@font-face{font-family:M;src:url(data:font/woff2;base64,%s) format('woff2')}" % MONO)
    css += (".s{font-family:F,'Helvetica Neue',Arial,sans-serif}"
            ".m{font-family:M,ui-monospace,Menlo,monospace;letter-spacing:.08em}")
    return css


def tw(text, size, mono=False):
    """Ancho aproximado de un texto; alcanza para dimensionar pills y cortar líneas."""
    if mono:
        return len(text) * size * 0.6 * 1.08
    narrow = sum(1 for c in text if c in "iljtf.,:;'!| ")
    wide = sum(1 for c in text if c in "mwMW@")
    return size * (0.53 * len(text) - 0.25 * narrow + 0.3 * wide)


def wrap(text, size, width):
    lines, cur = [], ""
    for word in text.split():
        cand = (cur + " " + word).strip()
        if tw(cand, size) > width and cur:
            lines.append(cur)
            cur = word
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


def svg(w, h, body, style, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
            f'<style>{style}</style>{body}</svg>\n')


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"  {path.relative_to(path.parents[1])}  {len(text) // 1024} KB")


# ---------------------------------------------------------------- hero

def hero(t):
    W, H = 1200, 440
    style = fonts() + (
        ".blob{animation:drift 16s ease-in-out infinite alternate;transform-origin:960px 220px}"
        ".b2{animation-duration:21s;animation-direction:alternate-reverse}"
        "@keyframes drift{0%{transform:translate(0,0) scale(1)}100%{transform:translate(-60px,30px) scale(1.12)}}"
        "@media (prefers-reduced-motion:reduce){.blob{animation:none}}")
    body = f'''
<defs>
  <clipPath id="c"><rect width="{W}" height="{H}" rx="24"/></clipPath>
  <filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="70"/></filter>
  <linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="{G1}"/><stop offset="1" stop-color="{G2}"/></linearGradient>
</defs>
<g clip-path="url(#c)">
  <rect width="{W}" height="{H}" fill="{t['bg']}"/>
  <g filter="url(#blur)" opacity=".95">
    <circle class="blob" cx="990" cy="250" r="170" fill="{G1}"/>
    <circle class="blob b2" cx="1090" cy="130" r="120" fill="{G2}"/>
    <circle class="blob" cx="860" cy="390" r="90" fill="{G2}" opacity=".7"/>
  </g>
</g>
<text class="m" x="56" y="70" font-size="13" fill="{t['soft']}">GISELA CARUSO</text>
<text class="m" x="56" y="92" font-size="13" fill="{t['soft']}">BUENOS AIRES · REMOTE</text>
<text class="s" x="52" y="210" font-size="72" letter-spacing="-2.2" fill="{t['fg']}">Make it make sense.</text>
<text class="s" x="52" y="290" font-size="72" letter-spacing="-2.2" fill="url(#g)">Then make it work.</text>
<line x1="56" x2="560" y1="342" y2="342" stroke="{t['line']}"/>
<text class="s" x="56" y="380" font-size="22" fill="{t['fg']}">Senior Product Designer &amp; Builder</text>
<text class="m" x="56" y="408" font-size="12.5" fill="{t['soft']}">15 YEARS · FRAMER EXPERT · DESIGN → CODE</text>'''
    return svg(W, H, body, style, "Gisela Caruso — Senior Product Designer & Builder. Make it make sense. Then make it work.")


# ---------------------------------------------------------------- redes

ICONS = {
    "web": '<g fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="12" r="9.5"/><ellipse cx="12" cy="12" rx="4" ry="9.5"/><path d="M2.5 12h19"/></g>',
    "linkedin": '<path fill="currentColor" d="M20.45 20.45h-3.55v-5.57c0-1.33-.03-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28zM5.34 7.43a2.06 2.06 0 1 1 0-4.13 2.06 2.06 0 0 1 0 4.13zm1.78 13.02H3.56V9h3.56v11.45zM22.23 0H1.77C.79 0 0 .77 0 1.73v20.54C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.73V1.73C24 .77 23.2 0 22.22 0z"/>',
    "x": '<path fill="currentColor" d="M18.24 2.25h3.31l-7.23 8.26 8.5 11.24h-6.65l-5.21-6.82-5.97 6.82H1.68l7.73-8.84L1.25 2.25h6.83l4.71 6.23zm-1.16 17.52h1.83L7.08 4.13H5.12z"/>',
    "instagram": '<g fill="none" stroke="currentColor" stroke-width="1.7"><rect x="2.5" y="2.5" width="19" height="19" rx="5.5"/><circle cx="12" cy="12" r="4.3"/></g><circle cx="17.6" cy="6.4" r="1.2" fill="currentColor"/>',
    "framer": '<path fill="currentColor" d="M5 1h14v7.33h-7zM5 8.33h7l7 7.34H5zM5 15.67h7V23z"/>',
    "contra": '<g fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9.5"/><path d="M9 15l6-6M10 9h5v5"/></g>',
    "email": '<g fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"><rect x="2.5" y="4.5" width="19" height="15" rx="2.5"/><path d="M3 6l9 7 9-7"/></g>',
}
SOCIAL = [("web", "giselacaruso.com"), ("linkedin", "LinkedIn"), ("framer", "Framer Expert"),
          ("contra", "Contra"), ("x", "X"), ("instagram", "Instagram"), ("email", "Email")]


def pill(t, icon, label):
    H, size = 44, 15
    w = round(16 + 18 + 10 + tw(label, size) + 20)
    body = (f'<rect x=".5" y=".5" width="{w - 1}" height="{H - 1}" rx="{H / 2 - .5}" fill="{t["card"]}" stroke="{t["line"]}"/>'
            f'<svg x="16" y="13" width="18" height="18" viewBox="0 0 24 24" color="{t["fg"]}">{ICONS[icon]}</svg>'
            f'<text class="s" x="44" y="27.5" font-size="{size}" fill="{t["fg"]}">{escape(label)}</text>')
    return svg(w, H, body, fonts(mono=False), label)


# ---------------------------------------------------------------- stack

STACK = [
    ("DESIGN", ["Figma", "Framer", "Illustrator", "Photoshop", "Lettering"]),
    ("BUILD", ["React", "TypeScript", "Tailwind CSS", "Supabase", "Vercel"]),
    ("WEB & COMMERCE", ["WordPress", "Elementor", "WooCommerce", "Webflow"]),
    ("AI", ["Claude Code", "MCP", "Agentic workflows", "Midjourney"]),
]


def stack(t):
    W, row, size, x0 = 1200, 60, 16, 240
    H = 40 + row * len(STACK)
    parts = []
    for i, (label, items) in enumerate(STACK):
        y = 32 + i * row
        if i:
            parts.append(f'<line x1="32" x2="{W - 32}" y1="{y - 10}" y2="{y - 10}" stroke="{t["line"]}"/>')
        parts.append(f'<text class="m" x="36" y="{y + 25}" font-size="12" fill="{t["soft"]}">{escape(label)}</text>')
        x = x0
        for item in items:
            w = round(tw(item, size) + 36)
            parts.append(f'<rect x="{x}" y="{y + 2}" width="{w}" height="36" rx="18" fill="{t["chip"]}" stroke="{t["line"]}"/>'
                         f'<text class="s" x="{x + w / 2}" y="{y + 25.5}" font-size="{size}" text-anchor="middle" fill="{t["fg"]}">{escape(item)}</text>')
            x += w + 8
    body = f'<rect width="{W}" height="{H}" rx="24" fill="{t["bg"]}"/>' + "".join(parts)
    label = "Toolkit: " + "; ".join(f"{a}: {', '.join(b)}" for a, b in STACK)
    return svg(W, H, body, fonts(), label)


# ---------------------------------------------------------------- casos

CASES = [
    ("guanabay", "Guana Bay", "E-COMMERCE · B2C + B2B", "One store, two ways to buy.", "WooCommerce"),
    ("mots", "Mots", "PLATFORM · CMS", "A new way to find the right space.", "WordPress"),
    ("akme", "Akmé", "WEB APP · OWN PRODUCT", "Your race, turned into a product.", "React · TypeScript · Supabase"),
    ("academia", "Academia Ajedrez 360°", "LEARNING · MEMBERSHIPS", "When WhatsApp was no longer enough.", "WordPress"),
]


def case(t, key, name, kind, claim, tech):
    W, H = 600, 300
    img = b64(HERE / f"covers/cover-{key}.webp")
    name_size = 34 if tw(name, 34) < 260 else 26
    lines = wrap(claim, 19, 250)
    claim_svg = "".join(f'<text class="s" x="32" y="{150 + i * 25}" font-size="19" fill="{t["soft"]}">{escape(l)}</text>'
                        for i, l in enumerate(lines))
    body = f'''
<defs><clipPath id="ci"><rect x="316" y="16" width="268" height="268" rx="14"/></clipPath>
<clipPath id="cc"><rect width="{W}" height="{H}" rx="22"/></clipPath></defs>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="22" fill="{t["card"]}" stroke="{t["line"]}"/>
<image href="data:image/webp;base64,{img}" x="316" y="16" width="268" height="268" preserveAspectRatio="xMidYMid slice" clip-path="url(#ci)"/>
<text class="m" x="32" y="52" font-size="11.5" fill="{t["soft"]}">{escape(kind)}</text>
<text class="s" x="30" y="108" font-size="{name_size}" letter-spacing="-.8" fill="{t["fg"]}">{escape(name)}</text>
{claim_svg}
<text class="m" x="32" y="246" font-size="11" fill="{t["soft"]}">{escape(tech.upper())}</text>
<text class="s" x="32" y="272" font-size="15" fill="{G1}">Read the case ↗</text>'''
    return svg(W, H, body, fonts(), f"{name} — {claim} Case study.")


# ---------------------------------------------------------------- dinámico

def gql(query, variables):
    token = os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request("https://api.github.com/graphql",
                                 data=json.dumps({"query": query, "variables": variables}).encode(),
                                 headers={"Authorization": f"bearer {token}", "User-Agent": "profile-readme"})
    data = json.load(urllib.request.urlopen(req))
    if "errors" in data:
        raise SystemExit(data["errors"])
    return data["data"]


QUERY = """
query($login:String!){ user(login:$login){
  followers{totalCount}
  repositories(first:100, ownerAffiliations:OWNER, privacy:PUBLIC, isFork:false){
    totalCount nodes{ name description homepageUrl stargazerCount primaryLanguage{name color} } }
  contributionsCollection{ contributionCalendar{ totalContributions
    weeks{ contributionDays{ date contributionCount contributionLevel } } } }
}}"""

LEVELS = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def activity(t, u):
    W = 1200
    cal = u["contributionsCollection"]["contributionCalendar"]
    repos = u["repositories"]
    days = [d["contributionCount"] for w in cal["weeks"] for d in w["contributionDays"]]
    streak = best = 0
    for n in days:
        streak = streak + 1 if n else 0
        best = max(best, streak)
    stats = [
        (cal["totalContributions"], "CONTRIBUTIONS · LAST 12 MONTHS"),
        (sum(1 for n in days if n), "ACTIVE DAYS"),
        (best, "LONGEST STREAK · DAYS"),
        (repos["totalCount"], "PUBLIC REPOS"),
    ]
    parts = []
    col = (W - 64) / 4
    for i, (n, label) in enumerate(stats):
        x = 40 + i * col
        parts.append(f'<text class="s" x="{x - 2}" y="92" font-size="52" letter-spacing="-1.5" fill="{t["fg"]}">{n:,}</text>'
                     f'<text class="m" x="{x}" y="122" font-size="11.5" fill="{t["soft"]}">{label}</text>')
    weeks = cal["weeks"][-53:]
    cell, gap = 17, 4
    x0 = (W - len(weeks) * (cell + gap) + gap) / 2
    y0 = 196
    last_month = None
    for wi, wk in enumerate(weeks):
        x = x0 + wi * (cell + gap)
        m = int(wk["contributionDays"][0]["date"][5:7])
        if m != last_month and wi < len(weeks) - 2:
            if last_month is not None or wk["contributionDays"][0]["date"][8:] <= "07":
                parts.append(f'<text class="m" x="{x}" y="{y0 - 14}" font-size="11" fill="{t["soft"]}">{MONTHS[m - 1].upper()}</text>')
            last_month = m
        for d in wk["contributionDays"]:
            wd = __import__("datetime").date.fromisoformat(d["date"]).isoweekday() % 7
            lvl = LEVELS.index(d["contributionLevel"])
            parts.append(f'<rect x="{x}" y="{y0 + wd * (cell + gap)}" width="{cell}" height="{cell}" rx="4" fill="{t["heat"][lvl]}">'
                         f'<title>{d["date"]}: {d["contributionCount"]}</title></rect>')
    ly = y0 + 7 * (cell + gap) + 22
    lx = W - x0 - 5 * (cell - 4 + gap)
    parts.append(f'<text class="m" x="{lx - 12}" y="{ly + 11}" font-size="11" text-anchor="end" fill="{t["soft"]}">LESS</text>')
    for i, c in enumerate(t["heat"]):
        parts.append(f'<rect x="{lx + i * (cell - 4 + gap)}" y="{ly}" width="{cell - 4}" height="{cell - 4}" rx="3" fill="{c}"/>')
    parts.append(f'<text class="m" x="{lx + 5 * (cell - 4 + gap) + 8}" y="{ly + 11}" font-size="11" fill="{t["soft"]}">MORE</text>')
    H = ly + 46
    body = (f'<rect width="{W}" height="{H}" rx="24" fill="{t["bg"]}"/>'
            f'<line x1="40" x2="{W - 40}" y1="150" y2="150" stroke="{t["line"]}"/>' + "".join(parts))
    label = f"GitHub activity for {USER}: " + ", ".join(f"{n} {l.lower()}" for n, l in stats)
    return svg(W, H, body, fonts(), label)


def repo_card(t, r, desc):
    W, H = 1200, 150
    lines = wrap(desc or "", 18, 760)[:2]
    lang = r.get("primaryLanguage") or {}
    home = (r.get("homepageUrl") or "").replace("https://", "").replace("http://", "").rstrip("/")
    parts = [f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="22" fill="{t["card"]}" stroke="{t["line"]}"/>',
             f'<text class="s" x="34" y="56" font-size="28" letter-spacing="-.6" fill="{t["fg"]}">{escape(r["name"])}</text>']
    for i, l in enumerate(lines):
        parts.append(f'<text class="s" x="34" y="{92 + i * 25}" font-size="18" fill="{t["soft"]}">{escape(l)}</text>')
    rx = 900
    if lang:
        parts.append(f'<circle cx="{rx + 6}" cy="51" r="6" fill="{lang["color"] or t["soft"]}"/>'
                     f'<text class="m" x="{rx + 20}" y="55" font-size="12" fill="{t["soft"]}">{escape(lang["name"].upper())}</text>')
    parts.append(f'<text class="m" x="{rx}" y="85" font-size="12" fill="{t["soft"]}">★ {r["stargazerCount"]}</text>')
    if home:
        parts.append(f'<text class="m" x="{rx}" y="115" font-size="12" fill="{G1}">{escape(home[:34])} ↗</text>')
    return svg(W, H, "".join(parts), fonts(), f"{r['name']}: {desc}")


# ---------------------------------------------------------------- main

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "static"
    if mode == "static":
        out = ROOT / "assets"
        for name, t in THEMES.items():
            write(out / f"hero-{name}.svg", hero(t))
            write(out / f"stack-{name}.svg", stack(t))
            for icon, label in SOCIAL:
                write(out / "social" / f"{icon}-{name}.svg", pill(t, icon, label))
            for c in CASES:
                write(out / "cases" / f"{c[0]}-{name}.svg", case(t, *c))
    elif mode == "dynamic":
        out = Path(sys.argv[2] if len(sys.argv) > 2 else "out").resolve()
        u = gql(QUERY, {"login": USER})["user"]
        by_name = {r["name"]: r for r in u["repositories"]["nodes"]}
        for name, t in THEMES.items():
            write(out / f"activity-{name}.svg", activity(t, u))
            for f in FEATURED:
                r = by_name.get(f["repo"])
                if r:
                    write(out / f"repo-{f['repo']}-{name}.svg", repo_card(t, r, f.get("desc") or r["description"]))
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
