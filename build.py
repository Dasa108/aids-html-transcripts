"""Build index.html from every transcripts/*.md file.

Usage: python3 build.py
Each .md becomes one tab, ordered by the number in its name (transcript1, transcript2, ...).
Two formats are understood: '## User' / '## Claude' sections, and Claude Code
terminal exports ('❯' prompts).
"""
import glob, html, os, re

root = os.path.dirname(os.path.abspath(__file__))


def parse_md(path):
    """transcript1.md: '## User' / '## Claude' sections."""
    turns, cur, role, buf = [], None, None, []

    def flush():
        nonlocal buf
        text = "\n".join(buf).strip()
        buf = []
        if not text:
            return
        if role == "User":
            turns.append([text, []])
        elif turns:
            turns[-1][1].append(text)
        else:
            turns.append(["(conversation start)", [text]])

    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line in ("## User", "## Claude"):
            flush()
            role = line[3:]
        else:
            buf.append(line)
    flush()
    return [(u, "\n\n".join(r)) for u, r in turns]


def dedent(line):
    line = line.rstrip()
    return line[2:] if line.startswith("  ") else line


def parse_export(path):
    """transcript2.md: terminal /export, '❯' user prompts, everything else response."""
    lines = open(path, encoding="utf-8").read().split("\n")
    turns, i = [], 0
    # skip the Claude Code banner, then keep any response that comes before the first prompt
    while i < len(lines) and not lines[i].startswith(("❯ ", "● ")):
        i += 1
    pre = []
    while i < len(lines) and not lines[i].startswith("❯ "):
        pre.append(dedent(lines[i]) if lines[i].startswith("  ") else lines[i].rstrip())
        i += 1
    if "\n".join(pre).strip():
        turns.append(("(continued from an earlier conversation — no prompt in this export)",
                      re.sub(r"\n{3,}", "\n\n", "\n".join(pre)).strip()))
    while i < len(lines):
        user = [lines[i][2:].rstrip()]
        i += 1
        while i < len(lines) and lines[i].startswith("  ") and lines[i].strip():
            user.append(dedent(lines[i]))
            i += 1
        resp = []
        while i < len(lines) and not lines[i].startswith("❯ "):
            resp.append(dedent(lines[i]) if lines[i].startswith("  ") else lines[i].rstrip())
            i += 1
        turns.append(("\n".join(user).strip(), re.sub(r"\n{3,}", "\n\n", "\n".join(resp)).strip()))
    return turns


def natural(path):
    m = re.search(r"(\d+)", os.path.basename(path))
    return (int(m.group(1)) if m else 0, path)


sources = []
for n, path in enumerate(sorted(glob.glob(f"{root}/transcripts/*.md"), key=natural), 1):
    text = open(path, encoding="utf-8").read()
    turns = parse_md(path) if re.search(r"^## (User|Claude)$", text, re.M) else parse_export(path)
    sources.append((f"t{n}", f"Transcript {n}", turns))

out = []
for sid, title, turns in sources:
    items = []
    for n, (u, r) in enumerate(turns, 1):
        items.append(
            f'<article class="turn" id="{sid}-{n}"><header><a class="num" href="#{sid}-{n}">Turn {n}</a></header>'
            f'<div class="user">{html.escape(u)}</div>'
            f'<details><summary>Response <span class="len">{len(r.split()):,} words</span></summary>'
            f'<div class="resp">{html.escape(r) or "<em>(no text response)</em>"}</div></details></article>'
        )
    out.append(f'<section class="transcript" id="{sid}" data-title="{title}"><h2>{title} '
               f'<span class="count">{len(turns)} turns</span></h2>{"".join(items)}</section>')
    print(title, len(turns), "turns")

page = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Venheilheim Transcripts</title>
<style>
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
.turn{background:var(--card);border:1px solid var(--line);border-radius:10px;margin:0 0 12px;overflow:hidden}
.turn header{padding:8px 14px 0}.num{color:var(--accent);font-weight:700;text-decoration:none;font-size:13px;letter-spacing:.03em}
.user{padding:6px 14px 12px;white-space:pre-wrap;overflow-wrap:anywhere;background:var(--user)}
details{border-top:1px solid var(--line)}
summary{cursor:pointer;padding:8px 14px;font-weight:600;font-size:14px;user-select:none}
summary:hover{color:var(--accent)}
.resp{padding:10px 14px 14px;white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.5 ui-monospace,"SFMono-Regular",Menlo,Consolas,monospace;background:var(--resp);max-height:80vh;overflow:auto}
.hidden{display:none}
</style></head><body>
<div class="bar"><h1>Transcripts</h1>
""" + "".join(f'<button data-show="{sid}" aria-pressed="false">{title}</button>' for sid, title, _ in sources) + """
<input id="q" type="search" placeholder="Filter turns…">
<button id="open">Expand all</button><button id="close">Collapse all</button></div>
<main>""" + "".join(out) + """</main>
<script>
const secs=[...document.querySelectorAll('.transcript')],tabs=[...document.querySelectorAll('[data-show]')];
function show(id){secs.forEach(s=>s.classList.toggle('hidden',s.id!==id));tabs.forEach(t=>t.setAttribute('aria-pressed',t.dataset.show===id));}
tabs.forEach(t=>t.onclick=()=>{show(t.dataset.show);history.replaceState(null,'','#'+t.dataset.show)});
const h=location.hash.slice(1);if(h){const el=document.getElementById(h);if(el){show(el.closest('.transcript').id);if(el.classList.contains('turn'))el.scrollIntoView();}}else show('t1');
const cur=()=>secs.find(s=>!s.classList.contains('hidden'));
document.getElementById('open').onclick=()=>cur().querySelectorAll('.turn:not(.hidden) details').forEach(d=>d.open=true);
document.getElementById('close').onclick=()=>cur().querySelectorAll('details').forEach(d=>d.open=false);
let tm;document.getElementById('q').oninput=e=>{clearTimeout(tm);tm=setTimeout(()=>{const q=e.target.value.toLowerCase();
document.querySelectorAll('.turn').forEach(t=>t.classList.toggle('hidden',q&&!t.textContent.toLowerCase().includes(q)));},200)};
</script></body></html>"""
open(f"{root}/index.html", "w", encoding="utf-8").write(page)
