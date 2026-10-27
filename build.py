"""Build the transcript site.

Usage: python3 build.py

TABS below lists each tab and the transcript files it is made from, in order;
several files in one tab are joined with continuous turn numbers. The script
writes index.html (all tabs) plus one standalone page per tab in transcripts/.

Three formats are understood:
  - '## User' / '## Claude' Markdown sections
  - Codex exports ('## User' / '## Assistant' / '## Activity'); each Activity
    block is shortened to its first line (the command), not its full output
  - Claude Code terminal exports ('❯' prompts)
"""
import html, os, re

root = os.path.dirname(os.path.abspath(__file__))

TABS = [
    ("venheilheim", "Venheilheim", "transcripts.html",
     [("transcript1.md", "Transcript 1"), ("transcripts_codex.md", "Codex"), ("transcript2.md", "Transcript 2")]),
    ("focusbank", "FocusBank", "transcript_focusbank.html",
     [("transcript_focusbank.md", None)]),
    ("lecture", "Lecture notes", "transcript_lecture.html",
     [("conversation_transcript.md", "Precursor (Antigravity)"), ("transript_lecture.md", "Claude Code")]),
    # No transcript yet: the tab carries only its interview-prep link.
    ("xg", "xG Companion", "transcript_xg.html", []),
]

# Interview-prep pages in prep/ (published copies of the study artifacts), linked from each tab.
PREP = {
    "venheilheim": [("The Venheilheim Build (interview course)", "venheilheim-build.html")],
    "focusbank": [("FocusBank Learning Lab (incl. interview prep)", "focusbank-learning-lab.html")],
    "lecture": [("Lecture Notes Field Guide (interview guide)", "lecture-notes-field-guide.html"),
                ("Lecture Notes Build Course", "lecture-notes-course.html")],
    "xg": [("xG Match Companion (interview prep course)", "xg-match-companion.html")],
}

# Personal details that must not appear on the public site.
REDACT = {"asaiyan195@gmail.com": "[email removed]"}


def tidy(text):
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def parse_sections(path):
    """'## User' followed by '## Claude' / '## Assistant' / '## Activity' / '## Completion' sections."""
    turns, role, buf = [], None, []

    def flush():
        nonlocal buf
        text = "\n".join(buf).strip()
        buf = []
        if not text:
            return
        if role == "User":
            turns.append([text, []])
            return
        if role == "Activity":
            first = text.split("\n", 1)[0].strip()
            text = "▸ " + first[:200]
            if turns and turns[-1][1] and turns[-1][1][-1].startswith("▸ "):
                turns[-1][1][-1] += "\n" + text
                return
        if not turns:
            turns.append(["(conversation start)", []])
        turns[-1][1].append(text)

    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        m = re.fullmatch(r"## (User|Claude|Assistant|Activity|Completion)", line)
        if m:
            flush()
            role = m.group(1)
        elif line.startswith("# Codex conversation") and role is None:
            continue
        else:
            buf.append(line)
    flush()
    return [(u, tidy("\n\n".join(r))) for u, r in turns]


def dedent(line):
    line = line.rstrip()
    return line[2:] if line.startswith("  ") else line


def parse_export(path):
    """Claude Code terminal /export: '❯' user prompts, everything else response."""
    lines = open(path, encoding="utf-8").read().split("\n")
    turns, i = [], 0
    # skip the Claude Code banner, then keep any response that comes before the first prompt
    while i < len(lines) and not lines[i].startswith(("❯ ", "● ")):
        i += 1
    pre = []
    while i < len(lines) and not lines[i].startswith("❯ "):
        pre.append(dedent(lines[i]))
        i += 1
    if "\n".join(pre).strip():
        turns.append(("(continued from an earlier conversation — no prompt in this export)", tidy("\n".join(pre))))
    while i < len(lines):
        user = [lines[i][2:].rstrip()]
        i += 1
        while i < len(lines) and lines[i].startswith("  ") and lines[i].strip():
            user.append(dedent(lines[i]))
            i += 1
        resp = []
        while i < len(lines) and not lines[i].startswith("❯ "):
            resp.append(dedent(lines[i]))
            i += 1
        turns.append(("\n".join(user).strip(), tidy("\n".join(resp))))
    return turns


def parse_antigravity(path):
    """Antigravity export: '### 👤 User' / '### 🤖 Assistant (…)' under '## Turn N:' headings."""
    turns, role, buf = [], None, []

    def flush():
        nonlocal buf
        text = "\n".join(l for l in buf if not l.startswith("> *Timestamp:*"))
        text = re.sub(r"\n---\s*$", "", text.strip()).strip()
        buf = []
        if role == "User":
            turns.append([text or "(empty message)", ""])
        elif role == "Assistant" and turns:
            turns[-1][1] = text

    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("### 👤 User") or line.startswith("### 🤖 Assistant"):
            flush()
            role = "User" if "👤" in line else "Assistant"
        elif re.match(r"## Turn \d+", line):
            flush()
            role = None
        elif role:
            buf.append(line)
    flush()
    return [(u, tidy(r)) for u, r in turns]


def parse(path):
    text = open(path, encoding="utf-8").read()
    if "### 👤 User" in text:
        return parse_antigravity(path)
    if re.search(r"^## (User|Claude|Assistant)$", text, re.M):
        return parse_sections(path)
    return parse_export(path)


def preview(resp):
    for line in resp.split("\n"):
        line = line.lstrip("●▸ ").strip()
        if line and not re.match(r"(Read|Ran|Listed|Searched) \d", line):
            return line[:110] + ("…" if len(line) > 110 else "")
    return ""


def render_tab(tid, title, parts):
    items, n, total = [], 0, 0
    for fname, label in parts:
        turns = parse(f"{root}/transcripts/{fname}")
        if label:
            items.append(f'<h3 class="part">{label} <span class="count">turns {n + 1}–{n + len(turns)}</span></h3>')
        for u, r in turns:
            n += 1
            for k, v in REDACT.items():
                u, r = u.replace(k, v), r.replace(k, v)
            items.append(
                f'<article class="turn" id="{tid}-{n}"><header><a class="num" href="#{tid}-{n}">Turn {n}</a></header>'
                f'<div class="user">{html.escape(u)}</div>'
                f'<details><summary>Response <span class="len">{len(r.split()):,} words</span>'
                f'<span class="pv">{html.escape(preview(r))}</span></summary>'
                f'<div class="resp">{html.escape(r) or "<em>(no text response)</em>"}</div></details></article>'
            )
        print(f"{title}: {fname} {len(turns)} turns")
    prep = "".join(f'<a href="PREP/{href}">{html.escape(label)} →</a>' for label, href in PREP.get(tid, []))
    prep = f'<nav class="prep"><span>Interview prep</span>{prep}</nav>' if prep else ""
    if not parts:
        items.append('<p class="none">No conversation transcript has been added for this project yet.</p>')
    count = f'<span class="count">{n} turns</span>' if parts else ""
    return (f'<section class="transcript" id="{tid}"><h2>{title} {count}</h2>'
            f'{prep}{"".join(items)}</section>')


# Each tab wears the theme of its project's own website.
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700'
         '&family=Figtree:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,600;9..144,700'
         '&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500'
         '&family=Barlow+Condensed:wght@600;700&family=Atkinson+Hyperlegible:wght@400;700&display=swap" rel="stylesheet">')

STYLE = """
@font-face{font-family:"Cinzel";src:url("FONTS/Cinzel.woff2") format("woff2");font-weight:400 900;font-display:swap}
@font-face{font-family:"IM Fell English";src:url("FONTS/IMFellEnglish-Regular.woff2") format("woff2");font-display:swap}
@font-face{font-family:"IM Fell English";src:url("FONTS/IMFellEnglish-Italic.woff2") format("woff2");font-style:italic;font-display:swap}
:root{--sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;--mono:ui-monospace,"SFMono-Regular",Menlo,Consolas,monospace;
  --display:var(--sans);--body:var(--sans);--radius:10px;--user-text:var(--text);--accent-ink:#fff;
  --bg:#f6f5f1;--card:#fff;--text:#1d1d1b;--muted:#6b6a65;--line:#e3e1da;--accent:#9a5b13;--user:#fbf6ec;--resp:#fafaf8}
/* Venheilheim: the game site's night sky and gold, period fonts, prompts on parchment (dark only, like the site) */
html[data-tab="venheilheim"]{--display:"Cinzel","Trajan Pro",Georgia,serif;--body:"IM Fell English",Georgia,serif;
  --bg:#0b1020;--card:#121a30;--text:#e9e2d0;--muted:#b3ad9d;--line:rgba(217,179,106,.28);--accent:#d9b36a;--accent-ink:#0b1020;
  --user:#efe4c8;--user-text:#33210f;--resp:#0e1528;color-scheme:dark}
html[data-tab="venheilheim"] .user{font-size:17px;line-height:1.5}
html[data-tab="venheilheim"] .bar h1,html[data-tab="venheilheim"] h2{letter-spacing:.08em;text-transform:uppercase}
html[data-tab="venheilheim"] .resp{color:#d6d0c0}
/* FocusBank: the app site's vault green (navy and lime in dark mode) */
html[data-tab="focusbank"]{--display:"Bricolage Grotesque","Avenir Next",system-ui,sans-serif;--body:"Figtree",system-ui,sans-serif;
  --mono:"JetBrains Mono",ui-monospace,monospace;--radius:14px;
  --bg:#f3f6ef;--card:#fff;--text:#152012;--muted:#56624f;--line:#d6dfcc;--accent:#3f6418;--accent-ink:#fff;--user:#e9efe2;--resp:#f8faf5}
/* Lecture notes: the course site's warm paper and orange */
html[data-tab="lecture"]{--display:Fraunces,Georgia,serif;--body:Inter,system-ui,sans-serif;--mono:"JetBrains Mono",ui-monospace,monospace;
  --bg:#faf7f2;--card:#fff;--text:#1c1917;--muted:#57534e;--line:#e7e0d6;--accent:#c2410c;--accent-ink:#fff;--user:#fdf1e3;--resp:#fcfaf6}
/* xG Companion: the course's pitch green and condensed match-programme headings */
html[data-tab="xg"]{--display:"Barlow Condensed","Arial Narrow",system-ui,sans-serif;--body:"Atkinson Hyperlegible",system-ui,sans-serif;
  --mono:"JetBrains Mono",ui-monospace,monospace;
  --bg:#f2f5f1;--card:#fff;--text:#15241c;--muted:#55675d;--line:#d2dbd5;--accent:#1b6a44;--accent-ink:#fff;--user:#dcebe2;--resp:#f7faf8}
html[data-tab="xg"] h2,html[data-tab="xg"] .bar h1{text-transform:uppercase;letter-spacing:.02em}
@media (prefers-color-scheme:dark){
  html[data-tab="xg"]{--bg:#0f1613;--card:#16201b;--text:#e7efe9;--muted:#9db1a6;--line:#2b3b33;--accent:#4fc28b;--accent-ink:#0f1613;
    --user:#183528;--resp:#121b17;color-scheme:dark}
  html[data-tab="focusbank"]{--bg:#0b1426;--card:#12203a;--text:#e7eef8;--muted:#9fb0c8;--line:#22355a;--accent:#b9f27c;--accent-ink:#10200a;
    --user:#182a4a;--resp:#0f1b31;color-scheme:dark}
  html[data-tab="lecture"]{--bg:#12100e;--card:#1c1916;--text:#f5f0e8;--muted:#b8afa4;--line:#2f2a25;--accent:#fb923c;--accent-ink:#12100e;
    --user:#3a2414;--resp:#171411;color-scheme:dark}
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.55 var(--body)}
.bar{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 16px;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.bar h1{font:700 17px var(--display);margin:0 12px 0 0}
button,input{font:500 14px var(--sans);color:var(--text);background:var(--card);border:1px solid var(--line);border-radius:6px;padding:5px 10px}
button{cursor:pointer}button[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);font-weight:600}
button[data-show]{font-family:var(--display)}
input{flex:1;min-width:140px}
main{max-width:900px;margin:0 auto;padding:16px}
h2{font:700 22px var(--display);margin:8px 0 16px}.count,.len{color:var(--muted);font:400 13px var(--sans);text-transform:none;letter-spacing:0}
.part{font:700 16px var(--display);margin:24px 0 10px;padding-bottom:4px;border-bottom:2px solid var(--accent);color:var(--accent)}
.turn{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);margin:0 0 12px;overflow:hidden}
.turn header{padding:8px 14px 0;background:var(--user)}.num{color:var(--accent);font:700 13px var(--display);text-decoration:none;letter-spacing:.04em}
html[data-tab="venheilheim"] .num{color:#8c1f16}
.user{padding:6px 14px 12px;white-space:pre-wrap;overflow-wrap:anywhere;background:var(--user);color:var(--user-text)}
details{border-top:1px solid var(--line)}
summary{cursor:pointer;padding:8px 14px;font:600 14px var(--display);user-select:none}
summary:hover{color:var(--accent)}
.pv{display:block;font:400 13px var(--body);color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
details[open] .pv{display:none}
.resp{padding:10px 14px 14px;white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.5 var(--mono);background:var(--resp);max-height:80vh;overflow:auto}
.prep{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:-6px 0 18px}
.prep span{font:600 12px var(--sans);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.prep a{font:600 14px var(--display);color:var(--accent-ink);background:var(--accent);border-radius:999px;padding:6px 14px;text-decoration:none}
.prep a:hover{filter:brightness(1.1)}
.none{color:var(--muted)}
.transcript,.turn{scroll-margin-top:110px}
.hidden{display:none}
"""

SCRIPT = """
const secs=[...document.querySelectorAll('.transcript')],tabs=[...document.querySelectorAll('[data-show]')];
function show(id){secs.forEach(s=>s.classList.toggle('hidden',s.id!==id));tabs.forEach(t=>t.setAttribute('aria-pressed',t.dataset.show===id));document.documentElement.dataset.tab=id;}
tabs.forEach(t=>t.onclick=()=>{show(t.dataset.show);history.replaceState(null,'','#'+t.dataset.show)});
const h=location.hash.slice(1),el=h&&document.getElementById(h);
if(el){show(el.closest('.transcript').id);if(el.classList.contains('turn'))el.scrollIntoView();}else show(secs[0].id);
const cur=()=>secs.find(s=>!s.classList.contains('hidden'));
document.getElementById('open').onclick=()=>cur().querySelectorAll('.turn:not(.hidden) details').forEach(d=>d.open=true);
document.getElementById('close').onclick=()=>cur().querySelectorAll('details').forEach(d=>d.open=false);
let tm;document.getElementById('q').oninput=e=>{clearTimeout(tm);tm=setTimeout(()=>{const q=e.target.value.toLowerCase();
cur().querySelectorAll('.turn').forEach(t=>t.classList.toggle('hidden',q&&!t.textContent.toLowerCase().includes(q)));},200)};
"""


def page(title, tabs, base):
    """base is the path from this page back to the site root ('' or '../')."""
    tabs = [(tid, t, body.replace('href="PREP/', f'href="{base}prep/')) for tid, t, body in tabs]
    fonts = f"{base}fonts/"
    buttons = "".join(f'<button data-show="{tid}" aria-pressed="false">{t}</button>' for tid, t, _ in tabs) if len(tabs) > 1 else ""
    return (f'<!doctype html>\n<html lang="en" data-tab="{tabs[0][0]}"><head><meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>{title}</title>{FONTS}<style>{STYLE.replace("FONTS/", fonts)}</style></head><body>\n'
            f'<div class="bar"><h1>{title}</h1>{buttons}\n'
            f'<input id="q" type="search" placeholder="Filter turns…">\n'
            f'<button id="open">Expand all</button><button id="close">Collapse all</button></div>\n'
            f'<main>{"".join(body for _, _, body in tabs)}</main><script>{SCRIPT}</script></body></html>')


built = [(tid, title, out, render_tab(tid, title, parts)) for tid, title, out, parts in TABS]
with open(f"{root}/index.html", "w", encoding="utf-8") as f:
    f.write(page("AIDS Transcripts", [(tid, t, body) for tid, t, _, body in built], ""))
for tid, t, out, body in built:
    with open(f"{root}/transcripts/{out}", "w", encoding="utf-8") as f:
        f.write(page(f"{t} Transcript", [(tid, t, body)], "../"))
