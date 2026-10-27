# AIDS HTML transcripts

Claude Code conversation transcripts as one clickable page: each turn shows the
prompt, with the response in a collapsed block below it.

## Adding a transcript

1. Put the file in `transcripts/` with the next number, e.g. `transcripts/transcript3.md`.
2. Run `python3 build.py` to regenerate `index.html`.
3. Commit and push. GitHub Pages republishes in a minute or two.

Both `/export` terminal dumps and `## User` / `## Claude` Markdown files work.
