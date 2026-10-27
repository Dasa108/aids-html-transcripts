# AIDS HTML transcripts

Claude Code and Codex conversation transcripts as one clickable page with three tabs
(Venheilheim, FocusBank, Lecture notes). Each turn shows the prompt, with the response
in a collapsed block below it.

Live: https://dasa108.github.io/aids-html-transcripts/

Each tab also has its own standalone page in `transcripts/` (`transcripts.html`,
`transcript_focusbank.html`, `transcript_lecture.html`).

## Adding or updating a transcript

1. Put the `.md` file in `transcripts/`. The raw `.md` files stay local and are not
   committed (see `.gitignore`); only the built HTML is published.
2. Add it to `TABS` in `build.py`, either as a new tab or as another part of an existing tab.
3. Run `python3 build.py`, then commit and push.

Claude Code `/export` files, `## User` / `## Claude` Markdown and Codex exports all work.
Anything listed in `REDACT` in `build.py` is replaced before publishing.
