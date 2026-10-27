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
     [("transript_lecture.md", None)]),
]

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


def parse(path):
    text = open(path, encoding="utf-8").read()
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
    return (f'<section class="transcript" id="{tid}"><h2>{title} <span class="count">{n} turns</span></h2>'
            f'{"".join(items)}</section>')


STYLE = """
:root{--bg:#f6f5f1;--card:#fff;--text:#1d1d1b;--muted:#6b6a65;--line:#e3e1da;--accent:#9a5b13;--user:#fbf6ec;--resp:#fafaf8}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161614;--card:#1f1f1c;--text:#e9e7e1;--muted:#9c9a92;--line:#33322e;--accent:#e0a35a;--user:#2a251d;--resp:#1a1a18}}
:root[data-theme="dark"]{--bg:#161614;--card:#1f1f1c;--text:#e9e7e1;--muted:#9c9a92;--line:#33322e;--accent:#e0a35a;--user:#2a251d;--resp:#1a1a18}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
.bar{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 16px;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.bar h1{font-size:17px;margin:0 12px 0 0}
button,input{font:inherit;color:var(--text);background:var(--card);border:1px solid var(--line);border-radius:6px;padding:5px 10px}
button{cursor:pointer}button[aria-pressed="true"]{border-color:var(--accent);color:var(--accent);font-weight:600}
input{flex:1;min-width:140px}
main{max-width:900px;margin:0 auto;padding:16px}
h2{font-size:20px;margin:8px 0 16px}.count,.len{color:var(--muted);font-weight:400;font-size:13px}
.part{font-size:15px;margin:24px 0 10px;padding-bottom:4px;border-bottom:2px solid var(--accent);color:var(--accent)}
.turn{background:var(--card);border:1px solid var(--line);border-radius:10px;margin:0 0 12px;overflow:hidden}
.turn header{padding:8px 14px 0}.num{color:var(--accent);font-weight:700;text-decoration:none;font-size:13px;letter-spacing:.03em}
.user{padding:6px 14px 12px;white-space:pre-wrap;overflow-wrap:anywhere;background:var(--user)}
details{border-top:1px solid var(--line)}
summary{cursor:pointer;padding:8px 14px;font-weight:600;font-size:14px;user-select:none}
summary:hover{color:var(--accent)}
.pv{display:block;font-weight:400;color:var(--muted);font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
details[open] .pv{display:none}
.resp{padding:10px 14px 14px;white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.5 ui-monospace,"SFMono-Regular",Menlo,Consolas,monospace;background:var(--resp);max-height:80vh;overflow:auto}
.hidden{display:none}
"""

SCRIPT = """
const secs=[...document.querySelectorAll('.transcript')],tabs=[...document.querySelectorAll('[data-show]')];
function show(id){secs.forEach(s=>s.classList.toggle('hidden',s.id!==id));tabs.forEach(t=>t.setAttribute('aria-pressed',t.dataset.show===id));}
tabs.forEach(t=>t.onclick=()=>{show(t.dataset.show);history.replaceState(null,'','#'+t.dataset.show)});
const h=location.hash.slice(1),el=h&&document.getElementById(h);
if(el){show(el.closest('.transcript').id);if(el.classList.contains('turn'))el.scrollIntoView();}else show(secs[0].id);
const cur=()=>secs.find(s=>!s.classList.contains('hidden'));
document.getElementById('open').onclick=()=>cur().querySelectorAll('.turn:not(.hidden) details').forEach(d=>d.open=true);
document.getElementById('close').onclick=()=>cur().querySelectorAll('details').forEach(d=>d.open=false);
let tm;document.getElementById('q').oninput=e=>{clearTimeout(tm);tm=setTimeout(()=>{const q=e.target.value.toLowerCase();
cur().querySelectorAll('.turn').forEach(t=>t.classList.toggle('hidden',q&&!t.textContent.toLowerCase().includes(q)));},200)};
"""


def page(title, tabs):
    buttons = "".join(f'<button data-show="{tid}" aria-pressed="false">{t}</button>' for tid, t, _ in tabs) if len(tabs) > 1 else ""
    return (f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>{title}</title><style>{STYLE}</style></head><body>\n'
            f'<div class="bar"><h1>{title}</h1>{buttons}\n'
            f'<input id="q" type="search" placeholder="Filter turns…">\n'
            f'<button id="open">Expand all</button><button id="close">Collapse all</button></div>\n'
            f'<main>{"".join(body for _, _, body in tabs)}</main><script>{SCRIPT}</script></body></html>')


built = [(tid, title, out, render_tab(tid, title, parts)) for tid, title, out, parts in TABS]
with open(f"{root}/index.html", "w", encoding="utf-8") as f:
    f.write(page("AIDS Transcripts", [(tid, t, body) for tid, t, _, body in built]))
for tid, t, out, body in built:
    with open(f"{root}/transcripts/{out}", "w", encoding="utf-8") as f:
        f.write(page(f"{t} Transcript", [(tid, t, body)]))
